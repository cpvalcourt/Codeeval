"""Stathletes Big Data Cup loader — real tracking data adapter (Phase 1).

Turns BDC 2026 CSVs into the canonical schema so the rest of the engine
(features, models, EPV, attribution, export) works unchanged. See
docs/REAL_DATA_GUIDE.md for the measured conventions this encodes.

Conventions handled here, all verified against the 2025-26 season files:

- Coordinates are already canonical (x -100..100, y -42.5..42.5, center
  origin), so no CoordinateNormalizer is needed; the Z column is dropped.
- ``Image Id`` is a string ``"<game>_065468"``; the trailing digits are a
  broadcast-time counter at 30 fps that keeps running through stoppages,
  so absent ids are whistles, not corruption.
- ``Player Id`` is a per-detection track id (~1000 distinct per period)
  and must NOT be used as identity; ``Player Jersey Number`` (~36
  distinct) is the real one, and the literal jersey ``"Go"`` marks a
  goalie.
- Events carry jersey numbers in ``Player_Id`` (joining to the tracking
  jersey), team *names* needing a Home_Team/Away_Team lookup, and a
  1-second clock that cannot pin a frame without using the event's own
  coordinates to disambiguate.
- ``camera_orientations.csv`` names the team whose goalie defends +x in
  period 1; teams alternate ends each period.

The loader returns one (tracking, events) pair per contiguous run of
play, so no possession — and no velocity — ever spans a stoppage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..domain import EventType, Position, Team
from .normalize import DirectionNormalizer
from .schema import validate_events, validate_tracking

# --- source column names -------------------------------------------------

TRACK_FRAME = "Image Id"
TRACK_PERIOD = "Period"
TRACK_CLOCK = "Game Clock"
TRACK_KIND = "Player or Puck"
TRACK_TEAM = "Team"
TRACK_JERSEY = "Player Jersey Number"
TRACK_X = "Rink Location X (Feet)"
TRACK_Y = "Rink Location Y (Feet)"

EVENT_PERIOD = "Period"
EVENT_CLOCK = "Clock"
EVENT_TEAM = "Team"
EVENT_HOME = "Home_Team"
EVENT_AWAY = "Away_Team"
EVENT_PLAYER = "Player_Id"
EVENT_NAME = "Event"
EVENT_X = "X_Coordinate"
EVENT_Y = "Y_Coordinate"

ORIENT_GAME = "Game"
ORIENT_FLAG = "GoalieTeamOnRightSideOfRink1stPeriod"

# --- source vocabulary ---------------------------------------------------

#: Jersey value that marks a goaltender instead of a number.
GOALIE_JERSEY = "Go"
PUCK_KIND = "Puck"
PUCK_ID = "puck"

#: BDC event -> canonical event. Unlisted events are intentionally ignored.
EVENT_MAP: dict[str, EventType] = {
    "Shot": EventType.SHOT,
    "Goal": EventType.GOAL,
    "Play": EventType.PASS,
    "Incomplete Play": EventType.TURNOVER,
    "Takeaway": EventType.TURNOVER,
}

#: A takeaway is credited to the team that *won* the puck, so it is a
#: turnover by the other team.
TEAM_FLIPPED_EVENTS = {"Takeaway"}

FRAME_RATE = 30.0
#: Frame-id space reserved per period so periods can never collide,
#: whether the source counter restarts each period or runs continuously.
PERIOD_STRIDE = 10_000_000
#: Half-length of the crease fallback used when a goalie is untracked.
GOALIE_FALLBACK_X = 87.0


class BigDataCupError(ValueError):
    """Raised when source files cannot be mapped to the canonical schema."""


# --- small pure helpers --------------------------------------------------


def parse_frame_id(values: pd.Series, period: int) -> pd.Series:
    """``"<game>_065468"`` -> ``period * PERIOD_STRIDE + 65468``."""
    digits = values.astype(str).str.extract(r"(\d+)\s*$")[0]
    parsed = pd.to_numeric(digits, errors="coerce")
    if parsed.isna().all():
        raise BigDataCupError(f"no numeric frame index found in {TRACK_FRAME!r}")
    return (parsed + period * PERIOD_STRIDE).astype("Int64")


def build_entity_id(team: str, jersey: str | float | None, kind: str) -> str:
    """Stable identity for one tracked object.

    Track ids churn as the tracker loses and reacquires players, so
    identity is team + jersey, with goalies named by role.
    """
    if kind == PUCK_KIND:
        return PUCK_ID
    side = str(team).strip().lower()
    label = str(jersey).strip()
    if label == GOALIE_JERSEY:
        return f"{side}_goalie"
    return f"{side}_{label}"


def clock_to_seconds(values: pd.Series) -> pd.Series:
    """``"19:57"`` -> 1197.0 seconds remaining."""
    parts = values.astype(str).str.extract(r"(\d+):(\d+)")
    return parts[0].astype(float) * 60 + parts[1].astype(float)


def direction_map(
    orientations: pd.DataFrame, game_key: str, team: Team = Team.HOME
) -> dict[int, bool]:
    """``{period: team already attacks +x}`` for the analyzed team.

    ``GoalieTeamOnRightSideOfRink1stPeriod`` names the team whose goalie
    *defends* +x in period 1 — that team therefore attacks -x — and the
    teams swap ends every period.
    """
    rows = orientations[orientations[ORIENT_GAME].astype(str).str.strip() == game_key]
    if rows.empty:
        raise BigDataCupError(f"no camera orientation row for game {game_key!r}")
    goalie_right = str(rows.iloc[0][ORIENT_FLAG]).strip().lower()
    if goalie_right not in {Team.HOME.value, Team.AWAY.value}:
        raise BigDataCupError(f"unexpected orientation value {goalie_right!r}")
    # The named team defends +x in P1, so the *other* team attacks +x.
    attacks_right_p1 = goalie_right != team.value
    return {period: attacks_right_p1 == (period % 2 == 1) for period in (1, 2, 3, 4)}


def split_segments(frames: np.ndarray, max_gap: int = 2) -> list[tuple[int, int]]:
    """Contiguous ``(first, last)`` frame runs, split at stoppage gaps."""
    ordered = np.unique(np.asarray(frames))
    if len(ordered) == 0:
        return []
    breaks = np.flatnonzero(np.diff(ordered) > max_gap)
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [len(ordered) - 1]))
    return [(int(ordered[s]), int(ordered[e])) for s, e in zip(starts, ends)]


# --- loader --------------------------------------------------------------


@dataclass
class BigDataCupLoader:
    """Reads BDC game files into canonical, validated segments."""

    frame_rate: float = FRAME_RATE
    #: Segments shorter than this are dropped (default 2 seconds).
    min_segment_frames: int = 60
    #: Entities tracked for less of a segment than this are dropped.
    min_entity_coverage: float = 0.7
    #: Rows further outside the rink than this are tracking glitches.
    rink_tolerance: float = 1.0

    # -- tracking ---------------------------------------------------------

    def load_tracking_period(self, path: Path | str, period: int) -> pd.DataFrame:
        """One period CSV -> canonical rows (still in source direction)."""
        raw = pd.read_csv(path, low_memory=False)
        missing = {TRACK_FRAME, TRACK_KIND, TRACK_X, TRACK_Y} - set(raw.columns)
        if missing:
            raise BigDataCupError(f"{path}: missing columns {sorted(missing)}")

        df = pd.DataFrame(
            {
                "frame_id": parse_frame_id(raw[TRACK_FRAME], period),
                "period": period,
                "clock": clock_to_seconds(raw[TRACK_CLOCK]),
                "kind": raw[TRACK_KIND].astype(str).str.strip(),
                "team_raw": raw[TRACK_TEAM],
                "jersey": raw[TRACK_JERSEY],
                "x": pd.to_numeric(raw[TRACK_X], errors="coerce"),
                "y": pd.to_numeric(raw[TRACK_Y], errors="coerce"),
            }
        )

        is_puck = df["kind"] == PUCK_KIND
        # Unidentified detections cannot be given a stable identity.
        df = df[is_puck | df["jersey"].notna()]
        df = df.dropna(subset=["frame_id", "x", "y"])
        df = self._drop_off_rink(df)

        df["entity_id"] = [
            build_entity_id(t, j, k)
            for t, j, k in zip(df["team_raw"], df["jersey"], df["kind"])
        ]
        df["team"] = np.where(
            df["kind"] == PUCK_KIND, "none", df["team_raw"].astype(str).str.lower()
        )
        df["position"] = np.where(
            df["kind"] == PUCK_KIND,
            Position.PUCK.value,
            np.where(
                df["jersey"].astype(str).str.strip() == GOALIE_JERSEY,
                Position.GOALIE.value,
                Position.SKATER.value,
            ),
        )
        df = df.drop_duplicates(["frame_id", "entity_id"], keep="first")
        return df.drop(columns=["kind", "team_raw", "jersey"])

    def _drop_off_rink(self, df: pd.DataFrame) -> pd.DataFrame:
        tol = self.rink_tolerance
        keep = df["x"].between(-100 - tol, 100 + tol) & df["y"].between(
            -42.5 - tol, 42.5 + tol
        )
        return df[keep]

    # -- events -----------------------------------------------------------

    def load_events(
        self, path: Path | str, tracking: pd.DataFrame, game_id: str
    ) -> pd.DataFrame:
        """Events CSV -> canonical events with frames resolved.

        ``tracking`` must be the *source-direction* tracking (before any
        direction flip), because alignment matches the event's recorded
        coordinates against the puck's position.
        """
        raw = pd.read_csv(path, low_memory=False)
        puck = tracking[tracking["position"] == Position.PUCK.value]
        lookup = {
            period: group for period, group in puck.groupby("period")
        }

        records: list[dict] = []
        for row in raw.itertuples(index=False):
            name = str(getattr(row, EVENT_NAME.replace(" ", "_"), "")).strip()
            canonical = EVENT_MAP.get(name)
            if canonical is None:
                continue
            period = int(getattr(row, EVENT_PERIOD))
            candidates = lookup.get(period)
            if candidates is None or candidates.empty:
                continue
            frame_id = self._align_event(
                candidates,
                clock_to_seconds(pd.Series([getattr(row, EVENT_CLOCK)])).iloc[0],
                float(getattr(row, EVENT_X)),
                float(getattr(row, EVENT_Y)),
            )
            if frame_id is None:
                continue

            side = (
                Team.HOME
                if str(getattr(row, EVENT_TEAM)).strip()
                == str(getattr(row, EVENT_HOME)).strip()
                else Team.AWAY
            )
            if name in TEAM_FLIPPED_EVENTS:
                side = side.opponent
            records.append(
                {
                    "game_id": game_id,
                    "frame_id": int(frame_id),
                    "event_type": canonical.value,
                    "team": side.value,
                    "player_id": build_entity_id(
                        side.value, getattr(row, EVENT_PLAYER), "Player"
                    ),
                    "_source": name,
                }
            )

        events = pd.DataFrame.from_records(records)
        return self._pair_goals_with_shots(events)

    def _align_event(
        self,
        puck_frames: pd.DataFrame,
        clock_seconds: float,
        event_x: float,
        event_y: float,
    ) -> int | None:
        """Frame whose puck sits nearest the event, within its clock second.

        The clock has 1-second resolution (~30 candidate frames), so the
        event's own coordinates break the tie.
        """
        if not np.isfinite(clock_seconds):
            return None
        for tolerance in (0.0, 1.0, 2.0):
            window = puck_frames[
                (puck_frames["clock"] - clock_seconds).abs() <= tolerance
            ]
            if not window.empty:
                dist = np.hypot(window["x"] - event_x, window["y"] - event_y)
                return int(window.iloc[int(np.argmin(dist.to_numpy()))]["frame_id"])
        return None

    @staticmethod
    def _pair_goals_with_shots(events: pd.DataFrame) -> pd.DataFrame:
        """Ensure every goal has a shot to attach to.

        The xG labeler learns from shot frames and marks a shot as scoring
        when a goal follows it. Feeds differ on whether a goal is also
        logged as a shot, so add the shot only when one is not already
        present nearby.
        """
        if events.empty:
            return events.drop(columns=["_source"], errors="ignore")
        goals = events[events["event_type"] == EventType.GOAL.value]
        shots = events[events["event_type"] == EventType.SHOT.value]
        additions = []
        for goal in goals.itertuples(index=False):
            near = shots[
                (shots["team"] == goal.team)
                & (shots["frame_id"] - goal.frame_id).abs().le(45)
            ]
            if near.empty:
                additions.append(
                    {
                        "game_id": goal.game_id,
                        "frame_id": goal.frame_id,
                        "event_type": EventType.SHOT.value,
                        "team": goal.team,
                        "player_id": goal.player_id,
                    }
                )
        out = events.drop(columns=["_source"], errors="ignore")
        if additions:
            out = pd.concat([out, pd.DataFrame(additions)], ignore_index=True)
        return out.sort_values("frame_id", ignore_index=True)

    # -- roster completion -------------------------------------------------

    def complete_roster(self, segment: pd.DataFrame) -> pd.DataFrame:
        """Give every retained entity a row in every frame of the segment.

        The exporter requires it, and interpolating inside one contiguous
        play run is safe. Sparsely tracked entities are dropped, except
        goalies, which are kept (the xG model conditions on them) and
        filled — falling back to the crease if untracked entirely.
        """
        frames = np.sort(segment["frame_id"].unique())
        n_frames = len(frames)
        filled: list[pd.DataFrame] = []

        for entity_id, rows in segment.groupby("entity_id", sort=False):
            position = rows["position"].iloc[0]
            coverage = len(rows) / n_frames
            is_goalie = position == Position.GOALIE.value
            if coverage < self.min_entity_coverage and not is_goalie:
                continue
            block = (
                rows.drop_duplicates("frame_id")
                .set_index("frame_id")
                .reindex(frames)
            )
            block["x"] = block["x"].interpolate(limit_direction="both")
            block["y"] = block["y"].interpolate(limit_direction="both")
            block["entity_id"] = entity_id
            block["position"] = position
            block["team"] = rows["team"].iloc[0]
            block["period"] = rows["period"].iloc[0]
            filled.append(block.reset_index(names="frame_id"))

        out = pd.concat(filled, ignore_index=True) if filled else segment.iloc[0:0]
        return self._ensure_goalies(out, frames)

    def _ensure_goalies(self, segment: pd.DataFrame, frames: np.ndarray) -> pd.DataFrame:
        """Synthesize crease-position goalies that were never tracked.

        Direction is already normalized here: the analyzed team attacks
        +x, so it defends -x and its opponent's goalie sits at +x.
        """
        present = set(segment["entity_id"])
        additions = []
        for team, sign in ((Team.HOME, -1.0), (Team.AWAY, 1.0)):
            entity_id = f"{team.value}_goalie"
            if entity_id in present or segment.empty:
                continue
            additions.append(
                pd.DataFrame(
                    {
                        "frame_id": frames,
                        "period": segment["period"].iloc[0],
                        "entity_id": entity_id,
                        "team": team.value,
                        "position": Position.GOALIE.value,
                        "x": sign * GOALIE_FALLBACK_X,
                        "y": 0.0,
                    }
                )
            )
        if not additions:
            return segment
        return pd.concat([segment, *additions], ignore_index=True)

    # -- orchestration -----------------------------------------------------

    def load_game(
        self,
        tracking_paths: dict[int, Path | str],
        events_path: Path | str,
        orientations_path: Path | str,
        game_id: str,
        game_key: str | None = None,
        team: Team = Team.HOME,
    ) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
        """One (tracking, events) pair per contiguous run of play.

        ``tracking_paths`` maps period number -> CSV path. ``game_key`` is
        the value in ``camera_orientations.csv``'s Game column (defaults
        to ``game_id``).
        """
        periods = sorted(tracking_paths)
        source = pd.concat(
            [self.load_tracking_period(tracking_paths[p], p) for p in periods],
            ignore_index=True,
        )
        if source.empty:
            raise BigDataCupError(f"{game_id}: no usable tracking rows")

        # Events must be aligned before the direction flip: canonical
        # events carry no coordinates, so the geometry is gone afterwards.
        events = self.load_events(events_path, source, game_id)

        orientations = pd.read_csv(orientations_path)
        flips = direction_map(orientations, game_key or game_id, team)
        tracking = DirectionNormalizer(flips).transform(source)

        tracking = self._drop_frames_without_puck(tracking)

        out: list[tuple[pd.DataFrame, pd.DataFrame]] = []
        for index, (first, last) in enumerate(
            split_segments(tracking["frame_id"].to_numpy())
        ):
            if last - first + 1 < self.min_segment_frames:
                continue
            window = tracking[tracking["frame_id"].between(first, last)]
            segment = self.complete_roster(window)
            if segment.empty:
                continue
            segment_id = f"{game_id}-p{segment['period'].iloc[0]}-s{index:03d}"
            segment = segment.assign(
                game_id=segment_id,
                timestamp=(segment["frame_id"] - first) / self.frame_rate,
            )
            segment_events = events[
                events["frame_id"].between(first, last)
            ].assign(game_id=segment_id)
            try:
                out.append(
                    (validate_tracking(segment), validate_events(segment_events))
                )
            except ValueError:
                # A malformed segment is dropped rather than failing the
                # whole game; the caller sees the count it received.
                continue
        return out

    @staticmethod
    def _drop_frames_without_puck(tracking: pd.DataFrame) -> pd.DataFrame:
        """The possession machine requires a puck wherever skaters exist."""
        puck_frames = set(
            tracking.loc[tracking["position"] == Position.PUCK.value, "frame_id"]
        )
        return tracking[tracking["frame_id"].isin(puck_frames)]


# --- file discovery ------------------------------------------------------

_TRACKING_RE = re.compile(r"(?P<game>.+?)[. ]Tracking_P(?P<period>\d+)\.csv$", re.I)


def discover_games(root: Path | str) -> dict[str, dict]:
    """Group a raw-data directory into per-game file sets.

    Returns ``{game_id: {"tracking": {period: path}, "events": path,
    "game_key": str}}`` for games that have both tracking and events.
    """
    root = Path(root)
    games: dict[str, dict] = {}
    for path in sorted(root.rglob("*.csv")):
        match = _TRACKING_RE.search(path.name)
        if not match:
            continue
        stem = match.group("game")
        game_id = stem.replace(" ", ".").strip(".")
        entry = games.setdefault(
            game_id,
            {"tracking": {}, "events": None, "game_key": stem.replace(".", " ").strip()},
        )
        entry["tracking"][int(match.group("period"))] = path

    for path in sorted(root.rglob("*Events.csv")):
        stem = path.name[: path.name.lower().rindex("events.csv")].strip(". ")
        game_id = stem.replace(" ", ".").strip(".")
        if game_id in games:
            games[game_id]["events"] = path

    return {gid: entry for gid, entry in games.items() if entry["events"]}

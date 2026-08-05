"""Builds Big Data Cup-shaped CSVs for tests.

Mirrors the real 2026 files exactly as measured by
scripts/inspect_raw_data.py: string ``Image Id`` on broadcast time with
stoppage gaps, ``Home``/``Away`` teams, a churning per-detection
``Player Id`` alongside the stable jersey number, the literal ``"Go"``
jersey for goalies, sparse goalie tracking, partial rosters, occasional
null coordinates, a 1-second game clock, and team *names* in the events
file.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HOME_JERSEYS = ["4", "9", "12", "18", "27"]
AWAY_JERSEYS = ["5", "11", "17", "22", "44"]
HOME_NAME = "Team D"
AWAY_NAME = "Team A"


def _clock(seconds: float) -> str:
    seconds = max(seconds, 0.0)
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def build_game(
    directory: Path,
    game_key: str = "2025-10-11 Team A @ Team D",
    n_segments: int = 3,
    segment_frames: int = 400,
    seed: int = 0,
    goalie_coverage: float = 0.35,
    home_attacks_right_p1: bool = True,
) -> dict:
    """Write one game's CSVs; returns the paths and expectations."""
    rng = np.random.default_rng(seed)
    directory.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    events: list[dict] = []
    frame = 65468
    clock = 1200.0
    period = 1
    # In P1 the goalie of the team NOT attacking right defends +x.
    home_sign = 1.0 if home_attacks_right_p1 else -1.0

    for segment in range(n_segments):
        # Puck carrier walks toward the attacking net so EPV has signal.
        carrier_x = -40.0 * home_sign
        carrier = HOME_JERSEYS[segment % len(HOME_JERSEYS)]
        for step in range(segment_frames):
            frame += 1
            clock -= 1 / 30.0
            carrier_x += 0.25 * home_sign
            puck_xy = (carrier_x, float(rng.normal(0, 3)))

            for team, jerseys in ((("Home"), HOME_JERSEYS), (("Away"), AWAY_JERSEYS)):
                sign = home_sign if team == "Home" else -home_sign
                for jersey in jerseys:
                    if rng.random() < 0.12:  # off camera
                        continue
                    if team == "Home" and jersey == carrier:
                        # The carrier stays on the puck, as in real play, so
                        # the possession state machine can detect control.
                        x = puck_xy[0] + rng.normal(0, 0.8)
                        y = puck_xy[1] + rng.normal(0, 0.8)
                    else:
                        x = puck_xy[0] + rng.normal(0, 12) * (1 if team == "Home" else 1.4)
                        y = float(rng.normal(0, 15))
                    if rng.random() < 0.005:
                        x = y = np.nan
                    rows.append(
                        _row(game_key, frame, period, clock, "Player", team, jersey,
                             rng.integers(1, 15000), x, y)
                    )
                # Goalie: tracked only part of the time, sits in its crease.
                if rng.random() < goalie_coverage:
                    rows.append(
                        _row(game_key, frame, period, clock, "Player", team, "Go",
                             rng.integers(1, 15000),
                             -sign * 87.0 + rng.normal(0, 1.0), float(rng.normal(0, 2))),
                    )

            rows.append(
                _row(game_key, frame, period, clock, "Puck", np.nan, np.nan, np.nan,
                     puck_xy[0], puck_xy[1])
            )

            # One pass early, a shot near the end of each segment.
            if step == segment_frames // 4:
                events.append(_event(period, clock, HOME_NAME, "9", "Play", puck_xy))
            if step == segment_frames - 30:
                events.append(_event(period, clock, HOME_NAME, "12", "Shot", puck_xy))
                if segment == 0:
                    events.append(
                        _event(period, clock, HOME_NAME, "12", "Goal", puck_xy)
                    )
            if step == segment_frames // 2:
                # A takeaway BY the away team = a turnover by home.
                events.append(_event(period, clock, AWAY_NAME, "17", "Takeaway", puck_xy))
                # An event we intentionally ignore.
                events.append(_event(period, clock, HOME_NAME, "4", "Zone Entry", puck_xy))

        frame += 900  # stoppage: the id counter keeps running

    tracking_path = directory / f"{game_key.replace(' ', '.')}.Tracking_P1.csv"
    pd.DataFrame(rows).to_csv(tracking_path, index=False)

    events_path = directory / f"{game_key.replace(' ', '.')}.Events.csv"
    pd.DataFrame(events).to_csv(events_path, index=False)

    orientations_path = directory / "camera_orientations.csv"
    # Flag names the team whose goalie defends +x in P1 — the team that
    # does NOT attack right. The real file holds one row per game, so
    # accumulate rather than overwrite when several games share a folder.
    row = pd.DataFrame(
        [{
            "Game": game_key,
            "GoalieTeamOnRightSideOfRink1stPeriod": "Away" if home_attacks_right_p1 else "Home",
        }]
    )
    if orientations_path.exists():
        existing = pd.read_csv(orientations_path)
        row = pd.concat([existing[existing["Game"] != game_key], row], ignore_index=True)
    row.to_csv(orientations_path, index=False)

    return {
        "tracking": {1: tracking_path},
        "events": events_path,
        "orientations": orientations_path,
        "game_key": game_key,
        "n_segments": n_segments,
        "segment_frames": segment_frames,
    }


def _row(game_key, frame, period, clock, kind, team, jersey, track_id, x, y) -> dict:
    return {
        "Image Id": f"{game_key}_{frame:06d}",
        "Period": period,
        "Game Clock": _clock(clock),
        "Player or Puck": kind,
        "Team": team,
        "Player Id": float(track_id) if track_id == track_id else np.nan,
        "Player Jersey Number": jersey,
        "Rink Location X (Feet)": x,
        "Rink Location Y (Feet)": y,
        "Rink Location Z (Feet)": 0.2,
        "Goal Score": np.nan,
    }


def _event(period, clock, team_name, jersey, name, puck_xy) -> dict:
    return {
        "Date": "10/11/25",
        "Home_Team": HOME_NAME,
        "Away_Team": AWAY_NAME,
        "Period": period,
        "Clock": _clock(clock),
        "Team": team_name,
        "Player_Id": jersey,
        "Event": name,
        "X_Coordinate": round(puck_xy[0], 1),
        "Y_Coordinate": round(puck_xy[1], 1),
        "Detail_1": np.nan,
        "Detail_2": "On Net" if name in ("Shot", "Goal") else np.nan,
    }

"""Rule-based possession state machine (Phase 1).

Determines, for every frame, whether the puck is controlled by the home
team, the away team, or loose. Control requires a skater to stay within
``control_radius`` of the puck for ``min_control_frames`` consecutive
frames (hysteresis, so a puck merely passing near an opponent does not
flip possession), and possession decays to LOOSE after ``loose_frames``
frames with no control candidate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import PossessionConfig
from ..domain import Position, Possession, PuckState, Team


class PossessionStateMachine:
    """Annotates tracking frames with puck state and controlling player."""

    def __init__(self, config: PossessionConfig | None = None):
        self._config = config or PossessionConfig()

    def annotate(self, tracking: pd.DataFrame) -> pd.DataFrame:
        """Return one row per frame: puck_state, controlling player/team.

        ``tracking`` must be canonical long-format data for a single game.
        """
        if tracking["game_id"].nunique() > 1:
            raise ValueError("annotate() expects tracking data for a single game")

        cfg = self._config
        puck = (
            tracking[tracking["position"] == Position.PUCK.value]
            .set_index("frame_id")[["x", "y"]]
            .sort_index()
        )
        skaters = tracking[tracking["position"] == Position.SKATER.value]

        state = PuckState.LOOSE
        controller: str | None = None
        candidate_streaks: dict[str, int] = {}
        no_candidate_streak = 0

        records: list[dict] = []
        for frame_id, frame_skaters in skaters.groupby("frame_id"):
            if frame_id not in puck.index:
                raise ValueError(f"frame {frame_id} has skaters but no puck row")
            px, py = puck.loc[frame_id, "x"], puck.loc[frame_id, "y"]
            dists = np.hypot(frame_skaters["x"] - px, frame_skaters["y"] - py)
            nearest_pos = int(np.argmin(dists.to_numpy()))
            nearest = frame_skaters.iloc[nearest_pos]
            nearest_dist = float(dists.iloc[nearest_pos])

            if nearest_dist <= cfg.control_radius:
                candidate_id = str(nearest["entity_id"])
                candidate_team = Team(nearest["team"])
                streak = candidate_streaks.get(candidate_id, 0) + 1
                candidate_streaks = {candidate_id: streak}
                no_candidate_streak = 0

                established = streak >= cfg.min_control_frames
                # An established touch takes control; the current controller
                # keeps control while still the nearest in-radius skater.
                if established or candidate_id == controller:
                    state = PuckState(candidate_team.value)
                    controller = candidate_id
            else:
                candidate_streaks = {}
                no_candidate_streak += 1
                if no_candidate_streak >= cfg.loose_frames:
                    state = PuckState.LOOSE
                    controller = None

            records.append(
                {
                    "frame_id": int(frame_id),
                    "puck_state": state.value,
                    "controller": controller,
                }
            )

        return pd.DataFrame.from_records(records)

    def extract_possessions(
        self, states: pd.DataFrame, game_id: str
    ) -> list[Possession]:
        """Collapse per-frame states into contiguous team possession spans.

        LOOSE frames terminate the current span; a new span starts at the
        next controlled frame.
        """
        possessions: list[Possession] = []
        current_team: Team | None = None
        start = end = 0
        for row in states.itertuples(index=False):
            frame_state = PuckState(row.puck_state)
            team = None if frame_state is PuckState.LOOSE else Team(frame_state.value)
            if team == current_team and team is not None:
                end = row.frame_id
                continue
            if current_team is not None:
                possessions.append(Possession(game_id, current_team, start, end))
            current_team = team
            start = end = row.frame_id
        if current_team is not None:
            possessions.append(Possession(game_id, current_team, start, end))
        return possessions

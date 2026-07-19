"""Passing-lane quantification (Phase 2).

A lane from the carrier to a teammate is scored by how far the nearest
intervening defender sits from the pass segment, adjusted for whether
that defender is closing on the lane. The raw geometry maps to an
openness score in [0, 1] through a logistic curve, so downstream models
receive a bounded, smoothly varying feature.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import LaneConfig
from ..domain import Position, Team
from .geometry import point_segment_distance


def lane_openness(
    carrier_xy: np.ndarray,
    target_xy: np.ndarray,
    defender_xy: np.ndarray,
    defender_v: np.ndarray | None = None,
    config: LaneConfig | None = None,
) -> float:
    """Openness in [0, 1] of the pass lane carrier -> target.

    ``defender_xy`` is (n, 2); ``defender_v`` (n, 2) optionally penalizes
    defenders moving toward the lane by projecting one look-ahead second
    of their velocity toward the segment.
    """
    cfg = config or LaneConfig()
    defender_xy = np.atleast_2d(np.asarray(defender_xy, float))
    if defender_xy.shape[0] == 0:
        return 1.0

    dists = point_segment_distance(defender_xy, carrier_xy, target_xy)
    if defender_v is not None:
        # A defender closing on the lane effectively shrinks their distance.
        ahead = defender_xy + np.atleast_2d(np.asarray(defender_v, float)) * 0.5
        dists_ahead = point_segment_distance(ahead, carrier_xy, target_xy)
        dists = np.minimum(dists, 0.5 * (dists + dists_ahead))

    min_dist = float(np.min(dists))
    # Logistic in (min_dist - closed_distance): ~0 when a defender sits in
    # the lane, ->1 as the nearest defender recedes.
    z = (min_dist - cfg.closed_distance) / cfg.distance_scale
    return float(1.0 / (1.0 + np.exp(-z)))


def compute_lane_features(
    tracking: pd.DataFrame,
    attacking_team: Team,
    carrier_by_frame: pd.Series,
    config: LaneConfig | None = None,
) -> pd.DataFrame:
    """Per-frame lane summary features for a single game.

    ``carrier_by_frame`` maps frame_id -> carrier entity_id (NaN/None when
    nobody controls the puck; those frames get neutral features).

    Returns columns: frame_id, best_lane_openness, mean_lane_openness,
    n_open_lanes.
    """
    cfg = config or LaneConfig()
    skaters = tracking[tracking["position"] == Position.SKATER.value]
    has_velocity = {"vx", "vy"}.issubset(tracking.columns)

    records: list[dict] = []
    for frame_id, frame in skaters.groupby("frame_id"):
        carrier_id = carrier_by_frame.get(frame_id)
        neutral = {
            "frame_id": int(frame_id),
            "best_lane_openness": 0.0,
            "mean_lane_openness": 0.0,
            "n_open_lanes": 0,
        }
        if carrier_id is None or (isinstance(carrier_id, float) and np.isnan(carrier_id)):
            records.append(neutral)
            continue
        carrier_rows = frame[frame["entity_id"] == carrier_id]
        if carrier_rows.empty:
            records.append(neutral)
            continue

        carrier_xy = carrier_rows[["x", "y"]].to_numpy()[0]
        teammates = frame[
            (frame["team"] == attacking_team.value) & (frame["entity_id"] != carrier_id)
        ]
        defenders = frame[frame["team"] == attacking_team.opponent.value]
        defender_xy = defenders[["x", "y"]].to_numpy()
        defender_v = defenders[["vx", "vy"]].to_numpy() if has_velocity else None

        scores = [
            lane_openness(carrier_xy, target[["x", "y"]].to_numpy().astype(float), defender_xy, defender_v, cfg)
            for _, target in teammates.iterrows()
        ]
        if not scores:
            records.append(neutral)
            continue
        scores_arr = np.array(scores)
        records.append(
            {
                "frame_id": int(frame_id),
                "best_lane_openness": float(scores_arr.max()),
                "mean_lane_openness": float(scores_arr.mean()),
                "n_open_lanes": int((scores_arr > cfg.open_threshold).sum()),
            }
        )
    return pd.DataFrame.from_records(records).sort_values("frame_id", ignore_index=True)

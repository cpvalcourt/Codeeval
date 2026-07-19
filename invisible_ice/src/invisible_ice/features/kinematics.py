"""Finite-difference kinematics (Phase 2).

Adds velocity, speed, and acceleration columns to canonical tracking data
using ``numpy.gradient`` over the timestamp axis, computed independently
per entity. Central differences interior, one-sided at the ends — the
standard second-order-accurate scheme for uniformly sampled tracking.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

KINEMATIC_COLUMNS = ["vx", "vy", "speed", "ax", "ay", "accel"]


def add_kinematics(tracking: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``tracking`` with per-entity kinematic columns.

    Entities with a single frame get zero velocity/acceleration (no
    difference can be formed).
    """
    out = tracking.sort_values(["game_id", "entity_id", "frame_id"]).reset_index(
        drop=True
    )
    for col in KINEMATIC_COLUMNS:
        out[col] = 0.0

    for _, idx in out.groupby(["game_id", "entity_id"], sort=False).indices.items():
        if len(idx) < 2:
            continue
        t = out.loc[idx, "timestamp"].to_numpy()
        x = out.loc[idx, "x"].to_numpy()
        y = out.loc[idx, "y"].to_numpy()
        vx = np.gradient(x, t)
        vy = np.gradient(y, t)
        out.loc[idx, "vx"] = vx
        out.loc[idx, "vy"] = vy
        out.loc[idx, "speed"] = np.hypot(vx, vy)
        ax = np.gradient(vx, t)
        ay = np.gradient(vy, t)
        out.loc[idx, "ax"] = ax
        out.loc[idx, "ay"] = ay
        out.loc[idx, "accel"] = np.hypot(ax, ay)

    return out.sort_values(["game_id", "frame_id", "entity_id"], ignore_index=True)

"""Royal Road crossing detection (Phase 2).

The "Royal Road" is the imaginary line bisecting the offensive zone down
the middle (y = 0 beyond the offensive blue line). A puck crossing it
forces the goaltender to move laterally, sharply raising scoring rates,
so we flag both the crossing frame and a trailing "recent crossing"
window for the models.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import RinkConfig
from ..domain import Position


def flag_royal_road(
    tracking: pd.DataFrame,
    rink: RinkConfig | None = None,
    recent_window: int = 30,
) -> pd.DataFrame:
    """Per-frame Royal Road flags for a single game.

    Returns columns: frame_id, royal_road_crossing (bool, crossing occurred
    on this frame), royal_road_recent (bool, a crossing occurred within the
    last ``recent_window`` frames, inclusive of the crossing frame).
    """
    rink = rink or RinkConfig()
    puck = (
        tracking[tracking["position"] == Position.PUCK.value]
        .sort_values("frame_id")[["frame_id", "x", "y"]]
        .reset_index(drop=True)
    )
    x = puck["x"].to_numpy()
    y = puck["y"].to_numpy()

    crossing = np.zeros(len(puck), dtype=bool)
    if len(puck) >= 2:
        sign_change = np.signbit(y[1:]) != np.signbit(y[:-1])
        in_zone = (x[1:] > rink.blue_line_x) & (x[:-1] > rink.blue_line_x)
        crossing[1:] = sign_change & in_zone

    recent = np.zeros(len(puck), dtype=bool)
    last_crossing = -np.inf
    frame_ids = puck["frame_id"].to_numpy()
    for i in range(len(puck)):
        if crossing[i]:
            last_crossing = frame_ids[i]
        recent[i] = (frame_ids[i] - last_crossing) <= recent_window

    return pd.DataFrame(
        {
            "frame_id": frame_ids.astype(int),
            "royal_road_crossing": crossing,
            "royal_road_recent": recent,
        }
    )

"""Pure geometric primitives shared by feature extractors (Phase 2).

Kept free of dataframes so they are trivially unit-testable and reusable.
"""

from __future__ import annotations

import numpy as np


def point_segment_distance(
    points: np.ndarray, a: np.ndarray, b: np.ndarray
) -> np.ndarray:
    """Distance from each row of ``points`` (n, 2) to segment a-b.

    Degenerate segments (a == b) fall back to point distance.
    """
    points = np.atleast_2d(points).astype(float)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ab = b - a
    denom = float(ab @ ab)
    if denom < 1e-12:
        return np.linalg.norm(points - a, axis=1)
    t = np.clip((points - a) @ ab / denom, 0.0, 1.0)
    closest = a + np.outer(t, ab)
    return np.linalg.norm(points - closest, axis=1)


def distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


def angle_to_target(origin: np.ndarray, target: np.ndarray) -> float:
    """Absolute angle (radians) of the target relative to the +x axis."""
    d = np.asarray(target, float) - np.asarray(origin, float)
    return float(np.arctan2(d[1], d[0]))

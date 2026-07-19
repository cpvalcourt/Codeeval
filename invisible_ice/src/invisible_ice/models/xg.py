"""Framewise expected-goals model (Phase 3).

Estimates P(goal | shot released at frame t) — the immediate-reward term
xG(S_t) of the Markov decomposition. Trained only on frames where a shot
actually occurred (goal vs. no goal); applied to every frame to answer
"what if the carrier shot right now?".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from .base import SklearnProbabilityModel


class XGModel(SklearnProbabilityModel):
    """Binary goal-probability model."""

    def __init__(self, feature_names: list[str], estimator=None):
        super().__init__(
            feature_names,
            estimator
            or HistGradientBoostingClassifier(
                max_iter=80, max_depth=3, learning_rate=0.15, random_state=0
            ),
        )

    def predict_xg(self, X: pd.DataFrame) -> np.ndarray:
        """P(goal) per row. Degenerate single-class training collapses
        to that class's probability (0.0 or 1.0)."""
        proba = self.predict_proba(X)
        classes = self.classes_
        if len(classes) == 1:
            return np.full(len(X), float(classes[0]))
        goal_col = classes.index(1)
        return proba[:, goal_col]

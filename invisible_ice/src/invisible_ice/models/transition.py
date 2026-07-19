"""Macro-transition model (Phase 3).

Predicts, from the current frame's spatial features, what the possessing
team does next: shoot, pass, keep carrying, or turn the puck over. This
is the P(Action | S_t) term of the spatial Markov decomposition.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from ..domain import Action
from .base import SklearnProbabilityModel

ACTION_ORDER = [Action.SHOOT, Action.PASS, Action.KEEP, Action.TURNOVER]


class TransitionModel(SklearnProbabilityModel):
    """Multiclass action model over :data:`ACTION_ORDER`."""

    def __init__(self, feature_names: list[str], estimator=None):
        super().__init__(
            feature_names,
            estimator
            or HistGradientBoostingClassifier(
                max_iter=80, max_depth=4, learning_rate=0.15, random_state=0
            ),
        )

    def predict_action_probs(self, X: pd.DataFrame) -> pd.DataFrame:
        """Probabilities as a dataframe with one column per action.

        Actions absent from the training data get probability 0, so the
        caller always sees all four columns.
        """
        proba = self.predict_proba(X)
        by_class = {str(c): proba[:, i] for i, c in enumerate(self.classes_)}
        out = pd.DataFrame(
            {
                a.value: by_class.get(a.value, np.zeros(len(X)))
                for a in ACTION_ORDER
            },
            index=X.index,
        )
        # Renormalize in case a class was dropped (keeps rows summing to 1).
        return out.div(out.sum(axis=1), axis=0)

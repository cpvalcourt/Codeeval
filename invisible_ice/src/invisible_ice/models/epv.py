"""EPV surface generation (Phase 3).

Combines the transition and xG models into the framewise Expected
Possession Value via backward recursion over each possession:

    EPV_T = P(shoot | S_T) * xG(S_T)                        (terminal frame)
    EPV_t = P(shoot | S_t) * xG(S_t)
          + P(turnover | S_t) * 0
          + (P(pass | S_t) + P(keep | S_t)) * EPV_{t+1}

i.e. the continuation term E[EPV(S_{t+dt}) | action] of the spatial
Markov decomposition is approximated by the realized next state — the
standard one-step bootstrap used by EPV systems.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..domain import Action
from .transition import TransitionModel
from .xg import XGModel

EPV_COLUMNS = ["frame_id", "epv", "xg", "p_shoot", "p_pass", "p_keep", "p_turnover"]


class EPVEngine:
    """Computes the framewise EPV curve for a single possession."""

    def __init__(self, transition_model: TransitionModel, xg_model: XGModel):
        self._transition = transition_model
        self._xg = xg_model

    def compute(self, features: pd.DataFrame) -> pd.DataFrame:
        """EPV per frame for one possession's feature matrix.

        ``features`` must contain frame_id plus every model feature, sorted
        or sortable by frame_id. Returns :data:`EPV_COLUMNS`.
        """
        if features.empty:
            return pd.DataFrame(columns=EPV_COLUMNS)
        ordered = features.sort_values("frame_id").reset_index(drop=True)

        action_probs = self._transition.predict_action_probs(ordered)
        xg = np.clip(self._xg.predict_xg(ordered), 0.0, 1.0)

        p_shoot = action_probs[Action.SHOOT.value].to_numpy()
        p_pass = action_probs[Action.PASS.value].to_numpy()
        p_keep = action_probs[Action.KEEP.value].to_numpy()
        p_turnover = action_probs[Action.TURNOVER.value].to_numpy()

        n = len(ordered)
        epv = np.zeros(n)
        epv[n - 1] = p_shoot[n - 1] * xg[n - 1]
        for t in range(n - 2, -1, -1):
            continuation = (p_pass[t] + p_keep[t]) * epv[t + 1]
            epv[t] = p_shoot[t] * xg[t] + continuation
        epv = np.clip(epv, 0.0, 1.0)

        return pd.DataFrame(
            {
                "frame_id": ordered["frame_id"].to_numpy(),
                "epv": epv,
                "xg": xg,
                "p_shoot": p_shoot,
                "p_pass": p_pass,
                "p_keep": p_keep,
                "p_turnover": p_turnover,
            }
        )

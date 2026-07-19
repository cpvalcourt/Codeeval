"""EPVEngine unit tests with deterministic stub models.

The stubs return hand-chosen probabilities so the backward Markov
recursion can be verified against exact arithmetic.
"""

import numpy as np
import pandas as pd

from invisible_ice.models.epv import EPV_COLUMNS, EPVEngine


class StubTransition:
    def __init__(self, probs: dict[str, list[float]]):
        self._probs = probs

    def predict_action_probs(self, X: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(self._probs, index=X.index)


class StubXG:
    def __init__(self, values: list[float]):
        self._values = values

    def predict_xg(self, X: pd.DataFrame) -> np.ndarray:
        return np.asarray(self._values)


def features(n: int) -> pd.DataFrame:
    return pd.DataFrame({"frame_id": range(n), "f": np.zeros(n)})


class TestEPVEngine:
    def test_terminal_frame_epv_is_shot_value(self):
        engine = EPVEngine(
            StubTransition({"shoot": [0.4], "pass": [0.2], "keep": [0.3], "turnover": [0.1]}),
            StubXG([0.25]),
        )
        out = engine.compute(features(1))
        assert np.isclose(out["epv"].iloc[0], 0.4 * 0.25)

    def test_backward_recursion_matches_hand_computation(self):
        engine = EPVEngine(
            StubTransition(
                {
                    "shoot": [0.1, 0.5],
                    "pass": [0.3, 0.1],
                    "keep": [0.5, 0.2],
                    "turnover": [0.1, 0.2],
                }
            ),
            StubXG([0.2, 0.3]),
        )
        out = engine.compute(features(2))
        epv_1 = 0.5 * 0.3  # terminal
        epv_0 = 0.1 * 0.2 + (0.3 + 0.5) * epv_1
        assert np.allclose(out["epv"], [epv_0, epv_1])

    def test_certain_turnover_zeroes_continuation(self):
        engine = EPVEngine(
            StubTransition(
                {
                    "shoot": [0.0, 1.0],
                    "pass": [0.0, 0.0],
                    "keep": [0.0, 0.0],
                    "turnover": [1.0, 0.0],
                }
            ),
            StubXG([0.9, 0.9]),
        )
        out = engine.compute(features(2))
        assert out["epv"].iloc[0] == 0.0  # turnover kills the possession value

    def test_epv_bounded_in_unit_interval(self):
        n = 5
        engine = EPVEngine(
            StubTransition(
                {
                    "shoot": [1.0] * n,
                    "pass": [1.0] * n,  # deliberately unnormalized inputs
                    "keep": [1.0] * n,
                    "turnover": [0.0] * n,
                }
            ),
            StubXG([1.0] * n),
        )
        out = engine.compute(features(n))
        assert (out["epv"] <= 1.0).all()
        assert (out["epv"] >= 0.0).all()

    def test_output_sorted_by_frame_and_has_all_columns(self):
        engine = EPVEngine(
            StubTransition(
                {
                    "shoot": [0.1, 0.1],
                    "pass": [0.2, 0.2],
                    "keep": [0.6, 0.6],
                    "turnover": [0.1, 0.1],
                }
            ),
            StubXG([0.1, 0.1]),
        )
        shuffled = features(2).iloc[::-1]
        out = engine.compute(shuffled)
        assert list(out.columns) == EPV_COLUMNS
        assert out["frame_id"].is_monotonic_increasing

    def test_empty_features_gives_empty_result(self):
        engine = EPVEngine(StubTransition({}), StubXG([]))
        out = engine.compute(features(0))
        assert out.empty
        assert list(out.columns) == EPV_COLUMNS

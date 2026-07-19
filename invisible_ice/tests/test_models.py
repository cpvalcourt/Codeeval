import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from invisible_ice.models.base import NotFittedError, SklearnProbabilityModel
from invisible_ice.models.transition import ACTION_ORDER, TransitionModel
from invisible_ice.models.xg import XGModel

FEATURES = ["f1", "f2"]


def toy_data(n=120, seed=0):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, 2)), columns=FEATURES)
    y = (X["f1"] + 0.2 * rng.normal(size=n) > 0).astype(int).to_numpy()
    return X, y


class TestSklearnProbabilityModel:
    def make(self):
        return SklearnProbabilityModel(FEATURES, LogisticRegression())

    def test_predict_before_fit_raises(self):
        X, _ = toy_data()
        with pytest.raises(NotFittedError):
            self.make().predict_proba(X)

    def test_missing_feature_column_raises(self):
        X, y = toy_data()
        model = self.make().fit(X, y)
        with pytest.raises(ValueError, match="missing feature columns.*f2"):
            model.predict_proba(X[["f1"]])

    def test_extra_columns_are_ignored_and_order_independent(self):
        X, y = toy_data()
        model = self.make().fit(X, y)
        shuffled = X[["f2", "f1"]].assign(extra=1.0)
        np.testing.assert_allclose(
            model.predict_proba(X), model.predict_proba(shuffled)
        )

    def test_empty_feature_names_rejected(self):
        with pytest.raises(ValueError, match="non-empty"):
            SklearnProbabilityModel([], LogisticRegression())

    def test_save_load_roundtrip(self, tmp_path):
        X, y = toy_data()
        model = self.make().fit(X, y)
        path = tmp_path / "model.joblib"
        model.save(path)
        loaded = SklearnProbabilityModel.load(path)
        np.testing.assert_allclose(model.predict_proba(X), loaded.predict_proba(X))


class TestTransitionModel:
    def test_probabilities_cover_all_actions_and_sum_to_one(self):
        X, _ = toy_data(200)
        rng = np.random.default_rng(1)
        y = rng.choice(["shoot", "pass", "keep", "turnover"], size=len(X))
        model = TransitionModel(FEATURES).fit(X, y)
        probs = model.predict_action_probs(X)
        assert list(probs.columns) == [a.value for a in ACTION_ORDER]
        np.testing.assert_allclose(probs.sum(axis=1), 1.0)

    def test_missing_class_gets_zero_probability(self):
        X, _ = toy_data(100)
        y = np.array(["keep", "pass"] * 50)  # no shots, no turnovers
        probs = TransitionModel(FEATURES).fit(X, y).predict_action_probs(X)
        assert (probs["shoot"] == 0.0).all()
        assert (probs["turnover"] == 0.0).all()
        np.testing.assert_allclose(probs.sum(axis=1), 1.0)


class TestXGModel:
    def test_xg_in_unit_interval_and_signal_learned(self):
        X, y = toy_data(300)
        model = XGModel(FEATURES).fit(X, y)
        xg = model.predict_xg(X)
        assert ((xg >= 0) & (xg <= 1)).all()
        # The model must have learned the f1 -> goal relationship.
        assert xg[X["f1"] > 1.0].mean() > xg[X["f1"] < -1.0].mean()

    def test_single_class_training_degenerates_gracefully(self):
        X, _ = toy_data(50)
        never_scores = XGModel(FEATURES).fit(X, np.zeros(len(X), dtype=int))
        np.testing.assert_allclose(never_scores.predict_xg(X), 0.0)
        always_scores = XGModel(FEATURES).fit(X, np.ones(len(X), dtype=int))
        np.testing.assert_allclose(always_scores.predict_xg(X), 1.0)

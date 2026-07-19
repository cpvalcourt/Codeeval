"""Model abstraction (Phase 3) — strategy pattern.

Every learned component implements :class:`ProbabilityModel`, so the EPV
engine depends only on this interface. Today the concrete strategy wraps
scikit-learn; swapping in XGBoost, LightGBM, or a PyTorch module later
means writing one new subclass, with zero changes to the pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


class NotFittedError(RuntimeError):
    pass


class ProbabilityModel(ABC):
    """A classifier exposing class probabilities over named features."""

    def __init__(self, feature_names: list[str]):
        if not feature_names:
            raise ValueError("feature_names must be non-empty")
        self.feature_names = list(feature_names)

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "ProbabilityModel": ...

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """(n_samples, n_classes) probabilities, columns per ``classes_``."""

    @property
    @abstractmethod
    def classes_(self) -> list: ...

    def _validate_features(self, X: pd.DataFrame) -> pd.DataFrame:
        missing = sorted(set(self.feature_names) - set(X.columns))
        if missing:
            raise ValueError(f"missing feature columns: {missing}")
        return X[self.feature_names]

    def save(self, path: Path | str) -> None:
        joblib.dump(self, Path(path))

    @classmethod
    def load(cls, path: Path | str) -> "ProbabilityModel":
        model = joblib.load(Path(path))
        if not isinstance(model, cls):
            raise TypeError(f"{path} does not contain a {cls.__name__}")
        return model


class SklearnProbabilityModel(ProbabilityModel):
    """Concrete strategy wrapping any sklearn classifier with predict_proba."""

    def __init__(self, feature_names: list[str], estimator):
        super().__init__(feature_names)
        self._estimator = estimator
        self._fitted = False

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "SklearnProbabilityModel":
        self._estimator.fit(self._validate_features(X), y)
        self._fitted = True
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self._fitted:
            raise NotFittedError(f"{type(self).__name__} has not been fitted")
        return self._estimator.predict_proba(self._validate_features(X))

    @property
    def classes_(self) -> list:
        if not self._fitted:
            raise NotFittedError(f"{type(self).__name__} has not been fitted")
        return list(self._estimator.classes_)

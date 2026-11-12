"""Training is reproducible: the same data and seed give the same model."""

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification

from uitnodigingsregel.modeling.train import train_random_forest, train_svm


@pytest.fixture
def data() -> pd.DataFrame:
    X, y = make_classification(n_samples=200, n_features=5, random_state=0)
    frame = pd.DataFrame(X, columns=[f"kenmerk_{i}" for i in range(5)])
    frame["Dropout"] = y
    return frame


def test_random_forest_is_reproducible(data, tmp_path):
    grid = {"n_estimators": [30], "max_features": [2]}
    models = [
        train_random_forest(data, 42, "Dropout", grid, tmp_path / f"rf_{i}.joblib")
        for i in range(2)
    ]
    X = data.drop(columns="Dropout").values
    np.testing.assert_array_equal(models[0].predict(X), models[1].predict(X))


def test_svm_is_reproducible(data, tmp_path):
    grid = {"C": [1.0], "kernel": ["rbf"]}
    models = [train_svm(data, 42, "Dropout", grid, tmp_path / f"svm_{i}.joblib") for i in range(2)]
    X = data.drop(columns="Dropout").values
    np.testing.assert_array_equal(models[0].predict_proba(X), models[1].predict_proba(X))

"""Tests for dataset module."""

import numpy as np
import pandas as pd

from uitnodigingsregel.dataset import impute_missing_values, remove_single_value_columns


def test_impute_missing_values_fills_na() -> None:
    train = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0, 5.0], "b": [5.0, 4.0, 3.0, 2.0, 1.0]})
    pred = pd.DataFrame({"a": [np.nan, 3.0], "b": [5.0, np.nan]})
    train_out, pred_out = impute_missing_values(train, pred)
    assert not train_out.isna().any().any()
    assert not pred_out.isna().any().any()


def test_impute_missing_values_fits_on_train_only() -> None:
    # pred has very different values — imputer must use train distribution, not pred
    train = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0, 5.0], "b": [1.0, 2.0, 3.0, 4.0, 5.0]})
    pred = pd.DataFrame({"a": [np.nan, 100.0], "b": [100.0, np.nan]})
    train_out, pred_out = impute_missing_values(train, pred)
    # imputed values should be close to train range, not pred range
    assert pred_out["a"].iloc[0] < 10
    assert pred_out["b"].iloc[1] < 10


def test_remove_single_value_columns() -> None:
    train = pd.DataFrame({"a": [1, 1, 1], "b": [1, 2, 3]})
    pred = pd.DataFrame({"a": [1, 1], "b": [4, 5]})
    train_out, pred_out = remove_single_value_columns(train, pred)
    assert "a" not in train_out.columns
    assert "a" not in pred_out.columns
    assert "b" in train_out.columns

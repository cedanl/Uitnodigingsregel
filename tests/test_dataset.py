"""Tests for dataset module."""

import numpy as np
import pandas as pd

from uitnodigingsregel.dataset import clean_data, remove_single_value_columns


def test_clean_data_removes_duplicates() -> None:
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    result = clean_data(df)
    assert len(result) == 2


def test_clean_data_fills_missing_numeric() -> None:
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [4.0, 5.0, 6.0]})
    result = clean_data(df)
    assert not result["a"].isna().any()


def test_remove_single_value_columns() -> None:
    train = pd.DataFrame({"a": [1, 1, 1], "b": [1, 2, 3]})
    pred = pd.DataFrame({"a": [1, 1], "b": [4, 5]})
    train_out, pred_out = remove_single_value_columns(train, pred)
    assert "a" not in train_out.columns
    assert "a" not in pred_out.columns
    assert "b" in train_out.columns

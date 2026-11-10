"""Tests for data loading and validation."""

from pathlib import Path

import pandas as pd
import pytest

from uitnodigingsregel.dataset import (
    DataValidationError,
    load_student_data,
    read_student_data,
    validate_student_data,
)

DEMO_TRAIN = Path("data/01-raw/demo/synth_data_train.csv")
DEMO_PRED = Path("data/01-raw/demo/synth_data_pred.csv")


def _train_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Studentnummer": [1, 2, 3, 4],
            "Dropout": [0, 1, 0, 1],
            "StudentAge": [17.5, 18.0, 19.5, 20.0],
            "Richting": ["a", "b", "a", "b"],
        }
    )


def _pred_df() -> pd.DataFrame:
    return _train_df().assign(Dropout=0)


@pytest.mark.parametrize("separator", ["\t", ";", ",", "|"])
def test_read_detects_separator(separator: str) -> None:
    content = _train_df().to_csv(sep=separator, index=False).encode("utf-8")
    pd.testing.assert_frame_equal(read_student_data(content), _train_df())


def test_read_converts_decimal_commas_and_keeps_text() -> None:
    content = _train_df().to_csv(sep=";", decimal=",", index=False).encode("utf-8")
    pd.testing.assert_frame_equal(read_student_data(content), _train_df(), check_dtype=False)


def test_read_handles_excel_encodings() -> None:
    df = _train_df().assign(Richting=["café", "b", "café", "b"])
    for encoding in ("utf-8-sig", "cp1252"):
        content = df.to_csv(sep=";", index=False).encode(encoding)
        pd.testing.assert_frame_equal(read_student_data(content), df)


def test_load_demo_data_equals_plain_read() -> None:
    train_df, pred_df = load_student_data(DEMO_TRAIN, DEMO_PRED)
    expected_train = pd.read_csv(DEMO_TRAIN, sep="\t").drop_duplicates()
    expected_pred = pd.read_csv(DEMO_PRED, sep="\t").drop_duplicates()
    pd.testing.assert_frame_equal(train_df, expected_train)
    pd.testing.assert_frame_equal(pred_df, expected_pred)


def test_load_adds_missing_target_to_prediction_data() -> None:
    train = _train_df().to_csv(sep=";", index=False).encode("utf-8")
    pred = _pred_df().drop(columns=["Dropout"]).to_csv(sep=";", index=False).encode("utf-8")
    _, pred_df = load_student_data(train, pred)
    pd.testing.assert_frame_equal(pred_df, _pred_df())


def test_validate_accepts_valid_data() -> None:
    validate_student_data(_train_df(), _pred_df())


@pytest.mark.parametrize(
    ("train_df", "pred_df", "message"),
    [
        (_train_df().drop(columns=["Dropout"]), _pred_df(), "ontbreekt de kolom 'Dropout'"),
        (_train_df(), _pred_df().drop(columns=["Studentnummer"]), "predictiedata ontbreekt"),
        (_train_df().assign(Dropout=[0, 1, 2, 1]), _pred_df(), "alleen 0 en 1"),
        (_train_df().assign(Dropout=[0, 1, None, 1]), _pred_df(), "alleen 0 en 1"),
        (_train_df().assign(Dropout=0), _pred_df(), "zowel uitvallers"),
        (_train_df(), _pred_df().drop(columns=["StudentAge"]), "'StudentAge'"),
        (_train_df(), _pred_df().assign(Extra=1), "'Extra'"),
        (
            _train_df().drop(columns=["StudentAge"]),
            _pred_df().drop(columns=["StudentAge"]),
            "geen kolommen met getallen",
        ),
        (_train_df().iloc[0:0], _pred_df(), "bevat geen rijen"),
    ],
)
def test_validate_rejects_invalid_data(
    train_df: pd.DataFrame, pred_df: pd.DataFrame, message: str
) -> None:
    with pytest.raises(DataValidationError, match=message):
        validate_student_data(train_df, pred_df)


def test_unknown_separator_reports_found_columns() -> None:
    content = _train_df().to_csv(sep="#", index=False).encode("utf-8")
    with pytest.raises(DataValidationError, match="scheidingsteken"):
        load_student_data(content, content)

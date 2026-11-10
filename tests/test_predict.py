"""Tests for model loading and training-data fingerprints."""

from pathlib import Path

import pandas as pd

from uitnodigingsregel.modeling.predict import (
    FINGERPRINT_FILE,
    MODEL_FILES,
    check_models_match_data,
    compute_data_fingerprint,
    save_fingerprint,
)


def _train_df() -> pd.DataFrame:
    return pd.DataFrame({"Studentnummer": [1, 2, 3], "Dropout": [0, 1, 0]})


def _write_model_files(models_dir: Path) -> None:
    for name in MODEL_FILES:
        (models_dir / name).write_bytes(b"")


def test_fingerprint_is_stable_for_equal_data() -> None:
    assert compute_data_fingerprint(_train_df()) == compute_data_fingerprint(_train_df())


def test_fingerprint_changes_with_values_and_columns() -> None:
    base = compute_data_fingerprint(_train_df())
    other_values = _train_df().assign(Dropout=[1, 1, 0])
    other_columns = _train_df().rename(columns={"Dropout": "Uitval"})
    assert compute_data_fingerprint(other_values) != base
    assert compute_data_fingerprint(other_columns) != base


def test_no_match_without_models(tmp_path: Path) -> None:
    fingerprint = compute_data_fingerprint(_train_df())
    save_fingerprint(fingerprint, tmp_path)
    assert not check_models_match_data(fingerprint, tmp_path)


def test_no_match_without_fingerprint_file(tmp_path: Path) -> None:
    _write_model_files(tmp_path)
    assert not check_models_match_data(compute_data_fingerprint(_train_df()), tmp_path)


def test_no_match_with_unreadable_fingerprint_file(tmp_path: Path) -> None:
    _write_model_files(tmp_path)
    (tmp_path / FINGERPRINT_FILE).write_text("geen json", encoding="utf-8")
    assert not check_models_match_data(compute_data_fingerprint(_train_df()), tmp_path)


def test_match_only_for_same_training_data(tmp_path: Path) -> None:
    _write_model_files(tmp_path)
    fingerprint = compute_data_fingerprint(_train_df())
    save_fingerprint(fingerprint, tmp_path)
    assert check_models_match_data(fingerprint, tmp_path)
    other = compute_data_fingerprint(_train_df().assign(Dropout=[1, 1, 0]))
    assert not check_models_match_data(other, tmp_path)

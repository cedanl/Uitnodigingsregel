"""Smoke test: the full pipeline runs on the demo data."""

import sys
from pathlib import Path

import pandas as pd
import pytest

from uitnodigingsregel.evaluate import load_settings
from uitnodigingsregel.modeling.predict import (
    MODEL_FILES,
    check_models_match_data,
    compute_data_fingerprint,
    load_models,
)

ROOT_DIR = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT_DIR))

from main import run_pipeline  # noqa: E402

DEMO_TRAIN = ROOT_DIR / "data/01-raw/demo/synth_data_train.csv"
DEMO_PRED = ROOT_DIR / "data/01-raw/demo/synth_data_pred.csv"


@pytest.fixture
def settings() -> dict:
    """Default settings with a one-point parameter grid, so training takes seconds."""
    settings = load_settings()
    settings["retrain_models"] = True
    settings["rf_parameters"] = {"n_estimators": [10], "max_depth": [2]}
    settings["alpha_range"] = [0.1]
    settings["svm_parameters"] = {"C": [1], "gamma": [0.01], "kernel": ["rbf"]}
    return settings


def _assert_ranked_lists_cover_students(ranked: tuple, pred_df: pd.DataFrame, id_col: str) -> None:
    assert len(ranked) == 3
    for ranked_df in ranked:
        assert len(ranked_df) == len(pred_df)
        assert set(ranked_df[id_col]) == set(pred_df[id_col])


def test_pipeline_trains_and_ranks_demo_data(settings: dict, tmp_path: Path) -> None:
    id_col = settings["studentnumber_column"]
    pred_df = pd.read_csv(DEMO_PRED, sep="\t").drop_duplicates()

    ranked = run_pipeline(DEMO_TRAIN, DEMO_PRED, settings, models_dir=tmp_path)

    _assert_ranked_lists_cover_students(ranked, pred_df, id_col)
    assert all((tmp_path / name).exists() for name in MODEL_FILES)
    train_df = pd.read_csv(DEMO_TRAIN, sep="\t").drop_duplicates()
    assert check_models_match_data(compute_data_fingerprint(train_df), tmp_path)

    settings["retrain_models"] = False
    reloaded = run_pipeline(DEMO_TRAIN, DEMO_PRED, settings, models_dir=tmp_path)
    for first, second in zip(ranked, reloaded, strict=True):
        pd.testing.assert_frame_equal(first, second)


def test_pipeline_reads_semicolon_separated_data(settings: dict, tmp_path: Path) -> None:
    id_col = settings["studentnumber_column"]
    pred_df = pd.read_csv(DEMO_PRED, sep="\t").drop_duplicates()
    train_path = tmp_path / "train.csv"
    pred_path = tmp_path / "pred.csv"
    pd.read_csv(DEMO_TRAIN, sep="\t").to_csv(train_path, sep=";", decimal=",", index=False)
    pred_df.to_csv(pred_path, sep=";", decimal=",", index=False)

    ranked = run_pipeline(train_path, pred_path, settings, models_dir=tmp_path / "models")

    _assert_ranked_lists_cover_students(ranked, pred_df, id_col)


def test_duplicate_rows_do_not_shift_scores_between_students(
    settings: dict, tmp_path: Path
) -> None:
    pred_df = pd.read_csv(DEMO_PRED, sep="\t").drop_duplicates()
    pred_path = tmp_path / "pred_with_duplicates.csv"
    pd.concat([pred_df.iloc[:3], pred_df]).to_csv(pred_path, sep="\t", index=False)
    models_dir = tmp_path / "models"

    expected = run_pipeline(DEMO_TRAIN, DEMO_PRED, settings, models_dir=models_dir)
    settings["retrain_models"] = False
    ranked = run_pipeline(DEMO_TRAIN, pred_path, settings, models_dir=models_dir)

    for expected_df, ranked_df in zip(expected, ranked, strict=True):
        pd.testing.assert_frame_equal(expected_df, ranked_df)


def test_pipeline_accepts_text_ids_and_keeps_them_out_of_the_models(
    settings: dict, tmp_path: Path
) -> None:
    id_col = settings["studentnumber_column"]
    train_df = pd.read_csv(DEMO_TRAIN, sep="\t").drop_duplicates()
    pred_df = pd.read_csv(DEMO_PRED, sep="\t").drop_duplicates()
    train_df[id_col] = "s" + train_df[id_col].astype(str)
    pred_df[id_col] = "s" + pred_df[id_col].astype(str)
    train_path = tmp_path / "train.csv"
    pred_path = tmp_path / "pred.csv"
    train_df.to_csv(train_path, sep="\t", index=False)
    pred_df.to_csv(pred_path, sep="\t", index=False)
    models_dir = tmp_path / "models"

    ranked = run_pipeline(train_path, pred_path, settings, models_dir=models_dir)
    numeric_ids = run_pipeline(DEMO_TRAIN, DEMO_PRED, settings, models_dir=tmp_path / "other")

    _assert_ranked_lists_cover_students(ranked, pred_df, id_col)
    rf_model, _, _ = load_models(models_dir)
    rf_numeric, _, _ = load_models(tmp_path / "other")
    assert rf_model.n_features_in_ == rf_numeric.n_features_in_
    assert rf_model.n_features_in_ <= train_df.shape[1] - 2
    lasso_text, lasso_numeric = ranked[1], numeric_ids[1]
    assert lasso_text["voorspelling"].tolist() == lasso_numeric["voorspelling"].tolist()

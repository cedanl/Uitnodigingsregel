"""Golden master / snapshot test for model output.

Verifies that the pipeline produces identical ranked predictions compared to
the committed baseline fixtures. Run `uv run python tests/update_snapshots.py`
to intentionally update the baseline after a deliberate model change.
"""

from pathlib import Path

import pandas as pd
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).parent.parent

SNAPSHOTS = {
    "rf": FIXTURES_DIR / "snapshot_rf.csv",
    "lasso": FIXTURES_DIR / "snapshot_lasso.csv",
    "svm": FIXTURES_DIR / "snapshot_svm.csv",
}


@pytest.fixture(scope="module")
def pipeline_output() -> dict[str, pd.DataFrame]:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from main import run_pipeline  # noqa: PLC0415

    from uitnodigingsregel.evaluate import load_settings  # noqa: PLC0415

    settings = load_settings()
    # Load the committed fixture models instead of retraining, so the test is
    # deterministic regardless of GridSearchCV parallelism or random state issues.
    settings["retrain_models"] = False

    train_path = REPO_ROOT / settings["synth_data_dir_train"]
    pred_path = REPO_ROOT / settings["synth_data_dir_pred"]

    ranked_rf, ranked_lasso, ranked_svm = run_pipeline(
        train_path, pred_path, settings, models_dir=FIXTURES_DIR / "models"
    )
    return {"rf": ranked_rf, "lasso": ranked_lasso, "svm": ranked_svm}


@pytest.mark.parametrize("model", ["rf", "lasso", "svm"])
def test_snapshot(model: str, pipeline_output: dict[str, pd.DataFrame]) -> None:
    snapshot_path = SNAPSHOTS[model]
    if not snapshot_path.exists():
        pytest.fail(
            f"Snapshot fixture not found: {snapshot_path}\n"
            "Run `uv run python tests/update_snapshots.py` to generate it."
        )

    baseline = pd.read_csv(snapshot_path, sep=";")
    actual = pipeline_output[model]

    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        baseline.reset_index(drop=True),
        check_exact=False,
        atol=1e-6,
        obj=f"{model.upper()} snapshot",
    )

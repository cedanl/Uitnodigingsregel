"""Generate golden master snapshot fixtures for model output tests.

Run this script intentionally when model output is expected to change:

    uv run python tests/update_snapshots.py

The generated CSV files in tests/fixtures/ should be committed to the repository.
"""

import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from uitnodigingsregel.evaluate import load_settings  # noqa: E402


def main() -> None:
    from main import run_pipeline  # noqa: PLC0415

    settings = load_settings()
    settings["retrain_models"] = True

    train_path = REPO_ROOT / settings["synth_data_dir_train"]
    pred_path = REPO_ROOT / settings["synth_data_dir_pred"]
    models_dir = FIXTURES_DIR / "models"

    print("Running pipeline on synthetic demo data with fixed seed...")
    ranked_rf, ranked_lasso, ranked_svm = run_pipeline(
        train_path, pred_path, settings, models_dir=models_dir
    )

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    ranked_rf.to_csv(FIXTURES_DIR / "snapshot_rf.csv", sep=";", index=False)
    ranked_lasso.to_csv(FIXTURES_DIR / "snapshot_lasso.csv", sep=";", index=False)
    ranked_svm.to_csv(FIXTURES_DIR / "snapshot_svm.csv", sep=";", index=False)

    print(f"Snapshots written to {FIXTURES_DIR}")
    print(f"  snapshot_rf.csv    ({len(ranked_rf)} rows)")
    print(f"  snapshot_lasso.csv ({len(ranked_lasso)} rows)")
    print(f"  snapshot_svm.csv   ({len(ranked_svm)} rows)")


if __name__ == "__main__":
    main()

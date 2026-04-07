"""Regenerate golden master snapshot fixtures.

Run ONLY when model output is intentionally expected to change:

    uv run python snapshots/update.py --confirm

The generated CSV files in snapshots/fixtures/ should be committed to the
repository so that snapshots/compare.py can detect future drift.
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(REPO_ROOT))

from uitnodigingsregel.evaluate import load_settings  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate snapshot fixtures.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required flag — confirms intentional fixture regeneration.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "ERROR: Pass --confirm to regenerate snapshots.\n"
            "This overwrites committed fixtures and should only be done after a "
            "deliberate model change."
        )
        sys.exit(1)

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

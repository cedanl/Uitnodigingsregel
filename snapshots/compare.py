"""Compare current pipeline output against committed snapshot fixtures.

Produces a side-by-side ranking report without pass/fail semantics:

    uv run python snapshots/compare.py
    uv run python snapshots/compare.py --save       # also saves HTML report
    uv run python snapshots/compare.py --top 20     # tune the top-N window

Output (printed and optionally saved to snapshots/reports/compare_YYYYMMDD.html):
  - Per-model side-by-side rank table (baseline rank | student | new rank | shift)
  - Per-model summary stats: mean absolute rank shift, students entering/leaving top N
  - Overall verdict: UNCHANGED / MINOR DRIFT / MAJOR DRIFT
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).parent.parent
SNAPSHOTS_DIR = Path(__file__).parent
FIXTURES_DIR = SNAPSHOTS_DIR / "fixtures"
REPORTS_DIR = SNAPSHOTS_DIR / "reports"
sys.path.insert(0, str(REPO_ROOT))

MODELS = {
    "rf": FIXTURES_DIR / "snapshot_rf.csv",
    "lasso": FIXTURES_DIR / "snapshot_lasso.csv",
    "svm": FIXTURES_DIR / "snapshot_svm.csv",
}
MODEL_LABELS = {"rf": "Random Forest", "lasso": "Lasso", "svm": "SVM"}


def run_current_pipeline() -> dict[str, pd.DataFrame]:
    from main import run_pipeline  # noqa: PLC0415
    from uitnodigingsregel.evaluate import load_settings  # noqa: PLC0415

    settings = load_settings()
    # Use committed fixture models — keeps comparison deterministic (no retraining noise)
    settings["retrain_models"] = False

    train_path = REPO_ROOT / settings["synth_data_dir_train"]
    pred_path = REPO_ROOT / settings["synth_data_dir_pred"]

    ranked_rf, ranked_lasso, ranked_svm = run_pipeline(
        train_path, pred_path, settings, models_dir=FIXTURES_DIR / "models"
    )
    return {"rf": ranked_rf, "lasso": ranked_lasso, "svm": ranked_svm}


def load_baseline(model_key: str) -> pd.DataFrame:
    path = MODELS[model_key]
    if not path.exists():
        raise FileNotFoundError(
            f"Baseline fixture not found: {path}\n"
            "Run `uv run python snapshots/update.py --confirm` to generate it."
        )
    return pd.read_csv(path, sep=";")


def compare_model(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    top_n: int = 20,
) -> dict:
    id_col = "Studentnummer"
    rank_col = "ranking"

    base = baseline[[id_col, rank_col]].rename(columns={rank_col: "baseline_rank"})
    curr = current[[id_col, rank_col]].rename(columns={rank_col: "new_rank"})

    merged = base.merge(curr, on=id_col, how="outer")
    merged["shift"] = merged["new_rank"] - merged["baseline_rank"]

    mean_abs_shift = merged["shift"].abs().mean()
    max_shift = merged["shift"].abs().max()

    base_top = set(base.loc[base["baseline_rank"] <= top_n, id_col])
    curr_top = set(curr.loc[curr["new_rank"] <= top_n, id_col])
    top_n_added = sorted(curr_top - base_top)
    top_n_removed = sorted(base_top - curr_top)

    diff_df = merged.sort_values("baseline_rank").reset_index(drop=True)

    return {
        "diff_df": diff_df,
        "mean_abs_shift": mean_abs_shift,
        "max_shift": max_shift,
        "top_n_added": top_n_added,
        "top_n_removed": top_n_removed,
    }


def drift_label(mean_abs_shift: float) -> str:
    if mean_abs_shift < 0.5:
        return "UNCHANGED"
    if mean_abs_shift < 3.0:
        return "MINOR DRIFT"
    return "MAJOR DRIFT"


def build_html_report(results: dict[str, dict], top_n: int) -> str:
    today = date.today().isoformat()
    sections = []

    for key, label in MODEL_LABELS.items():
        r = results[key]
        diff_df = r["diff_df"]
        verdict = drift_label(r["mean_abs_shift"])

        rows_html = []
        for _, row in diff_df.iterrows():
            try:
                shift_val = float(row["shift"])
            except (TypeError, ValueError):
                shift_val = 0.0

            bg = "#fff8c5" if abs(shift_val) > 0.5 else "white"
            arrow = ("▲" if shift_val < 0 else "▼") if abs(shift_val) > 0.5 else "="
            rows_html.append(
                f"<tr style='background:{bg}'>"
                f"<td>{row['Studentnummer']}</td>"
                f"<td>{row['baseline_rank']}</td>"
                f"<td>{row['new_rank']}</td>"
                f"<td>{shift_val:+.1f} {arrow}</td>"
                f"</tr>"
            )

        sections.append(f"""
<h2>{label} — {verdict}</h2>
<p>Mean absolute rank shift: <strong>{r['mean_abs_shift']:.2f}</strong> &nbsp;|&nbsp;
   Max shift: <strong>{r['max_shift']:.1f}</strong></p>
<p>Students entering top {top_n}: {r['top_n_added'] or 'none'}</p>
<p>Students leaving top {top_n}: {r['top_n_removed'] or 'none'}</p>
<table border="1" cellpadding="4" cellspacing="0">
  <thead><tr>
    <th>Studentnummer</th><th>Baseline rank</th><th>New rank</th><th>Shift</th>
  </tr></thead>
  <tbody>{''.join(rows_html)}</tbody>
</table>
""")

    overall = max(
        (drift_label(results[k]["mean_abs_shift"]) for k in results),
        key=lambda v: {"UNCHANGED": 0, "MINOR DRIFT": 1, "MAJOR DRIFT": 2}[v],
    )
    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Snapshot comparison — {today}</title>
<style>
  body {{ font-family: sans-serif; margin: 2rem; }}
  table {{ border-collapse: collapse; font-size: .85rem; }}
</style>
</head><body>
<h1>Snapshot comparison — {today}</h1>
<p>Overall verdict: <strong>{overall}</strong> (top-{top_n} window)</p>
{body}
</body></html>"""


def print_summary(results: dict[str, dict], top_n: int) -> None:
    for key, label in MODEL_LABELS.items():
        r = results[key]
        print(f"\n--- {label} ({drift_label(r['mean_abs_shift'])}) ---")
        print(f"  Mean absolute rank shift : {r['mean_abs_shift']:.2f}")
        print(f"  Max rank shift           : {r['max_shift']:.1f}")
        print(f"  Students entering top {top_n} : {r['top_n_added'] or 'none'}")
        print(f"  Students leaving top {top_n}  : {r['top_n_removed'] or 'none'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare pipeline output to snapshot fixtures."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        metavar="N",
        help="Size of the top-N window for entry/exit stats (default: 20).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save HTML report to snapshots/reports/compare_YYYYMMDD.html.",
    )
    args = parser.parse_args()

    print("Loading snapshot baselines...")
    baselines = {key: load_baseline(key) for key in MODELS}

    print("Running current pipeline (using fixture models, retrain_models=False)...")
    current = run_current_pipeline()

    results = {key: compare_model(baselines[key], current[key], top_n=args.top) for key in MODELS}

    print_summary(results, top_n=args.top)

    if args.save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = REPORTS_DIR / f"compare_{date.today().strftime('%Y%m%d')}.html"
        html = build_html_report(results, top_n=args.top)
        filename.write_text(html, encoding="utf-8")
        print(f"\nReport saved to {filename}")


if __name__ == "__main__":
    main()

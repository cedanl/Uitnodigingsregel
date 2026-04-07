# Snapshots — golden master fixtures

This directory contains committed baseline fixtures for the three trained models
(Random Forest, Lasso, SVM). They are **not tests** — no CI runs against them.
They exist so you can detect whether a code or dependency change shifted the
model output, and by how much.

## Directory layout

```
snapshots/
  fixtures/
    snapshot_rf.csv           ← ranked predictions from Random Forest
    snapshot_lasso.csv        ← ranked predictions from Lasso
    snapshot_svm.csv          ← ranked predictions from SVM
    models/
      random_forest_regressor.joblib
      lasso_regression.joblib
      support_vector_machine.joblib
  reports/                    ← generated comparison reports (gitignored)
  update.py                   ← regenerates fixtures (requires --confirm)
  compare.py                  ← produces drift report (no pass/fail)
```

## Workflows

### Detect drift since last snapshot

```bash
make snapshot-compare
# or with an HTML report:
uv run python snapshots/compare.py --save
```

Output: per-model rank-shift summary and an overall verdict:
`UNCHANGED / MINOR DRIFT / MAJOR DRIFT`

### Update snapshots after a deliberate model change

```bash
make snapshot-update
# or: uv run python snapshots/update.py --confirm
```

Commit the changed CSV files and `.joblib` files together with the code change.

## What the comparison report contains

- Per-model side-by-side table: baseline rank | student number | new rank | shift
- Mean absolute rank shift and max shift
- Students entering / leaving the top 20 (configurable with `--top N`)
- Overall verdict: UNCHANGED / MINOR DRIFT / MAJOR DRIFT

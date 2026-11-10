# Uitnodigingsregel

## Overview
Dropout prediction models for student intervention planning. Trains Random Forest, Lasso, and SVM models on student data and ranks students by predicted dropout probability. Type 2 (Analysis) repository.

## Standards
Follow CEDA technical standards: https://github.com/cedanl/.github/tree/main/standards/README.md

## Tech Stack
- Python 3.13, uv for dependency management
- scikit-learn (RF, Lasso, SVM), pandas, matplotlib/seaborn
- Streamlit for interactive app
- Quarto for model analysis report
- ruff for linting/formatting

## Project Structure
```
├── src/uitnodigingsregel/       # Installable package
│   ├── cli.py                   # CLI entrypoint (uitnodigingsregel command)
│   ├── dataset.py               # Data loading and validation (load_student_data, detect_separator)
│   ├── evaluate.py              # Model evaluation (load_settings, prepare_model_predictions, etc.)
│   ├── visualize.py             # Plotting (generate_precision_plot, generate_sensitivity_plot, etc.)
│   ├── analyze.py               # Analysis helpers (get_coefficient_table, get_top_svm_features, etc.)
│   ├── report.py                # Quarto report: input data selection and rendering (render_report)
│   ├── modeling/
│   │   ├── train.py             # Model training (train_random_forest, train_lasso, train_svm)
│   │   └── predict.py           # Model prediction (predict_random_forest, predict_lasso, predict_svm)
│   ├── app/                     # Streamlit app (installed as package data)
│   │   ├── main.py              # App entrypoint
│   │   └── styles.py            # CSS en kleurconstanten
│   └── metadata/
│       └── config.yaml          # Model hyperparameters and settings
├── data/
│   ├── 01-raw/                  # Input data
│   │   ├── demo/                # Synthetic data (committed)
│   │   └── user_data/           # User-provided data (gitignored)
│   ├── 02-prepared/             # Standardized datasets
│   └── 03-output/               # Processed datasets
├── models/                      # Trained model files (.joblib) and training_data.json (gitignored)
│   ├── predictions/             # Ranked lists written by main.py
│   └── report/                  # Models trained by the report
├── reports/                     # Generated reports and figures
├── tests/                       # Unit tests and pipeline smoke test
├── snapshots/                   # Golden master comparison of pipeline output
├── docs/                        # MkDocs site (GitHub Pages)
├── Model_analysis.qmd           # Quarto analysis report
├── main.py                      # Pipeline entrypoint
└── Makefile                     # Convenience commands
```

## How to Run
```bash
uv sync                              # Install dependencies
uv run python main.py                # Run full pipeline
uv run uitnodigingsregel             # Launch interactive app (CLI)
uv run quarto render Model_analysis.qmd  # Render analysis report
uv run ruff check src tests main.py  # Lint
uv run pytest                        # Test
uv run --group docs mkdocs build --strict  # Build docs
```

## Data
- Input: student records with features and a `Dropout` column (binary)
- Output: ranked students by predicted dropout probability
- Demo data in `data/01-raw/demo/` uses synthetic data
- User data goes in `data/01-raw/user_data/` (gitignored)
- CSV input: separator is detected automatically (tab, `;`, `,`, `|`); decimal comma is accepted when the separator is not `,`
- The report describes the training data passed by the app (env `UITNODIGINGSREGEL_TRAIN_DATA`), else `data/01-raw/user_data/train.csv`, else the demo data. It trains its own models on an 80% split in `models/report/`; the pipeline models in `models/` are trained on all data
- Training and prediction data need the same columns; a missing `Dropout` column in the prediction data is added with value 0

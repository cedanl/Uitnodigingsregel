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
│   ├── dataset.py               # Data cleaning (clean_data, remove_single_value_columns)
│   ├── features.py              # Feature engineering (convert_categorical_to_dummies, standardize_dataset)
│   ├── evaluate.py              # Model evaluation (load_settings, prepare_model_predictions, etc.)
│   ├── visualize.py             # Plotting (generate_precision_plot, generate_sensitivity_plot, etc.)
│   ├── analyze.py               # Analysis helpers (get_coefficient_table, get_top_svm_features, etc.)
│   ├── modeling/
│   │   ├── train.py             # Model training (train_random_forest, train_lasso, train_svm)
│   │   └── predict.py           # Model prediction (predict_random_forest, predict_lasso, predict_svm)
│   └── metadata/
│       └── config.yaml          # Model hyperparameters and settings
├── app/                         # Streamlit app (thin wrapper)
│   ├── main.py
│   └── config.toml              # Data paths
├── data/
│   ├── 01-raw/                  # Input data
│   │   ├── demo/                # Synthetic data (committed)
│   │   └── user_data/           # User-provided data (gitignored)
│   ├── 02-prepared/             # Standardized datasets
│   └── 03-output/               # Processed datasets
├── models/                      # Trained model files (.joblib)
├── reports/                     # Generated reports and figures
├── Model_analysis.qmd           # Quarto analysis report
├── main.py                      # Pipeline entrypoint
├── config.yaml                  # Root config (used by main.py and .qmd)
└── Makefile                     # Convenience commands
```

## How to Run
```bash
uv sync                              # Install dependencies
uv run python main.py                # Run full pipeline
uv run streamlit run app/main.py     # Launch interactive app
quarto render Model_analysis.qmd     # Render analysis report
uv run ruff check src app            # Lint
uv run pytest                        # Test
```

## Data
- Input: student records with features and a `Dropout` column (binary)
- Output: ranked students by predicted dropout probability
- Demo data in `data/01-raw/demo/` uses synthetic data
- User data goes in `data/01-raw/user_data/` (gitignored)
- CSV delimiter: `;`

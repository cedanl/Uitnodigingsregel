"""Data analysis helpers: feature importance, missing data, metrics parsing."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.svm import SVC


def get_coefficient_table(
    X_train: pd.DataFrame,
    model: Lasso,
    X_train_original: pd.DataFrame,
) -> pd.Series:
    """Get Lasso coefficients scaled back to original feature scale.

    Args:
        X_train: Standardized training features.
        model: Trained Lasso model.
        X_train_original: Original (unstandardized) training features.

    Returns:
        Series of coefficients indexed by feature name.
    """
    if isinstance(X_train, pd.DataFrame):
        coefs = pd.Series(model.coef_, index=X_train.columns)
        feature_stds = X_train_original.std()
        return coefs / feature_stds
    return pd.Series(model.coef_, index=[f"Feature {i}" for i in range(len(model.coef_))])


def get_top_svm_features(
    validation_data: pd.DataFrame,
    svm_model: SVC,
    train_data_sdd: pd.DataFrame | None = None,
    n_features: int = 5,
    dropout_column: str = "Dropout",
) -> list[tuple[str, float]]:
    """Get top N features from SVM model using perturbation importance.

    Args:
        validation_data: DataFrame with features and dropout column.
        svm_model: Trained SVM model.
        train_data_sdd: Scaled training data (preferred over validation_data).
        n_features: Number of top features to return.
        dropout_column: Name of the target column.

    Returns:
        List of (feature_name, importance) tuples sorted by importance.
    """
    data = train_data_sdd.copy() if train_data_sdd is not None else validation_data.copy()
    data = data.fillna(data.mean())
    data = data.replace([np.inf, -np.inf], np.nan).fillna(data.mean())

    X = data.drop(dropout_column, axis=1)
    feature_names = X.columns

    calibrated_svm = CalibratedClassifierCV(svm_model, method="sigmoid", cv="prefit")
    calibrated_svm.fit(X, data[dropout_column])
    prob_original = calibrated_svm.predict_proba(X)[:, 1]

    perturbation = 1.0
    feature_stds = X.std()
    feature_importance = []
    for fname in feature_names:
        X_perturbed = X.copy()
        X_perturbed[fname] = X_perturbed[fname] + perturbation * feature_stds[fname]
        prob_perturbed = calibrated_svm.predict_proba(X_perturbed)[:, 1]
        prob_change = np.mean(prob_perturbed - prob_original)
        feature_importance.append((fname, abs(prob_change)))

    feature_importance.sort(key=lambda x: x[1], reverse=True)
    return feature_importance[:n_features]


def analyze_missing_data(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, int, int, int, int]:
    """Analyze missing values in a DataFrame.

    Args:
        data: DataFrame to analyze.

    Returns:
        Tuple of (summary_df, total_missing, total_rows, total_cols, n_cols_with_missing).
    """
    missing_summary = pd.DataFrame(
        {
            "Type": data.dtypes,
            "Aantal_Missing": data.isnull().sum(),
            "Percentage_Missing": (data.isnull().sum() / len(data) * 100).round(1),
        }
    )
    return (
        missing_summary,
        data.isnull().sum().sum(),
        len(data),
        len(data.columns),
        (data.isnull().sum() > 0).sum(),
    )


def parse_model_metrics(
    metrics_file_path: Path = Path("reports/model_evaluation.txt"),
) -> list[dict]:
    """Parse model evaluation metrics from a text report file.

    Args:
        metrics_file_path: Path to the model evaluation text file.

    Returns:
        List of dicts with Model, R² (train/test), MSE (train/test) keys.
    """
    try:
        with open(metrics_file_path, encoding="utf-8") as f:
            metrics_text = f.read()
    except FileNotFoundError:
        return []

    metrics_data = []
    current_model = None
    r2_train = r2_test = mse_train = mse_test = None

    for line in metrics_text.split("\n"):
        line = line.strip()
        if "Metrics:" in line and not line.startswith(("Model Evaluation", "=")):
            current_model = line.split(" Metrics:")[0].strip()
            r2_train = r2_test = mse_train = mse_test = None
        elif current_model:
            if "R² (Training):" in line:
                r2_train = float(line.split(":")[1].strip())
            elif "R² (Validation):" in line:
                r2_test = float(line.split(":")[1].strip())
            elif "MSE (Training):" in line:
                mse_train = float(line.split(":")[1].strip())
            elif "MSE (Validation):" in line:
                mse_test = float(line.split(":")[1].strip())
                if all(v is not None for v in [r2_train, r2_test, mse_train, mse_test]):
                    metrics_data.append(
                        {
                            "Model": current_model,
                            "R² (train)": r2_train,
                            "MSE (train)": mse_train,
                            "R² (test)": r2_test,
                            "MSE (test)": mse_test,
                        }
                    )
    return metrics_data


def display_top_features(
    model: RandomForestRegressor | Lasso | SVC,
    data: pd.DataFrame,
    model_type: str,
    n_features: int = 5,
    dropout_column: str = "Dropout",
) -> str:
    """Display top features for any model type as a markdown table.

    Args:
        model: Trained model object.
        data: DataFrame with features and dropout column.
        model_type: One of 'rf', 'lasso', 'svm'.
        n_features: Number of top features to show.
        dropout_column: Name of the target column.

    Returns:
        Formatted markdown table string.
    """
    X = data.drop(dropout_column, axis=1)

    if model_type == "rf":
        importances = pd.Series(model.feature_importances_, index=X.columns)
        top = importances.iloc[importances.abs().argsort()[::-1]].head(n_features)
        result = "\n| Feature | Belang |\n|:--------|:-------|\n"
        for feature, importance in top.items():
            result += f"| {feature} | {importance:.4f} |\n"

    elif model_type == "lasso":
        coefs = pd.Series(model.coef_, index=X.columns)
        top = coefs.iloc[coefs.abs().argsort()[::-1]].head(n_features)
        result = "\n| Feature | Coefficient |\n|:--------|:------------|\n"
        for feature, coef in top.items():
            fmt = f"{coef:.2e}" if abs(coef) < 0.0001 and coef != 0 else f"{coef:.4f}"
            result += f"| {feature} | {fmt} |\n"

    elif model_type == "svm":
        top_features = get_top_svm_features(
            data, model, n_features=n_features, dropout_column=dropout_column
        )
        result = "\n| Feature | Belang |\n|:--------|:-------|\n"
        for feature, importance in top_features:
            result += f"| {feature} | {importance:.4f} |\n"

    else:
        result = f"\nOnbekend model type: {model_type}\n"

    return result

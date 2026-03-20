"""Model prediction functions for Random Forest, Lasso, and SVM."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.svm import SVC


def load_models(
    models_dir: Path = Path("models"),
) -> tuple[RandomForestRegressor, Lasso, SVC]:
    """Load all three trained models from disk.

    Args:
        models_dir: Directory containing the .joblib model files.

    Returns:
        Tuple of (rf_model, lasso_model, svm_model).
    """
    models_dir = Path(models_dir)
    rf_model = joblib.load(models_dir / "random_forest_regressor.joblib")
    lasso_model = joblib.load(models_dir / "lasso_regression.joblib")
    svm_model = joblib.load(models_dir / "support_vector_machine.joblib")
    return rf_model, lasso_model, svm_model


def _rank_predictions(
    predictions: pd.Series,
    studentnumbers: pd.DataFrame,
    studentnumber_column: str,
) -> pd.DataFrame:
    """Create a ranked DataFrame from model predictions.

    Args:
        predictions: Series of predicted dropout probabilities.
        studentnumbers: DataFrame with the student number column.
        studentnumber_column: Name of the student number column.

    Returns:
        DataFrame with ranking, student number, and prediction columns.
    """
    pred_data = pd.DataFrame({"voorspelling": predictions})
    pred_data = pd.concat([pred_data, studentnumbers.reset_index(drop=True)], axis=1)
    pred_data["ranking"] = pred_data["voorspelling"].rank(method="dense", ascending=False)
    pred_data = pred_data.sort_values(by=["voorspelling"], ascending=False).reset_index(drop=True)
    return pred_data[["ranking", studentnumber_column, "voorspelling"]]


def predict_random_forest(
    model: RandomForestRegressor,
    pred_df: pd.DataFrame,
    dropout_column: str,
    studentnumber_column: str,
) -> pd.DataFrame:
    """Generate ranked dropout predictions using a Random Forest model.

    Args:
        model: Trained Random Forest model.
        pred_df: Prediction DataFrame with features.
        dropout_column: Name of the target column (dropped if present).
        studentnumber_column: Name of the student number column.

    Returns:
        DataFrame with students ranked by predicted dropout probability.
    """
    X_pred = (
        pred_df.drop(dropout_column, axis=1).values
        if dropout_column in pred_df.columns
        else pred_df.values
    )
    studentnumbers = pred_df[[studentnumber_column]]
    predictions = model.predict(X_pred)
    return _rank_predictions(predictions, studentnumbers, studentnumber_column)


def predict_lasso(
    model: Lasso,
    pred_df_scaled: pd.DataFrame,
    pred_df_original: pd.DataFrame,
    dropout_column: str,
    studentnumber_column: str,
) -> pd.DataFrame:
    """Generate ranked dropout predictions using a Lasso model.

    Args:
        model: Trained Lasso model.
        pred_df_scaled: Scaled prediction DataFrame.
        pred_df_original: Original prediction DataFrame (for student numbers).
        dropout_column: Name of the target column (dropped if present).
        studentnumber_column: Name of the student number column.

    Returns:
        DataFrame with students ranked by predicted dropout probability.
    """
    X_pred = (
        pred_df_scaled.drop(dropout_column, axis=1).values
        if dropout_column in pred_df_scaled.columns
        else pred_df_scaled.values
    )
    studentnumbers = pred_df_original[[studentnumber_column]]
    predictions = model.predict(X_pred)
    return _rank_predictions(predictions, studentnumbers, studentnumber_column)


def predict_svm(
    model: SVC,
    pred_df_scaled: pd.DataFrame,
    pred_df_original: pd.DataFrame,
    dropout_column: str,
    studentnumber_column: str,
) -> pd.DataFrame:
    """Generate ranked dropout predictions using an SVM model.

    Args:
        model: Trained SVM model with probability estimates.
        pred_df_scaled: Scaled prediction DataFrame.
        pred_df_original: Original prediction DataFrame (for student numbers).
        dropout_column: Name of the target column (dropped if present).
        studentnumber_column: Name of the student number column.

    Returns:
        DataFrame with students ranked by predicted dropout probability.
    """
    X_pred = (
        pred_df_scaled.drop(dropout_column, axis=1).values
        if dropout_column in pred_df_scaled.columns
        else pred_df_scaled.values
    )
    studentnumbers = pred_df_original[[studentnumber_column]]
    predictions = model.predict_proba(X_pred)[:, 1]
    return _rank_predictions(predictions, studentnumbers, studentnumber_column)

"""Model training functions for Random Forest, Lasso, and SVM."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC


def train_random_forest(
    dataset_train: pd.DataFrame,
    random_seed: int,
    dropout_column: str,
    rf_parameters: dict,
    model_path: Path = Path("models/random_forest_regressor.joblib"),
) -> RandomForestRegressor:
    """Train a Random Forest regressor with grid search hyperparameter tuning.

    Args:
        dataset_train: Training DataFrame with features and target.
        random_seed: Random state for reproducibility.
        dropout_column: Name of the target column.
        rf_parameters: Parameter grid for GridSearchCV.
        model_path: Path to save the trained model.

    Returns:
        Best-fit RandomForestRegressor model.
    """
    X = dataset_train.drop(dropout_column, axis=1).values
    y = dataset_train[dropout_column].values
    rf = RandomForestRegressor(random_state=random_seed)

    grid_model = GridSearchCV(rf, rf_parameters, refit=True, n_jobs=-1, verbose=0)
    grid_model.fit(X, y)
    best_rf_model = RandomForestRegressor(**grid_model.best_params_)
    best_rf_model.fit(X, y)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_rf_model, model_path)
    return best_rf_model


def train_lasso(
    dataset_train_scaled: pd.DataFrame,
    random_seed: int,
    dropout_column: str,
    alpha_range: list[float],
    model_path: Path = Path("models/lasso_regression.joblib"),
) -> Lasso:
    """Train a Lasso regression model with grid search over alpha values.

    Args:
        dataset_train_scaled: Scaled training DataFrame with features and target.
        random_seed: Random state for reproducibility.
        dropout_column: Name of the target column.
        alpha_range: List of alpha values to search.
        model_path: Path to save the trained model.

    Returns:
        Best-fit Lasso model.
    """
    X = dataset_train_scaled.drop(dropout_column, axis=1).values
    y = dataset_train_scaled[dropout_column].values
    lasso_model = Lasso(random_state=random_seed)
    param = {"alpha": alpha_range}

    lasso_grid_search = GridSearchCV(
        lasso_model, param_grid=param, refit=False, cv=5, n_jobs=-1, verbose=0
    )
    lasso_grid_search.fit(X, y)
    best_lasso_model = Lasso(**lasso_grid_search.best_params_)
    best_lasso_model.fit(X, y)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_lasso_model, model_path)
    return best_lasso_model


def train_svm(
    dataset_train_scaled: pd.DataFrame,
    random_seed: int,
    dropout_column: str,
    svm_parameters: dict,
    model_path: Path = Path("models/support_vector_machine.joblib"),
) -> SVC:
    """Train an SVM classifier with grid search hyperparameter tuning.

    Args:
        dataset_train_scaled: Scaled training DataFrame with features and target.
        random_seed: Random state for reproducibility.
        dropout_column: Name of the target column.
        svm_parameters: Parameter grid for GridSearchCV.
        model_path: Path to save the trained model.

    Returns:
        Best-fit SVC model with probability estimates enabled.
    """
    X = dataset_train_scaled.drop(dropout_column, axis=1).values
    y = dataset_train_scaled[dropout_column].values

    svm_gridsearch = GridSearchCV(
        SVC(random_state=random_seed, probability=True),
        svm_parameters,
        refit=False,
        n_jobs=-1,
        verbose=0,
    )
    svm_gridsearch.fit(X, y)
    best_svm_model = SVC(**svm_gridsearch.best_params_, probability=True)
    best_svm_model.fit(X, y)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_svm_model, model_path)
    return best_svm_model

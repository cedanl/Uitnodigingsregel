"""Model loading for the uitnodigingsregel pipeline."""

from pathlib import Path

import joblib
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

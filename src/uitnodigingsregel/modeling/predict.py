"""Model loading for the uitnodigingsregel pipeline."""

import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.svm import SVC

MODEL_FILES = (
    "random_forest_regressor.joblib",
    "lasso_regression.joblib",
    "support_vector_machine.joblib",
)
FINGERPRINT_FILE = "training_data.json"


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
    rf_model, lasso_model, svm_model = (joblib.load(models_dir / name) for name in MODEL_FILES)
    return rf_model, lasso_model, svm_model


def compute_data_fingerprint(train_df: pd.DataFrame) -> str:
    """Compute a fingerprint of the training data.

    Args:
        train_df: Training DataFrame as read from file.

    Returns:
        Hex digest that changes when column names or cell values change.
    """
    digest = hashlib.sha256()
    digest.update("\x1f".join(map(str, train_df.columns)).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(train_df, index=False).values.tobytes())
    return digest.hexdigest()


def save_fingerprint(fingerprint: str, models_dir: Path = Path("models")) -> None:
    """Record which training data the models in models_dir were trained on.

    Args:
        fingerprint: Fingerprint from compute_data_fingerprint().
        models_dir: Directory containing the .joblib model files.
    """
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / FINGERPRINT_FILE).write_text(
        json.dumps({"fingerprint": fingerprint}), encoding="utf-8"
    )


def check_models_match_data(fingerprint: str, models_dir: Path = Path("models")) -> bool:
    """Check whether models_dir holds all models, trained on the given data.

    Args:
        fingerprint: Fingerprint from compute_data_fingerprint().
        models_dir: Directory containing the .joblib model files.

    Returns:
        True if all model files exist and were trained on data with this fingerprint.
    """
    models_dir = Path(models_dir)
    if not all((models_dir / name).exists() for name in MODEL_FILES):
        return False
    try:
        saved = json.loads((models_dir / FINGERPRINT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(saved, dict) and saved.get("fingerprint") == fingerprint

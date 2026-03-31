"""Data cleaning functions for the uitnodigingsregel pipeline."""

from pathlib import Path

import pandas as pd
from sklearn.impute import KNNImputer


def impute_missing_values(
    dataset_train: pd.DataFrame,
    dataset_pred: pd.DataFrame,
    n_neighbors: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Impute missing values using KNN, fitted on train data only.

    Fits a KNNImputer on the training set and applies it to both train and
    prediction sets, preventing data leakage from pred into train.

    Args:
        dataset_train: Training DataFrame with possible missing values.
        dataset_pred: Prediction DataFrame with possible missing values.
        n_neighbors: Number of neighbors for KNN imputation.

    Returns:
        Tuple of (train, pred) DataFrames with imputed numeric columns.
    """
    numerical_cols = dataset_train.select_dtypes(include=["number"]).columns.tolist()

    imputer = KNNImputer(n_neighbors=n_neighbors)
    imputer.fit(dataset_train[numerical_cols])

    dataset_train = dataset_train.copy()
    dataset_pred = dataset_pred.copy()
    dataset_train[numerical_cols] = imputer.transform(dataset_train[numerical_cols])
    dataset_pred[numerical_cols] = imputer.transform(dataset_pred[numerical_cols])

    return dataset_train, dataset_pred


def remove_single_value_columns(
    dataset_train: pd.DataFrame,
    dataset_pred: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove columns where all rows in the training set have the same value.

    Args:
        dataset_train: Training DataFrame.
        dataset_pred: Prediction DataFrame.

    Returns:
        Tuple of (train, pred) DataFrames with constant columns removed.
    """
    single_value_columns = [
        col for col in dataset_train.columns if dataset_train[col].nunique() == 1
    ]
    dataset_train = dataset_train.drop(columns=single_value_columns, errors="ignore")
    dataset_pred = dataset_pred.drop(columns=single_value_columns, errors="ignore")
    return dataset_train, dataset_pred


def detect_separator(
    file_path: str | Path,
    target_column: str = "Dropout",
) -> str:
    """Detect the CSV separator by trying common delimiters.

    Reads the first 5 rows with each candidate separator and returns the
    first one that produces multiple columns containing the target column.

    Args:
        file_path: Path to the CSV file.
        target_column: Expected column name used to validate the separator.

    Returns:
        Detected separator character, defaults to ',' if none matched.
    """
    separators = [",", "\t", ";", "|"]
    for sep in separators:
        try:
            df_sample = pd.read_csv(file_path, sep=sep, nrows=5, engine="python")
            if len(df_sample.columns) > 1 and target_column in df_sample.columns:
                return sep
        except (pd.errors.ParserError, pd.errors.EmptyDataError):
            continue
    return ","

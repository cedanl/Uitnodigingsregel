"""Data cleaning functions for the uitnodigingsregel pipeline."""

from pathlib import Path

import pandas as pd


def clean_data(dataset: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate rows and fill NA values with column means for numeric columns.

    Args:
        dataset: Raw input DataFrame.

    Returns:
        Cleaned DataFrame with no duplicates and imputed numeric NAs.
    """
    dataset_no_dups = dataset.drop_duplicates()
    numerical_cols = dataset_no_dups.select_dtypes(include=["number"])
    dataset_no_dups.loc[:, numerical_cols.columns] = numerical_cols.fillna(numerical_cols.mean())
    return dataset_no_dups


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

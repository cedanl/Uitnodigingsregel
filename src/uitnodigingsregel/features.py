"""Feature engineering functions: dummy encoding and standardization."""

from pathlib import Path

import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def convert_categorical_to_dummies(
    train_dataset: pd.DataFrame,
    predict_dataset: pd.DataFrame,
    dropout_column: str,
    output_dir: Path = Path("data/03-output"),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One-hot encode categorical columns and align train/predict DataFrames.

    Creates dummy variables for all categorical columns, drops the first level
    to prevent multicollinearity, and aligns both DataFrames on columns.

    Args:
        train_dataset: Training DataFrame.
        predict_dataset: Prediction DataFrame.
        dropout_column: Name of the target column.
        output_dir: Directory to write processed CSV output.

    Returns:
        Tuple of (train, pred) DataFrames with dummy-encoded categoricals.
    """
    categorical_cols = train_dataset.select_dtypes(include=["category", "object"]).columns
    if len(categorical_cols) > 0:
        train_dataset = pd.get_dummies(
            train_dataset, columns=categorical_cols, drop_first=True, dummy_na=True
        )
        predict_dataset = pd.get_dummies(
            predict_dataset, columns=categorical_cols, drop_first=True, dummy_na=True
        )
        train_dataset, predict_dataset = train_dataset.align(
            predict_dataset, join="outer", axis=1, fill_value=0
        )
        dummy_cols = [
            col
            for col in train_dataset.columns
            if any(col.startswith(cat_col) for cat_col in categorical_cols)
        ]
        train_dataset[dummy_cols] = train_dataset[dummy_cols].astype(int)
        predict_dataset[dummy_cols] = predict_dataset[dummy_cols].astype(int)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    train_dataset.to_parquet(output_dir / "train_processed.parquet")
    predict_dataset.to_parquet(output_dir / "pred_processed.parquet")
    train_dataset.to_csv(output_dir / "train_processed.csv", sep=";", index=False)
    predict_dataset.to_csv(output_dir / "pred_processed.csv", sep=";", index=False)
    return train_dataset, predict_dataset


def standardize_dataset(
    dataset_train: pd.DataFrame,
    dataset_pred: pd.DataFrame,
    dropout_column: str,
    output_dir: Path = Path("data/02-prepared"),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Min-max scale both datasets, preserving the dropout column.

    Args:
        dataset_train: Training DataFrame (with dropout column).
        dataset_pred: Prediction DataFrame (with dropout column).
        dropout_column: Name of the target column (excluded from scaling).
        output_dir: Directory to write standardized Parquet and CSV output.

    Returns:
        Tuple of (train, pred) DataFrames with scaled features.
    """
    dropout_train = dataset_train[dropout_column]
    dropout_pred = dataset_pred[dropout_column]
    dataset_train = dataset_train.drop(columns=[dropout_column])
    dataset_pred = dataset_pred.drop(columns=[dropout_column])

    column_names_train = dataset_train.columns.tolist()
    column_names_pred = dataset_pred.columns.tolist()
    scaler = MinMaxScaler().fit(dataset_train)
    train_scaled_data = scaler.transform(dataset_train)
    pred_scaled_data = scaler.transform(dataset_pred)
    train_df_scaled = pd.DataFrame(train_scaled_data, columns=column_names_train)
    pred_df_scaled = pd.DataFrame(pred_scaled_data, columns=column_names_pred)

    train_df_scaled[dropout_column] = dropout_train.values
    pred_df_scaled[dropout_column] = dropout_pred.values

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    train_df_scaled.to_parquet(output_dir / "train_data_standardized.parquet")
    pred_df_scaled.to_parquet(output_dir / "pred_data_standardized.parquet")
    train_df_scaled.to_csv(output_dir / "train_data_standardized.csv", sep=";", index=False)
    pred_df_scaled.to_csv(output_dir / "pred_data_standardized.csv", sep=";", index=False)
    return train_df_scaled, pred_df_scaled

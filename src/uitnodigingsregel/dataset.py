"""Data loading and validation functions for the uitnodigingsregel pipeline."""

import io
from pathlib import Path
from typing import IO

import pandas as pd

MAX_LISTED_COLUMNS = 5


class DataValidationError(ValueError):
    """Input data cannot be used; the message is written for the end user."""


def detect_separator(
    file_path: str | Path | IO[str],
    target_column: str = "Dropout",
) -> str:
    """Detect the CSV separator by trying common delimiters.

    Reads the first 5 rows with each candidate separator and returns the
    first one that produces multiple columns containing the target column.

    Args:
        file_path: Path to the CSV file, or an open text buffer.
        target_column: Expected column name used to validate the separator.

    Returns:
        Detected separator character, defaults to ',' if none matched.
    """
    separators = [",", "\t", ";", "|"]
    for sep in separators:
        if not isinstance(file_path, (str, Path)):
            file_path.seek(0)
        try:
            df_sample = pd.read_csv(file_path, sep=sep, nrows=5, engine="python")
            if len(df_sample.columns) > 1 and target_column in df_sample.columns:
                return sep
        except (pd.errors.ParserError, pd.errors.EmptyDataError):
            continue
    return ","


def read_student_data(source: str | Path | bytes, id_column: str = "Studentnummer") -> pd.DataFrame:
    """Read a student CSV file, whatever its separator or decimal sign.

    Args:
        source: Path to the CSV file, or its raw content (e.g. from an upload).
        id_column: Column present in every student file, used to find the separator.

    Returns:
        DataFrame with decimal-comma text columns converted to numbers.

    Raises:
        DataValidationError: If the file is empty.
    """
    raw = source if isinstance(source, bytes) else Path(source).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")

    buffer = io.StringIO(text)
    separator = detect_separator(buffer, id_column)
    buffer.seek(0)
    try:
        df = pd.read_csv(buffer, sep=separator, engine="python")
    except pd.errors.EmptyDataError as e:
        raise DataValidationError("Het bestand is leeg.") from e

    if separator != ",":
        df = convert_decimal_commas(df)
    return df


def convert_decimal_commas(df: pd.DataFrame) -> pd.DataFrame:
    """Convert text columns that hold numbers with a decimal comma to numeric.

    Args:
        df: DataFrame as read from file.

    Returns:
        DataFrame where each text column whose values are all numbers is numeric.
    """
    df = df.copy()
    for column in df.select_dtypes(include=["object", "string"]).columns:
        values = df[column].dropna()
        if values.empty:
            continue
        converted = pd.to_numeric(
            values.astype(str).str.replace(",", ".", regex=False), errors="coerce"
        )
        if converted.notna().all():
            df[column] = pd.to_numeric(
                df[column].astype("string").str.replace(",", ".", regex=False), errors="coerce"
            )
    return df


def validate_student_data(
    train_df: pd.DataFrame,
    pred_df: pd.DataFrame,
    target_column: str = "Dropout",
    id_column: str = "Studentnummer",
) -> None:
    """Check that training and prediction data can be used by the pipeline.

    Args:
        train_df: Training DataFrame.
        pred_df: Prediction DataFrame.
        target_column: Name of the dropout column.
        id_column: Name of the student number column.

    Raises:
        DataValidationError: With a Dutch message that names the problem and the columns.
    """
    for label, df in (("trainingsdata", train_df), ("predictiedata", pred_df)):
        if df.empty:
            raise DataValidationError(f"De {label} bevat geen rijen.")
        missing = [c for c in (id_column, target_column) if c not in df.columns]
        if missing:
            raise DataValidationError(
                f"In de {label} ontbreekt de kolom {_list_columns(missing)}. "
                f"Gevonden kolommen: {_list_columns(df.columns)}. "
                "Staat alles in één kolom, dan gebruikt het bestand een scheidingsteken "
                "dat niet herkend wordt. Gebruik tab, puntkomma of komma."
            )

    target_values = set(train_df[target_column].dropna().unique())
    if train_df[target_column].isna().any() or not target_values <= {0, 1}:
        raise DataValidationError(
            f"De kolom '{target_column}' in de trainingsdata mag alleen 0 en 1 bevatten, "
            "zonder lege cellen."
        )
    if len(target_values) < 2:
        raise DataValidationError(
            f"De kolom '{target_column}' in de trainingsdata bevat alleen de waarde "
            f"{_list_columns(target_values)}. Het model heeft zowel uitvallers (1) als "
            "niet-uitvallers (0) nodig."
        )

    only_train = [c for c in train_df.columns if c not in pred_df.columns]
    only_pred = [c for c in pred_df.columns if c not in train_df.columns]
    if only_train or only_pred:
        parts = []
        if only_train:
            parts.append(f"ontbreekt in de predictiedata: {_list_columns(only_train)}")
        if only_pred:
            parts.append(f"ontbreekt in de trainingsdata: {_list_columns(only_pred)}")
        raise DataValidationError(
            "Trainings- en predictiedata moeten dezelfde kolommen hebben. " + "; ".join(parts) + "."
        )

    features = train_df.drop(columns=[id_column, target_column])
    if features.select_dtypes(include=["number"]).empty:
        raise DataValidationError(
            "De trainingsdata bevat geen kolommen met getallen naast "
            f"'{id_column}' en '{target_column}'. Controleer of getallen als getal zijn "
            "opgeslagen."
        )


def load_student_data(
    train_source: str | Path | bytes,
    pred_source: str | Path | bytes,
    target_column: str = "Dropout",
    id_column: str = "Studentnummer",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read, complete and validate the training and prediction data.

    The outcome is not yet known for students in the prediction data, so a
    missing target column is added there with value 0.

    Args:
        train_source: Path or raw content of the training CSV.
        pred_source: Path or raw content of the prediction CSV.
        target_column: Name of the dropout column.
        id_column: Name of the student number column.

    Returns:
        Tuple of (train_df, pred_df) without duplicate rows.

    Raises:
        DataValidationError: If the data cannot be used by the pipeline.
    """
    train_df = read_student_data(train_source, id_column).drop_duplicates().reset_index(drop=True)
    pred_df = read_student_data(pred_source, id_column).drop_duplicates().reset_index(drop=True)

    if target_column in train_df.columns and target_column not in pred_df.columns:
        pred_df.insert(train_df.columns.get_loc(target_column), target_column, 0)

    validate_student_data(train_df, pred_df, target_column, id_column)
    return train_df, pred_df


def _list_columns(columns: object) -> str:
    names = [f"'{c}'" for c in columns]
    listed = ", ".join(names[:MAX_LISTED_COLUMNS])
    extra = len(names) - MAX_LISTED_COLUMNS
    return f"{listed} en {extra} andere" if extra > 0 else listed

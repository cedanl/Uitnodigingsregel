"""Data cleaning functions for the uitnodigingsregel pipeline."""

from pathlib import Path

import pandas as pd


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

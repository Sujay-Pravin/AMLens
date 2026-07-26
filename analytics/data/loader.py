"""
Dataset loading utilities for the Analytics SDK.

Responsibilities:
- Load supported dataset formats.
- Return a raw pandas DataFrame.
- Validate file existence and supported extensions.

This module intentionally performs NO preprocessing,
schema validation, or feature engineering.
"""

from pathlib import Path
from typing import Union

import pandas as pd

from analytics.config import SUPPORTED_FILE_TYPES


class DataLoader:
    """
    Loads AML datasets into pandas DataFrames.
    """

    @staticmethod
    def load(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load a dataset from disk.

        Parameters
        ----------
        file_path : str | Path
            Path to the dataset.

        Returns
        -------
        pd.DataFrame
            Raw dataset.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.

        ValueError
            If the file type is unsupported.
        """

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")

        if file_path.suffix.lower() not in SUPPORTED_FILE_TYPES:
            raise ValueError(
                f"Unsupported dataset format '{file_path.suffix}'. "
                f"Supported formats: {SUPPORTED_FILE_TYPES}"
            )

        if file_path.suffix.lower() == ".csv":
            return pd.read_csv(
                file_path,
                low_memory=False,
            )

        if file_path.suffix.lower() == ".parquet":
            return pd.read_parquet(file_path)

        raise RuntimeError("Unexpected loader failure.")
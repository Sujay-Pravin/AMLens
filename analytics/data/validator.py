"""
Dataset validation utilities.

Checks whether a dataset conforms to the expected schema.
"""

from dataclasses import dataclass
from typing import List

import pandas as pd

from analytics.data.schemas import REQUIRED_COLUMNS


@dataclass
class ValidationReport:
    valid: bool
    total_rows: int
    total_columns: int
    missing_columns: List[str]
    duplicate_rows: int
    missing_values: dict


class DataValidator:
    """
    Validates AML datasets.
    """

    @staticmethod
    def validate(df: pd.DataFrame) -> ValidationReport:
        """
        Validate the input dataframe.

        Parameters
        ----------
        df : pd.DataFrame

        Returns
        -------
        ValidationReport
        """

        missing_columns = sorted(
            REQUIRED_COLUMNS.difference(df.columns)
        )

        duplicate_rows = int(df.duplicated().sum())

        missing_values = (
            df.isnull()
            .sum()
            .loc[lambda x: x > 0]
            .to_dict()
        )

        return ValidationReport(
            valid=len(missing_columns) == 0,
            total_rows=len(df),
            total_columns=len(df.columns),
            missing_columns=missing_columns,
            duplicate_rows=duplicate_rows,
            missing_values=missing_values,
        )
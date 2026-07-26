"""
Dataset preprocessing utilities.

Responsibilities:
- Normalize column names
- Convert timestamps
- Convert data types
- Remove duplicate rows
- Sort chronologically
"""

from __future__ import annotations

import pandas as pd

from analytics.data.schemas import COLUMN_RENAMES


class DataPreprocessor:
    """
    Handles preprocessing of AML datasets.
    """

    @staticmethod
    def preprocess(df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the input dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            Raw dataframe.

        Returns
        -------
        pd.DataFrame
            Clean dataframe.
        """

        df = df.copy()

        # -------------------------------
        # Rename columns
        # -------------------------------
        df.rename(columns=COLUMN_RENAMES, inplace=True)

        # -------------------------------
        # Timestamp
        # -------------------------------
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        # -------------------------------
        # Numeric columns
        # -------------------------------
        numeric_columns = [
            "from_bank",
            "to_bank",
            "amount_received",
            "amount_paid",
            "is_laundering",
        ]

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # -------------------------------
        # String columns
        # -------------------------------
        string_columns = [
            "from_account",
            "to_account",
            "receiving_currency",
            "payment_currency",
            "payment_format",
            "sender_bank_name",
            "receiver_bank_name",
            "sender_entity_id",
            "receiver_entity_id",
            "sender_entity_name",
            "receiver_entity_name",
            "source_set",
        ]

        for column in string_columns:
            if column in df.columns:
                df[column] = (
                    df[column]
                    .astype("string")
                    .str.strip()
                )

        # -------------------------------
        # Remove duplicate rows
        # -------------------------------
        df.drop_duplicates(inplace=True)

        # -------------------------------
        # Sort chronologically
        # -------------------------------
        df.sort_values(
            by="timestamp",
            inplace=True,
            ignore_index=True
        )

        return df
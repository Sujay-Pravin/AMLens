from typing import Any, Dict

import pandas as pd

from analytics.interfaces import EDAResult


class EDAAnalyzer:
    """
    Performs exploratory data analysis on the processed AML dataset.
    """

    @staticmethod
    def analyze(df: pd.DataFrame) -> EDAResult:
        """
        Compute dataset statistics.

        Parameters
        ----------
        df : pd.DataFrame
            Preprocessed AML dataset.

        Returns
        -------
        EDAResult
        """
        metrics = {
            "payment_formats": df["payment_format"].value_counts().to_dict(),
            "payment_currencies": df["payment_currency"].value_counts().to_dict(),
            "receiving_currencies": df["receiving_currency"].value_counts().to_dict(),
            "top_sender_banks": df["from_bank"].value_counts().head(10).to_dict(),
            "top_receiver_banks": df["to_bank"].value_counts().head(10).to_dict(),
        }

        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_summary": df.describe(include="number").to_dict(),
            "categorical_summary": df.describe(
                include=["object", "string", "category"]
        ).to_dict(),
        }

        missing_values = (
            df.isnull()
            .sum()
            .to_dict()
        )

        class_distribution = (
            df["is_laundering"]
            .value_counts()
            .to_dict()
        )

        return EDAResult(
            summary=summary,
            missing_values=missing_values,
            class_distribution=class_distribution,
            metrics=metrics,
            plots=[],
        )
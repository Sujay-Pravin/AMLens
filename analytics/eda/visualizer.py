from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analytics.interfaces import EDAResult


class EDAVisualizer:
    """
    Generates plots for EDA.
    """

    OUTPUT_DIR = Path("outputs/plots")

    @classmethod
    def create_all(cls, df: pd.DataFrame, eda: EDAResult) -> None:
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        cls.class_distribution(eda)
        cls.amount_distribution(df)
        cls.payment_formats(eda)

    @classmethod
    def class_distribution(cls, eda: EDAResult):
        plt.figure(figsize=(6, 4))
        plt.bar(
            list(eda.class_distribution.keys()),
            list(eda.class_distribution.values()),
        )
        plt.title("Class Distribution")
        plt.xlabel("Is Laundering")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(cls.OUTPUT_DIR / "class_distribution.png")
        plt.close()

    @classmethod
    def amount_distribution(cls, df: pd.DataFrame):
        plt.figure(figsize=(8, 5))
        plt.hist(df["amount_paid"], bins=50)
        plt.title("Amount Paid Distribution")
        plt.xlabel("Amount")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(cls.OUTPUT_DIR / "amount_distribution.png")
        plt.close()

    @classmethod
    def payment_formats(cls, eda: EDAResult):
        plt.figure(figsize=(8, 5))
        plt.bar(
            eda.metrics["payment_formats"].keys(),
            eda.metrics["payment_formats"].values(),
        )
        plt.xticks(rotation=45)
        plt.title("Payment Formats")
        plt.tight_layout()
        plt.savefig(cls.OUTPUT_DIR / "payment_formats.png")
        plt.close()
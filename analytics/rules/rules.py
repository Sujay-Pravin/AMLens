from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass(frozen=True)
class Rule:
    """
    Represents a single AML rule.
    """

    name: str
    description: str
    risk_points: int
    condition: Callable[[pd.Series], bool]


# -----------------------------
# Thresholds
# -----------------------------

HIGH_VALUE_THRESHOLD = 50_000
SENDER_TX_1D_THRESHOLD = 20
SENDER_TX_7D_THRESHOLD = 100
RECEIVER_TX_7D_THRESHOLD = 100
UNIQUE_RECEIVERS_THRESHOLD = 25
Z_SCORE_THRESHOLD = 3.0
AMOUNT_DIFF_THRESHOLD = 5_000


# -----------------------------
# Rules
# -----------------------------

HIGH_VALUE_RULE = Rule(
    name="High Value Transaction",
    description="Transaction amount exceeds threshold.",
    risk_points=20,
    condition=lambda row: row["high_value_trans"] == 1,
)

NIGHT_TRANSACTION_RULE = Rule(
    name="Night Transaction",
    description="Transaction occurred during night hours.",
    risk_points=8,
    condition=lambda row: row["is_night_time"] == 1,
)

HIGH_SENDER_VELOCITY_1D_RULE = Rule(
    name="High Sender Velocity (1 Day)",
    description="Large number of outgoing transactions in one day.",
    risk_points=15,
    condition=lambda row: row["sender_tx_count_1d"] >= SENDER_TX_1D_THRESHOLD,
)

HIGH_SENDER_VELOCITY_7D_RULE = Rule(
    name="High Sender Velocity (7 Days)",
    description="Large number of outgoing transactions in seven days.",
    risk_points=10,
    condition=lambda row: row["sender_tx_count_7d"] >= SENDER_TX_7D_THRESHOLD,
)

HIGH_RECEIVER_VELOCITY_RULE = Rule(
    name="High Receiver Velocity",
    description="Receiver has unusually high incoming activity.",
    risk_points=10,
    condition=lambda row: row["receiver_tx_count_7d"] >= RECEIVER_TX_7D_THRESHOLD,
)

AMOUNT_SPIKE_RULE = Rule(
    name="Amount Spike",
    description="Transaction amount deviates significantly from sender history.",
    risk_points=15,
    condition=lambda row: abs(row["amount_zscore_prior_5"]) >= Z_SCORE_THRESHOLD,
)

MANY_RECEIVERS_RULE = Rule(
    name="Many Unique Receivers",
    description="Sender transacts with many unique receivers.",
    risk_points=10,
    condition=lambda row: (
        row["sender_unique_receivers_30d"]
        >= UNIQUE_RECEIVERS_THRESHOLD
    ),
)

CROSS_BANK_RULE = Rule(
    name="Cross Bank Transfer",
    description="Funds moved between different banks.",
    risk_points=5,
    condition=lambda row: row["same_bank"] == 0,
)

CURRENCY_SWITCH_RULE = Rule(
    name="Currency Switch",
    description="Payment and receiving currencies differ.",
    risk_points=8,
    condition=lambda row: row["same_currency"] == 0,
)

ROUND_AMOUNT_RULE = Rule(
    name="Round Amount",
    description="Transaction uses round-number amounts.",
    risk_points=5,
    condition=lambda row: row["is_round_amount"] == 1,
)

AMOUNT_DIFFERENCE_RULE = Rule(
    name="Large Amount Difference",
    description="Large discrepancy between paid and received amounts.",
    risk_points=8,
    condition=lambda row: row["amount_diff"] >= AMOUNT_DIFF_THRESHOLD,
)

RULES = [
    HIGH_VALUE_RULE,
    NIGHT_TRANSACTION_RULE,
    HIGH_SENDER_VELOCITY_1D_RULE,
    HIGH_SENDER_VELOCITY_7D_RULE,
    HIGH_RECEIVER_VELOCITY_RULE,
    AMOUNT_SPIKE_RULE,
    MANY_RECEIVERS_RULE,
    CROSS_BANK_RULE,
    CURRENCY_SWITCH_RULE,
    ROUND_AMOUNT_RULE,
    AMOUNT_DIFFERENCE_RULE,
]
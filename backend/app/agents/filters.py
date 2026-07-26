"""
Dataset Filtering — applies parsed query entities to the engineered
dataframe BEFORE any analytics tool runs, so the planner's selected tools
operate on the narrowed dataset the user actually asked about (e.g. one
customer, one date range) rather than the whole file.

Filtering happens after feature engineering (not before) because several
engineered features (velocity, rolling stats) depend on each sender's full
transaction history — narrowing the dataframe first would corrupt them.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.logging import get_logger

logger = get_logger(__name__)


def apply_filters(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    """Narrow `df` by whichever filters are present and non-null.

    Supported keys: customer_id, account_id, date_from, date_to,
    amount_min, amount_max, bank. `country` has no corresponding column in
    this dataset's schema and is intentionally not applied.
    """
    if not filters:
        return df

    mask = pd.Series(True, index=df.index)

    customer_id = filters.get("customer_id")
    if customer_id and "sender_entity_id" in df.columns and "receiver_entity_id" in df.columns:
        mask &= (df["sender_entity_id"] == customer_id) | (df["receiver_entity_id"] == customer_id)

    account_id = filters.get("account_id")
    if account_id and "from_account" in df.columns and "to_account" in df.columns:
        mask &= (df["from_account"] == account_id) | (df["to_account"] == account_id)

    date_from = filters.get("date_from")
    if date_from and "timestamp" in df.columns:
        mask &= df["timestamp"] >= pd.Timestamp(date_from)

    date_to = filters.get("date_to")
    if date_to and "timestamp" in df.columns:
        mask &= df["timestamp"] <= pd.Timestamp(date_to)

    amount_min = filters.get("amount_min")
    if amount_min is not None and "amount_paid" in df.columns:
        mask &= df["amount_paid"] >= amount_min

    amount_max = filters.get("amount_max")
    if amount_max is not None and "amount_paid" in df.columns:
        mask &= df["amount_paid"] <= amount_max

    bank = filters.get("bank")
    bank_columns = [
        c for c in ("sender_bank_name", "receiver_bank_name") if c in df.columns
    ]
    if bank and bank_columns:
        bank_mask = pd.Series(False, index=df.index)
        for column in bank_columns:
            bank_mask |= df[column].astype("string").str.contains(bank, case=False, na=False)
        mask &= bank_mask

    filtered = df[mask]
    if len(filtered) != len(df):
        logger.info(f"[Filters] Narrowed {len(df)} rows to {len(filtered)} rows using {filters}")

    return filtered

import bisect
from collections import defaultdict, deque
import numpy as np
import pandas as pd

from analytics.interfaces import FeatureResult


class FeatureEngineer:
    """
    Generates behavioral and transaction-level features for AML detection.
    """

    @staticmethod
    def engineer(df: pd.DataFrame) -> FeatureResult:

        features = df.copy()

        n = len(features)

        senders = features["sender_entity_id"].values
        receivers = features["receiver_entity_id"].values
        amounts_paid = features["amount_paid"].values.astype(np.float32)
        amounts_received = features["amount_received"].values.astype(np.float32)
        timestamps = features["timestamp"].tolist()

        time_since_prev = np.full(n, -1.0, dtype=np.float32)
        sender_tx_count_1d = np.zeros(n, dtype=np.int32)
        sender_tx_count_7d = np.zeros(n, dtype=np.int32)
        receiver_tx_count_7d = np.zeros(n, dtype=np.int32)

        rolling_amount_mean_5 = np.zeros(n, dtype=np.float32)
        rolling_amount_std_5 = np.zeros(n, dtype=np.float32)

        sender_unique_receivers_30d = np.zeros(n, dtype=np.int32)
        sender_times = {}
        sender_prev_ts = {}

        sender_tx_times = defaultdict(list)
        receiver_tx_times = defaultdict(list)

        sender_recent_amounts = defaultdict(list)
        sender_receiver_windows = defaultdict(deque)

        delta_day = pd.Timedelta(days=1)
        delta_week = pd.Timedelta(days=7)
        delta_30d = pd.Timedelta(days=30)

        for i in range(n):
            s = senders[i]
            r = receivers[i]
            amt = amounts_paid[i]
            ts = timestamps[i]

            # Time since previous transaction
            if s in sender_prev_ts:
                time_since_prev[i] = (
                    ts - sender_prev_ts[s]
                ).total_seconds()

            sender_prev_ts[s] = ts

            # Sender velocity
            sender_history = sender_tx_times[s]

            idx_day = bisect.bisect_left(
                sender_history,
                ts - delta_day,
            )

            idx_week = bisect.bisect_left(
                sender_history,
                ts - delta_week,
            )

            sender_tx_count_1d[i] = len(sender_history) - idx_day
            sender_tx_count_7d[i] = len(sender_history) - idx_week

            # Receiver velocity
            receiver_history = receiver_tx_times[r]

            idx_receiver_week = bisect.bisect_left(
                receiver_history,
                ts - delta_week,
            )

            receiver_tx_count_7d[i] = (
                len(receiver_history)
                - idx_receiver_week
            )

            # Rolling amount history
            previous_amounts = sender_recent_amounts[s]

            if previous_amounts:
                rolling_amount_mean_5[i] = float(
                    np.mean(previous_amounts)
                )
                rolling_amount_std_5[i] = float(
                    np.std(previous_amounts, ddof=0)
                )
            else:
                rolling_amount_mean_5[i] = 0.0
                rolling_amount_std_5[i] = 0.0

            # Unique receivers (30d)
            receiver_window = sender_receiver_windows[s]

            while (
                receiver_window
                and receiver_window[0][0] < ts - delta_30d
            ):
                receiver_window.popleft()

            sender_unique_receivers_30d[i] = len(
                {
                    receiver
                    for _, receiver in receiver_window
                }
            )

            # Update histories AFTER feature computation
            sender_history.append(ts)
            receiver_history.append(ts)

            previous_amounts.append(amt)

            if len(previous_amounts) > 5:
                previous_amounts.pop(0)

            receiver_window.append((ts, r))



        # ---------- Save Features ----------

        features["time_since_prev_tx"] = time_since_prev
        features["sender_tx_count_1d"] = sender_tx_count_1d
        features["sender_tx_count_7d"] = sender_tx_count_7d
        features["receiver_tx_count_7d"] = receiver_tx_count_7d

        features["rolling_amount_mean_5"] = rolling_amount_mean_5
        features["rolling_amount_std_5"] = rolling_amount_std_5

        features["sender_unique_receivers_30d"] = (
            sender_unique_receivers_30d
        )

        features["amount_zscore_prior_5"] = (
            (
                features["amount_paid"]
                - features["rolling_amount_mean_5"]
            )
            / (
                features["rolling_amount_std_5"]
                + 1e-5
            )
        ).astype(np.float32)

        features["same_currency"] = (
            features["receiving_currency"]
            == features["payment_currency"]
        ).astype(np.int8)

        features["same_bank"] = (
            features["from_bank"]
            == features["to_bank"]
        ).astype(np.int8)
        features["is_round_amount"] = (
            (amounts_received % 1 == 0)
            & (amounts_paid % 1 == 0)
        ).astype(np.int8)

        features["hour"] = (
            features["timestamp"]
            .dt.hour
            .astype(np.int8)
        )

        features["day_of_week"] = (
            features["timestamp"]
            .dt.dayofweek
            .astype(np.int8)
        )

        features["is_weekend"] = (
            features["day_of_week"]
            .isin([5, 6])
        ).astype(np.int8)

        features["is_night_time"] = (
            (features["hour"] >= 22)
            | (features["hour"] <= 6)
        ).astype(np.int8)

        features["high_value_trans"] = (
            features["amount_paid"] > 50000
        ).astype(np.int8)

        features["amount_diff"] = np.abs(
            amounts_received - amounts_paid
        ).astype(np.float32)

        engineered = [
            "time_since_prev_tx",
            "sender_tx_count_1d",
            "sender_tx_count_7d",
            "receiver_tx_count_7d",
            "rolling_amount_mean_5",
            "rolling_amount_std_5",
            "sender_unique_receivers_30d",
            "amount_zscore_prior_5",
            "same_currency",
            "same_bank",
            "is_round_amount",
            "hour",
            "day_of_week",
            "is_weekend",
            "is_night_time",
            "high_value_trans",
            "amount_diff",
        ]

        return FeatureResult(
            dataframe=features,
            feature_names=engineered,
        )
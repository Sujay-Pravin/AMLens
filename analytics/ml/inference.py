import numpy as np
import joblib
import pandas as pd
import shap

from analytics.config import MODEL_DIR
from .schemas import FeatureContribution, MLResult

# Columns that must never reach the model (bias / leakage risk).
BIAS_COLUMNS = ["payment_format", "Payment Format"]

# Snake_case -> title-case rename required because the trained pipeline's
# ColumnTransformer was fit on the raw (un-renamed) column names.
MODEL_COLUMN_RENAMES = {
    "amount_received": "Amount Received",
    "amount_paid": "Amount Paid",
    "receiving_currency": "Receiving Currency",
    "payment_currency": "Payment Currency",
}


def extract_pos_class_shap(sv, is_single_sample=False):
    if isinstance(sv, list):
        if is_single_sample:
            return sv[1][0]
        else:
            return sv[1]

    elif isinstance(sv, np.ndarray):
        if sv.ndim == 3:
            if sv.shape[-1] == 2:
                return sv[0, :, 1] if is_single_sample else sv[:, :, 1]
            elif sv.shape[0] == 2:
                return sv[1, 0, :] if is_single_sample else sv[1, :, :]

        elif sv.ndim == 2:
            return sv[0] if is_single_sample else sv

    return sv


class AMLInference:
    """
    Handles inference using the trained AML model.
    """

    def __init__(self, model_path=None):

        if model_path is None:
            model_path = MODEL_DIR / "xgboost_model.joblib"

        self.pipeline = joblib.load(model_path)

        self.preprocessor = self.pipeline.named_steps["preprocessor"]
        self.classifier = self.pipeline.named_steps["classifier"]

        self.feature_names = self.preprocessor.get_feature_names_out()

        self.explainer = shap.TreeExplainer(
            self.classifier,
            feature_perturbation="tree_path_dependent"
        )

    @staticmethod
    def _prepare_for_model(features: pd.DataFrame) -> pd.DataFrame:
        """
        Adapt engineered features to what the trained pipeline expects:
        drop bias-risk columns and rename columns back to the raw
        (title-case) names the ColumnTransformer was fit on.
        """

        prepared = features.drop(
            columns=[c for c in BIAS_COLUMNS if c in features.columns]
        )

        renames = {
            src: dst
            for src, dst in MODEL_COLUMN_RENAMES.items()
            if src in prepared.columns
        }

        return prepared.rename(columns=renames)

    def predict(self, features: pd.DataFrame) -> MLResult:
        """
        Predict fraud probability for engineered features.

        Parameters
        ----------
        features : pd.DataFrame
            DataFrame after preprocessing + feature engineering.

        Returns
        -------
        MLResult
        """

        prepared = self._prepare_for_model(features)

        probability = float(self.pipeline.predict_proba(prepared)[0][1])
        prediction = int(self.pipeline.predict(prepared)[0])

        processed = self.preprocessor.transform(prepared)
        if hasattr(processed, "toarray"):
            processed = processed.toarray()
        processed_row = np.asarray(processed)[0]

        local_values = self.explainer.shap_values(processed)
        local_values = extract_pos_class_shap(
            local_values,
            is_single_sample=True
        )

        shap_dict = {
            feature: float(value)
            for feature, value in zip(self.feature_names, local_values)
        }

        sorted_feats = sorted(
            zip(self.feature_names, processed_row, local_values),
            key=lambda x: abs(x[2]),
            reverse=True
        )

        positive = []
        for feature, value, impact in sorted_feats:
            if impact > 0:
                positive.append(
                    FeatureContribution(
                        feature=feature,
                        value=float(value),
                        impact=float(impact)
                    )
                )
            if len(positive) == 5:
                break

        negative = []
        for feature, value, impact in sorted_feats:
            if impact < 0:
                negative.append(
                    FeatureContribution(
                        feature=feature,
                        value=float(value),
                        impact=float(impact)
                    )
                )
            if len(negative) == 5:
                break

        return MLResult(
            prediction=prediction,
            probability=probability,
            confidence=probability,
            shap_values=shap_dict,
            top_positive_features=positive,
            top_negative_features=negative
        )

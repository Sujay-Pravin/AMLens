from analytics.data.loader import DataLoader
from analytics.data.validator import DataValidator
from analytics.data.preprocess import DataPreprocessor
from analytics.features.engineer import FeatureEngineer
from analytics.rules.engine import RuleEngine
from analytics.ml.inference import AMLInference
from analytics.fusion.engine import RiskFusion
from analytics.graph.engine import GraphAnalyzer

raw = DataLoader.load("../dataset/sample.csv")

validation_report = DataValidator.validate(raw)
print(validation_report)

clean = DataPreprocessor.preprocess(raw)

feature_result = FeatureEngineer.engineer(clean)
features = feature_result.dataframe

row = features.iloc[0]
rule_result = RuleEngine.evaluate_transaction(row)
print(rule_result)

ml = AMLInference()
ml_result = ml.predict(features.iloc[[0]])
print(ml_result)

risk_assessment = RiskFusion.fuse(rule_result, ml_result)
print(risk_assessment)

graph_metrics = GraphAnalyzer.analyze(features)
print(graph_metrics)

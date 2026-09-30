from dataclasses import dataclass
from .normalize import normalize_transactions
from .graph import build_transaction_graph
from .features import extract_features
from .anomaly import anomaly_scores
from .entities import cluster_entities,mixing_indicators
from .risk import score_risk,ranked_alerts

@dataclass
class AnalysisResult:
    transactions: object; graph: object; features: object; entities: object; risk: object; alerts: object

class AnalyticsPipeline:
    def run(self,source,contamination=.08):
        tx=normalize_transactions(source); graph=build_transaction_graph(tx); feat=anomaly_scores(extract_features(tx,graph),contamination); entities=cluster_entities(graph); risk=score_risk(feat,mixing_indicators(tx,graph)).merge(entities,on="address",how="left"); return AnalysisResult(tx,graph,feat,entities,risk,ranked_alerts(risk))

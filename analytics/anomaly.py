from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def anomaly_scores(features,contamination=.08):
    out=features.copy(); cols=[c for c in out.select_dtypes("number").columns if c!="anomaly_score"]
    if len(out)<3 or not cols: out["anomaly_score"]=0.0; return out
    x=StandardScaler().fit_transform(out[cols].fillna(0)); model=IsolationForest(contamination=min(max(contamination,.001),.49),random_state=42); raw=-model.fit(x).decision_function(x); lo,hi=raw.min(),raw.max(); out["anomaly_score"]=(100*(raw-lo)/(hi-lo) if hi>lo else 0).round(2); return out

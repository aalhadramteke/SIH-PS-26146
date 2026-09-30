import pandas as pd

def score_risk(features,mixing):
    out=features.merge(mixing,on="address",how="left",suffixes=("","_mix")).fillna(0)
    def norm(c):
        x=pd.to_numeric(out.get(c,0),errors="coerce").fillna(0); return (x/(x.max() or 1)).clip(0,1)
    out["risk_score"]=(.55*norm("anomaly_score")*100+.20*norm("peeling_score")*100+.15*norm("mixer_score")*100+.10*norm("fanout_ratio")*100).round(2); out["risk_level"]=pd.cut(out.risk_score,[-1,30,60,80,101],labels=["Low","Medium","High","Critical"])
    reasons=[]
    for _,r in out.iterrows():
        why=[]
        if r.get("anomaly_score",0)>=60: why.append("unusual behavior")
        if r.get("peeling_score",0)>0: why.append("peeling-chain pattern")
        if r.get("mixer_score",0)>0: why.append("high fan-out / mixer indicator")
        reasons.append("; ".join(why) or "baseline activity")
    out["explanation"]=reasons; return out.sort_values("risk_score",ascending=False).reset_index(drop=True)

def ranked_alerts(risk,limit=100): return risk.loc[risk.risk_score>=60].head(limit).copy()

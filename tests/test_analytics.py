import pandas as pd
from analytics.pipeline import AnalyticsPipeline

def test_pipeline_schema_tolerant_and_ranked():
    data=pd.DataFrame({"txid":["a","b","c","d"],"from_address":["A","A","A","X"],"to_address":["B","C","D","A"],"amount":[10,9,8,2]})
    result=AnalyticsPipeline().run(data)
    assert {"risk_score","risk_level","explanation"}.issubset(result.risk.columns)
    assert len(result.transactions)==4 and result.risk.address.notna().all()

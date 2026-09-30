from __future__ import annotations
import numpy as np
import pandas as pd
from .graph import address_summary

def extract_features(tx, graph):
    s=address_summary(graph).set_index("address")
    grouped=tx.groupby("input_address").agg(tx_count=("tx_id","nunique"),total_volume=("input_value","sum"),mean_value=("input_value","mean"),unique_recipients=("output_address","nunique"),active_days=("timestamp",lambda x:x.dropna().dt.date.nunique()))
    grouped=grouped.join(s,how="outer").fillna(0); grouped["fanout_ratio"]=grouped.unique_recipients/grouped.tx_count.clip(lower=1); grouped["in_out_ratio"]=grouped.in_value/grouped.out_value.clip(lower=1); grouped["value_concentration"]=grouped.mean_value/grouped.total_volume.clip(lower=1)
    numeric=grouped.select_dtypes("number").columns; grouped[numeric]=grouped[numeric].replace([np.inf,-np.inf],0).fillna(0)
    return grouped.reset_index().rename(columns={"input_address":"address"})

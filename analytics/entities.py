from __future__ import annotations
import networkx as nx

def cluster_entities(graph):
    rows=[]
    for i,members in enumerate(sorted(nx.connected_components(nx.Graph(graph)),key=lambda x:(-len(x),sorted(x)[0]))):
        for address in members: rows.append({"address":address,"entity_id":f"entity-{i+1:04d}","entity_size":len(members)})
    import pandas as pd
    return pd.DataFrame(rows)

def mixing_indicators(tx,graph):
    f=tx.groupby("input_address").agg(out_degree=("output_address","nunique"),tx_count=("tx_id","nunique"),total_value=("input_value","sum"),recipient_entropy=("output_address","nunique"))
    f["peeling_score"]=((f.out_degree<=2)&(f.tx_count>=3)).astype(float)*(f.tx_count/f.tx_count.max()).fillna(0); f["mixer_score"]=((f.out_degree>=5)|(f.recipient_entropy>=5)).astype(float)
    return f.reset_index().rename(columns={"input_address":"address"})

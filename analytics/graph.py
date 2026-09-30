from __future__ import annotations
import networkx as nx
import pandas as pd

def build_transaction_graph(tx: pd.DataFrame) -> nx.MultiDiGraph:
    g=nx.MultiDiGraph()
    for row in tx.to_dict("records"):
        g.add_node(row["input_address"],kind="address"); g.add_node(row["output_address"],kind="address"); g.add_edge(row["input_address"],row["output_address"],**row)
    return g

def address_summary(g):
    rows=[]
    for n in g.nodes:
        rows.append({"address":n,"in_degree":g.in_degree(n),"out_degree":g.out_degree(n),"total_degree":g.degree(n),"in_value":sum(d.get("output_value",0) for _,_,d in g.in_edges(n,data=True)),"out_value":sum(d.get("input_value",0) for _,_,d in g.out_edges(n,data=True))})
    return pd.DataFrame(rows)

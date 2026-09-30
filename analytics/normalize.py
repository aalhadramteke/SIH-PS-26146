from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import pandas as pd

ALIASES={"tx_id":("tx_id","txid","transaction_id","hash","id"),"timestamp":("timestamp","time","block_time","datetime","date"),"block_height":("block_height","block","height"),"input_address":("input_address","from_address","sender","source","address_in"),"output_address":("output_address","to_address","recipient","target","address_out"),"input_value":("input_value","value_in","amount_in","input_amount","amount"),"output_value":("output_value","value_out","amount_out","output_amount","amount")}

def _records(source: Any) -> pd.DataFrame:
    if isinstance(source,pd.DataFrame): return source.copy()
    if isinstance(source,(str,Path)):
        p=Path(source)
        if p.suffix.lower()==".csv": return pd.read_csv(p)
        if p.suffix.lower() in (".json",".jsonl"): return pd.read_json(p,lines=p.suffix.lower()==".jsonl")
        if p.suffix.lower() == ".xml":
            from bitcoin_monitoring.ingestion import read_records
            return pd.DataFrame([r.to_dict() for r in read_records(p)])
        raise ValueError(f"Unsupported input file: {p.suffix}")
    if isinstance(source,list): return pd.DataFrame(source)
    if isinstance(source,dict):
        for key in ("transactions","data","records","edges"):
            if isinstance(source.get(key),list): return pd.DataFrame(source[key])
        return pd.DataFrame(source)
    raise TypeError("source must be a DataFrame, path, list, or dict")

def normalize_transactions(source: Any) -> pd.DataFrame:
    raw=_records(source); lower={str(c).lower():c for c in raw.columns}; rename={}
    for target,names in ALIASES.items():
        for name in names:
            if name in lower: rename[lower[name]]=target; break
    df=raw.rename(columns=rename).copy()
    for col in ("inputs", "outputs", "input_addresses", "output_addresses", "input_amounts", "output_amounts"):
        if col in df:
            df[col] = df[col].map(lambda v: json.loads(v) if isinstance(v, str) and v[:1] in "[{" else v)
    if "input_address" not in df and "input_addresses" in df: df["input_address"] = df["input_addresses"]
    if "output_address" not in df and "output_addresses" in df: df["output_address"] = df["output_addresses"]
    if "input_address" not in df and "inputs" in df:
        df["input_address"] = df["inputs"].map(lambda values: [v.get("address", v) if isinstance(v, dict) else v for v in values])
    if "output_address" not in df and "outputs" in df:
        df["output_address"] = df["outputs"].map(lambda values: [v.get("address", v) if isinstance(v, dict) else v for v in values])
    if "input_value" not in df and "input_value_sats" in df: df["input_value"] = pd.to_numeric(df["input_value_sats"], errors="coerce") / 100_000_000
    if "output_value" not in df and "output_value_sats" in df: df["output_value"] = pd.to_numeric(df["output_value_sats"], errors="coerce") / 100_000_000
    # A compact synthetic export often has one ``amount`` column.  Treat it
    # as the observed transfer value for both sides rather than silently
    # making input volume zero.
    if "input_value" not in df and "output_value" in df:
        df["input_value"] = df["output_value"]
    if "output_value" not in df and "input_value" in df:
        df["output_value"] = df["input_value"]
    if "tx_id" not in df: df["tx_id"]=[f"tx-{i}" for i in range(len(df))]
    for col in ("input_address","output_address"):
        if col not in df: df[col]="unknown"
    rows=[]
    for rec in df.to_dict("records"):
        ins=rec["input_address"] if isinstance(rec["input_address"],list) else [rec["input_address"]]
        outs=rec["output_address"] if isinstance(rec["output_address"],list) else [rec["output_address"]]
        for src in ins or ["unknown"]:
            for dst in outs or ["unknown"]:
                item=dict(rec); item.update(input_address=str(src),output_address=str(dst)); rows.append(item)
    out=pd.DataFrame(rows)
    for col in ("input_value","output_value","block_height"):
        if col not in out: out[col]=0.0
        out[col]=pd.to_numeric(out[col],errors="coerce").fillna(0.0)
    if "timestamp" not in out: out["timestamp"]=pd.NaT
    out["timestamp"]=pd.to_datetime(out["timestamp"],errors="coerce",utc=True); out["tx_id"]=out.tx_id.astype(str)
    for col in ("input_address","output_address"): out[col]=out[col].fillna("unknown").astype(str)
    out["fee"]=(out.input_value-out.output_value).clip(lower=0)
    return out.reset_index(drop=True)

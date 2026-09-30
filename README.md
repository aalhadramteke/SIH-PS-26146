# BTC-Trace AI

Offline AI-powered monitoring and analysis of synthetic Bitcoin transaction and P2P metadata for SIH 26146.

## What is included

- Reproducible synthetic data generator with normal, anomalous, peeling-chain, and mixing-like scenarios.
- CSV, JSON, and XML ingestion with schema validation.
- Network and blockchain correlation into an address transaction graph.
- Isolation Forest anomaly detection, connected-component entity clustering, and behavior indicators.
- Explainable risk scoring and ranked investigation alerts.
- Streamlit dashboard for overview, alerts, entity clusters, and transaction exploration.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -e .

python -m bitcoin_monitoring.cli generate --count 1000 --seed 42 --scenario mixed --format json --output sample_transactions.json
python -m bitcoin_monitoring.cli validate sample_transactions.json
python -m streamlit run dashboard/app.py
```

The dashboard also accepts CSV/JSON uploads or a local path from the sidebar. XML is supported by the ingestion library and CLI.

## Architecture

```text
CSV / JSON / XML -> validation -> normalization -> graph + features
                                      -> Isolation Forest + clustering
                                      -> explainable risk alerts -> dashboard
```

The generated labels are retained only as ground truth for evaluation; the analytics pipeline does not use them as model features.

## Tests

```bash
python -m pytest -q
```

## Offline GeoIP

Optional MaxMind `.mmdb` files can be placed in `data/geoip/`. The synthetic generator always includes deterministic country and ASN fields so the prototype works without network access.

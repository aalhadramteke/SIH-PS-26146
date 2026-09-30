"""Analyst console for the offline Bitcoin transaction monitoring prototype.

Run with::

    streamlit run dashboard/app.py

The dashboard deliberately keeps ingestion and scoring in ``AnalyticsPipeline``.
The UI only presents the normalized transactions, explainable risk scores, entity
clusters, and NetworkX graph produced by that pipeline.
"""

from __future__ import annotations

import html
import inspect
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import streamlit as st

try:  # Plotly is a project dependency, but keep a graceful chart fallback.
    import plotly.graph_objects as go

    PLOTLY_AVAILABLE = True
except ImportError:  # pragma: no cover - useful for a minimal local install.
    go = None
    PLOTLY_AVAILABLE = False


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from analytics.pipeline import AnalyticsPipeline  # noqa: E402


# Optional project-level styling/components can be added without making the
# dashboard depend on them.  The local fallback below is the reference design.
try:  # pragma: no cover - these modules are optional in the prototype.
    from dashboard import components as _dashboard_components
except Exception:  # pragma: no cover
    _dashboard_components = None

try:  # pragma: no cover - these modules are optional in the prototype.
    from dashboard import theme as _dashboard_theme
except Exception:  # pragma: no cover
    _dashboard_theme = None


NAV_ITEMS = {
    "Overview": "⌂  Overview",
    "Alerts": "⚠  Alert triage",
    "Entities": "◎  Entities",
    "Transactions": "▤  Transactions",
    "Network & timeline": "⌁  Network & timeline",
}

RISK_ORDER = ["Critical", "High", "Medium", "Low"]
RISK_COLORS = {
    "Critical": "#fb7185",
    "High": "#fb923c",
    "Medium": "#facc15",
    "Low": "#38bdf8",
}
THEME_COLORS = getattr(_dashboard_theme, "COLORS", {})
ACCENT = THEME_COLORS.get("cyan", "#38bdf8")
MUTED = THEME_COLORS.get("muted", "#8fa5bd")
TEXT = THEME_COLORS.get("text", "#e7f0f8")


def _apply_optional_theme() -> None:
    """Use a repository theme hook when one exists, then add safe defaults."""

    if _dashboard_theme is not None:
        for hook_name in ("apply_theme", "inject_css", "configure"):
            hook = getattr(_dashboard_theme, hook_name, None)
            if callable(hook):
                try:
                    hook()
                    break
                except TypeError:
                    # A future theme may require a configuration object.  The
                    # local theme remains a reliable fallback in that case.
                    continue
                except Exception:
                    break

    st.markdown(
        """
        <style>
        :root {
            --btc-bg: #07111f;
            --btc-panel: #101d2e;
            --btc-panel-alt: #14263a;
            --btc-border: rgba(143, 165, 189, .18);
            --btc-text: #e7f0f8;
            --btc-muted: #8fa5bd;
            --btc-accent: #38bdf8;
        }
        .stApp {
            background: radial-gradient(circle at 82% -8%, rgba(22, 92, 135, .28), transparent 31%),
                        linear-gradient(135deg, #07111f 0%, #0a1625 52%, #081321 100%);
            color: var(--btc-text);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a1727 0%, #081321 100%);
            border-right: 1px solid var(--btc-border);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { padding: 2rem 2.4rem 3.5rem; max-width: 1720px; }
        .btc-brand { display:flex; align-items:center; gap:.7rem; padding:.25rem .35rem 1.35rem; }
        .btc-brand-mark {
            width: 2.15rem; height: 2.15rem; display:flex; align-items:center; justify-content:center;
            border-radius: .7rem; background: linear-gradient(135deg, #f7931a, #ffb14e);
            color: #1d1305; font-weight: 900; font-size: 1.35rem; box-shadow: 0 8px 20px rgba(247,147,26,.22);
        }
        .btc-brand-name { color: var(--btc-text); font-weight: 780; letter-spacing: .01em; font-size: 1.05rem; }
        .btc-brand-sub { color: var(--btc-muted); font-size: .67rem; letter-spacing: .12em; text-transform: uppercase; margin-top:.16rem; }
        .side-caption { color: var(--btc-muted); font-size: .7rem; letter-spacing:.12em; text-transform:uppercase; margin: .35rem 0 .5rem; }
        .hero {
            border: 1px solid rgba(56,189,248,.22); border-radius: 1rem; padding: 1.35rem 1.55rem;
            background: linear-gradient(105deg, rgba(20,38,58,.96), rgba(16,29,46,.76));
            box-shadow: 0 16px 38px rgba(0,0,0,.16); margin-bottom: 1.35rem;
        }
        .hero-kicker { color: var(--btc-accent); text-transform: uppercase; letter-spacing: .16em; font-size: .68rem; font-weight:700; }
        .hero-title { color: var(--btc-text); font-size: 2.05rem; line-height:1.1; font-weight: 760; margin:.32rem 0 .45rem; }
        .hero-copy { color: var(--btc-muted); font-size: .92rem; margin:0; }
        .hero-meta { display:flex; gap:.5rem; flex-wrap:wrap; margin-top:.9rem; }
        .tag { display:inline-flex; align-items:center; gap:.32rem; padding:.28rem .56rem; border-radius:999px; font-size:.7rem; color:#b9d7ec; background:rgba(56,189,248,.10); border:1px solid rgba(56,189,248,.2); }
        .tag.green { color:#9ee7c0; background:rgba(52,211,153,.1); border-color:rgba(52,211,153,.2); }
        .tag.orange { color:#ffd09b; background:rgba(251,146,60,.1); border-color:rgba(251,146,60,.2); }
        .kpi-card { min-height: 122px; padding: 1rem 1.05rem .9rem; border:1px solid var(--btc-border); border-radius:.8rem; background:linear-gradient(145deg, rgba(20,38,58,.94), rgba(16,29,46,.92)); box-shadow: 0 10px 22px rgba(0,0,0,.11); }
        .kpi-label { color:var(--btc-muted); text-transform:uppercase; letter-spacing:.1em; font-size:.64rem; font-weight:700; }
        .kpi-value { color:var(--btc-text); font-size:1.65rem; line-height:1.2; font-weight:760; margin-top:.48rem; }
        .kpi-note { color:#7790a9; font-size:.72rem; margin-top:.38rem; }
        .section-kicker { color:var(--btc-accent); font-size:.65rem; letter-spacing:.15em; text-transform:uppercase; font-weight:750; margin-top:.55rem; }
        .section-title { color:var(--btc-text); font-size:1.18rem; font-weight:720; margin:.15rem 0 .15rem; }
        .section-copy { color:var(--btc-muted); font-size:.8rem; margin:0 0 .75rem; }
        .detail-card { border:1px solid var(--btc-border); border-radius:.8rem; background:rgba(16,29,46,.72); padding:1rem 1.1rem; }
        .detail-label { color:var(--btc-muted); text-transform:uppercase; letter-spacing:.1em; font-size:.62rem; font-weight:700; }
        .detail-value { color:var(--btc-text); font-size:1rem; font-weight:680; margin-top:.28rem; overflow-wrap:anywhere; }
        .alert-banner { border-left:3px solid #fb7185; background:rgba(251,113,133,.08); padding:.7rem .85rem; border-radius:0 .55rem .55rem 0; color:#ffd6dc; }
        .info-banner { border-left:3px solid var(--btc-accent); background:rgba(56,189,248,.08); padding:.7rem .85rem; border-radius:0 .55rem .55rem 0; color:#c9e9f9; }
        .muted { color:var(--btc-muted); }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
        div[data-testid="stDataFrame"] { border:1px solid var(--btc-border); border-radius:.6rem; overflow:hidden; }
        div[data-testid="stMetric"] { background:rgba(20,38,58,.5); border:1px solid var(--btc-border); padding:.8rem; border-radius:.65rem; }
        div[data-testid="stMetricLabel"] { color:var(--btc-muted); }
        .stButton > button { border:1px solid rgba(56,189,248,.3); background:rgba(56,189,248,.08); color:#cfeefe; }
        .stButton > button:hover { border-color:var(--btc-accent); color:white; }
        hr { border-color:var(--btc-border); }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # The analyst-console defaults above are intentionally conservative.  The
    # presentation layer below gives the SIH build an India GovTech identity
    # while keeping the information architecture and graph visuals intact.
    st.markdown(
        """
        <style>
        :root {
            --btc-bg: #f4f7fb; --btc-panel: #ffffff; --btc-panel-alt: #f8fafc;
            --btc-border: #d6e0ec; --btc-text: #10233f; --btc-muted: #6b7e95;
            --btc-accent: #174f92;
        }
        .stApp { background: linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%); color: #10233f; }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #d6e0ec; }
        [data-testid="stHeader"] { background: rgba(247,249,252,.9); }
        .block-container { max-width: 1560px; padding: 1.8rem 3rem 3.5rem; }
        .hero { background: #ffffff; border-color: #cfdae8; box-shadow: 0 10px 28px rgba(16,35,63,.07); }
        .hero::before { background: linear-gradient(90deg,#ff9933 0 33.33%,#174f92 33.33% 66.66%,#138808 66.66%); }
        .hero-title, .section-title, .detail-value, .kpi-value { color: #10233f; }
        .hero-kicker, .section-kicker { color: #174f92; }
        .hero-copy, .section-copy, .kpi-note, .detail-label { color: #6b7e95; }
        .tag { color: #174f92; background: #eef5fd; border-color: #c7d9ee; }
        .tag.green { color: #137a2a; background: #edf8ef; border-color: #c4e3c8; }
        .tag.orange { color: #af5b12; background: #fff4e9; border-color: #f3d1ae; }
        .kpi-card, .detail-card { background: #ffffff; border-color: #d6e0ec; box-shadow: 0 8px 22px rgba(16,35,63,.06); }
        div[data-testid="stMetric"] { background: #ffffff; border-color: #d6e0ec; }
        div[data-testid="stDataFrame"] { border-color: #d6e0ec; background: #ffffff; }
        .stButton > button { color: #ffffff; background: #174f92; border-color: #174f92; }
        .stButton > button:hover { color: #ffffff; background: #0f3d77; border-color: #0f3d77; }
        hr { border-color: #d6e0ec; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _safe_text(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return ", ".join(_safe_text(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, default=str)
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _short(value: Any, left: int = 9, right: int = 7) -> str:
    text = _safe_text(value)
    if len(text) <= left + right + 1:
        return text
    return f"{text[:left]}…{text[-right:]}"


def _float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if pd.notna(number) else default
    except (TypeError, ValueError):
        return default


def _fmt_num(value: Any, decimals: int = 0) -> str:
    return f"{_float(value):,.{decimals}f}"


def _fmt_btc(value: Any, decimals: int = 4) -> str:
    return f"{_float(value):,.{decimals}f} BTC"


def _resolve_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute() or candidate.exists():
        return candidate
    return ROOT / candidate


def _load_upload(uploaded: Any) -> Any:
    """Convert an uploaded document to a pipeline-compatible source."""

    suffix = Path(uploaded.name).suffix.lower()
    payload = uploaded.getvalue()
    if suffix == ".csv":
        return pd.read_csv(io.BytesIO(payload))
    if suffix in {".json", ".jsonl"}:
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return pd.read_json(io.BytesIO(payload), lines=True)
    if suffix == ".xml":
        # The canonical XML reader performs schema validation.  Use a short-
        # lived file because AnalyticsPipeline itself accepts paths for XML.
        from bitcoin_monitoring.ingestion import read_records

        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as handle:
                handle.write(payload)
                temp_path = handle.name
            return [record.to_dict() for record in read_records(temp_path)]
        finally:
            if temp_path:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except OSError:
                    pass
    raise ValueError("Supported uploads are CSV, JSON, and XML.")


@st.cache_data(show_spinner=False)
def _run_pipeline(source: Any, contamination: float, file_version: int = 0) -> Any:
    # ``file_version`` invalidates a path-based cache when the file is edited.
    return AnalyticsPipeline().run(source, contamination=float(contamination))


def _unique_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions is None or transactions.empty:
        return pd.DataFrame()
    if "tx_id" not in transactions.columns:
        return transactions.copy()
    return transactions.drop_duplicates(subset=["tx_id"], keep="first").copy()


def _series(df: pd.DataFrame, name: str, default: Any = 0) -> pd.Series:
    if name in df.columns:
        return df[name]
    return pd.Series(default, index=df.index)


def _risk_frame(result: Any) -> pd.DataFrame:
    risk = getattr(result, "risk", pd.DataFrame())
    if risk is None:
        return pd.DataFrame()
    risk = risk.copy()
    if "risk_score" not in risk.columns:
        risk["risk_score"] = 0.0
    risk["risk_score"] = pd.to_numeric(risk["risk_score"], errors="coerce").fillna(0.0)
    if "risk_level" not in risk.columns:
        risk["risk_level"] = "Low"
    risk["risk_level"] = risk["risk_level"].astype(str).replace("nan", "Low")
    if "address" not in risk.columns:
        risk["address"] = "unknown"
    return risk.sort_values("risk_score", ascending=False).reset_index(drop=True)


def _entity_frame(result: Any, risk: pd.DataFrame) -> pd.DataFrame:
    entities = getattr(result, "entities", pd.DataFrame())
    if entities is None or entities.empty:
        return pd.DataFrame(columns=["address", "entity_id", "entity_size"])
    entities = entities.copy()
    if "address" not in entities.columns:
        entities["address"] = "unknown"
    if "entity_id" not in entities.columns:
        entities["entity_id"] = "entity-unknown"
    if "entity_size" not in entities.columns:
        entities["entity_size"] = 1
    extra = [
        col
        for col in (
            "risk_score",
            "risk_level",
            "tx_count",
            "total_volume",
            "explanation",
            "anomaly_score",
            "peeling_score",
            "mixer_score",
        )
        if col in risk.columns
    ]
    if extra:
        entities = entities.merge(risk[["address", *extra]], on="address", how="left", suffixes=("", "_risk"))
    return entities


def _entity_summary(entity_rows: pd.DataFrame, transactions: pd.DataFrame | None = None) -> pd.DataFrame:
    if entity_rows.empty:
        return pd.DataFrame()
    work = entity_rows.copy()
    work["risk_score"] = pd.to_numeric(_series(work, "risk_score"), errors="coerce").fillna(0.0)
    work["tx_count"] = pd.to_numeric(_series(work, "tx_count"), errors="coerce").fillna(0.0)
    work["total_volume"] = pd.to_numeric(_series(work, "total_volume"), errors="coerce").fillna(0.0)
    work["risk_level"] = _series(work, "risk_level", "Low").astype(str)
    summary = (
        work.groupby("entity_id", as_index=False)
        .agg(
            members=("address", "nunique"),
            entity_size=("entity_size", "max"),
            tx_count=("tx_count", "sum"),
            volume_btc=("total_volume", "sum"),
            max_risk=("risk_score", "max"),
            alert_count=("risk_score", lambda values: int((values >= 60).sum())),
        )
        .sort_values(["max_risk", "members"], ascending=[False, False])
        .reset_index(drop=True)
    )
    summary["risk_level"] = summary["max_risk"].map(
        lambda score: "Critical" if score > 80 else "High" if score > 60 else "Medium" if score > 30 else "Low"
    )
    if transactions is not None and not transactions.empty:
        # Normalization creates input/output cross-product rows. Summing
        # address feature volumes would count those rows repeatedly, so entity
        # KPIs use each transaction ID once within its connected component.
        address_to_entity = work.drop_duplicates("address").set_index("address")["entity_id"]
        unique_tx = _unique_transactions(transactions)
        unique_tx["entity_id"] = unique_tx["input_address"].map(address_to_entity)
        activity = unique_tx.groupby("entity_id").agg(
            transactions=("tx_id", "nunique"), volume=("input_value", "sum")
        )
        summary["tx_count"] = summary["entity_id"].map(activity["transactions"]).fillna(0)
        summary["volume_btc"] = summary["entity_id"].map(activity["volume"]).fillna(0)
    return summary


def _metric_card(label: str, value: str, note: str = "", tone: str = "blue") -> None:
    component = getattr(_dashboard_components, "render_kpi_card", None)
    if callable(component) and _dashboard_theme is not None:
        component(label, value, detail=note, tone={"blue": "info", "orange": "high", "red": "critical", "green": "success"}.get(tone, "neutral"))
        return
    tone_color = {"blue": ACCENT, "orange": "#fb923c", "red": "#fb7185", "green": "#34d399"}.get(tone, ACCENT)
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top:2px solid {tone_color};">
            <div class="kpi-label">{_esc(label)}</div>
            <div class="kpi-value">{_esc(value)}</div>
            <div class="kpi-note">{_esc(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(kicker: str, title: str, copy: str = "") -> None:
    component = getattr(_dashboard_components, "render_section_header", None)
    if callable(component) and _dashboard_theme is not None:
        component(title, copy or None, eyebrow=kicker)
        return
    st.markdown(f'<div class="section-kicker">{_esc(kicker)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{_esc(title)}</div>', unsafe_allow_html=True)
    if copy:
        st.markdown(f'<p class="section-copy">{_esc(copy)}</p>', unsafe_allow_html=True)


def _dataframe(frame: pd.DataFrame, **kwargs: Any) -> None:
    """Share the table component, with compatibility for Streamlit 1.35+."""
    component = getattr(_dashboard_components, "render_data_table", None)
    if callable(component):
        component(frame, height=kwargs.get("height"))
        return
    if "width" in inspect.signature(st.dataframe).parameters:
        kwargs["width"] = "stretch"
    else:
        kwargs["use_container_width"] = True
    st.dataframe(frame, **kwargs)


def _plotly_chart(figure: Any) -> None:
    kwargs = {"width": "stretch"} if "width" in inspect.signature(st.plotly_chart).parameters else {"use_container_width": True}
    st.plotly_chart(figure, config={"displayModeBar": False}, **kwargs)


def _plot_layout(fig: Any, height: int = 360) -> Any:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=12, r=12, t=28, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, ui-sans-serif, sans-serif", color=TEXT, size=12),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#cbd8e7", font=dict(color=TEXT)),
    )
    return fig


def _risk_distribution(risk: pd.DataFrame) -> Any:
    counts = risk["risk_level"].value_counts().reindex(RISK_ORDER, fill_value=0) if not risk.empty else pd.Series(dtype=int)
    if not PLOTLY_AVAILABLE:
        return None, counts
    fig = go.Figure(
        go.Bar(
            x=counts.index.tolist(),
            y=counts.values.tolist(),
            marker_color=[RISK_COLORS[level] for level in counts.index],
            text=[_fmt_num(value) for value in counts.values],
            textposition="outside",
            hovertemplate="%{x}<br>%{y:,} addresses<extra></extra>",
        )
    )
    fig.update_yaxes(title="Addresses", gridcolor="rgba(143,165,189,.12)", zeroline=False)
    fig.update_xaxes(title=None)
    return _plot_layout(fig, 310), counts


def _timeline_frame(transactions: pd.DataFrame) -> pd.DataFrame:
    tx = _unique_transactions(transactions)
    if tx.empty or "timestamp" not in tx.columns:
        return pd.DataFrame()
    tx["timestamp"] = pd.to_datetime(tx["timestamp"], errors="coerce", utc=True)
    tx = tx.dropna(subset=["timestamp"]).copy()
    if tx.empty:
        return tx
    span_days = max(0.0, (tx["timestamp"].max() - tx["timestamp"].min()).total_seconds() / 86400)
    frequency = "h" if span_days <= 3 else "D"
    tx["bucket"] = tx["timestamp"].dt.floor(frequency)
    tx["input_value"] = pd.to_numeric(_series(tx, "input_value"), errors="coerce").fillna(0.0)
    tx["fee"] = pd.to_numeric(_series(tx, "fee"), errors="coerce").fillna(0.0)
    return (
        tx.groupby("bucket", as_index=False)
        .agg(transactions=("tx_id", "nunique"), volume_btc=("input_value", "sum"), fees_btc=("fee", "sum"))
        .sort_values("bucket")
    )


def _timeline_chart(transactions: pd.DataFrame, risk: pd.DataFrame | None = None) -> Any:
    timeline = _timeline_frame(transactions)
    if not PLOTLY_AVAILABLE or timeline.empty:
        return None, timeline
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=timeline["bucket"],
            y=timeline["volume_btc"],
            name="Volume (BTC)",
            marker_color="rgba(56,189,248,.55)",
            hovertemplate="%{x|%d %b %H:%M}<br>%{y:,.4f} BTC<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=timeline["bucket"],
            y=timeline["transactions"],
            name="Transactions",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color="#f5b84b", width=2),
            marker=dict(size=5),
            hovertemplate="%{x|%d %b %H:%M}<br>%{y:,} transactions<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis=dict(title="BTC volume", gridcolor="rgba(143,165,189,.12)", zeroline=False),
        yaxis2=dict(title="Transactions", overlaying="y", side="right", showgrid=False),
        xaxis=dict(title=None),
        legend=dict(orientation="h", y=1.12, x=0),
    )
    return _plot_layout(fig, 330), timeline


def _alert_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    columns = [
        "address",
        "risk_score",
        "risk_level",
        "explanation",
        "entity_id",
        "entity_size",
        "tx_count",
        "total_volume",
    ]
    out = frame[[col for col in columns if col in frame.columns]].copy()
    if "address" in out:
        out["address"] = out["address"].map(_short)
    if "risk_score" in out:
        out["risk_score"] = out["risk_score"].map(lambda value: round(_float(value), 2))
    if "total_volume" in out:
        out["total_volume"] = out["total_volume"].map(lambda value: round(_float(value), 6))
    return out.rename(
        columns={
            "address": "Address",
            "risk_score": "Risk",
            "risk_level": "Level",
            "explanation": "Evidence",
            "entity_id": "Entity",
            "entity_size": "Entity size",
            "tx_count": "Tx count",
            "total_volume": "Volume (BTC)",
        }
    )


def _transaction_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    columns = [
        "tx_id",
        "timestamp",
        "block_height",
        "input_address",
        "output_address",
        "input_value",
        "output_value",
        "fee",
        "scenario",
        "geo_country",
        "asn",
    ]
    out = frame[[col for col in columns if col in frame.columns]].copy()
    for col in ("tx_id", "input_address", "output_address"):
        if col in out:
            out[col] = out[col].map(_short)
    if "timestamp" in out:
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce", utc=True).dt.strftime("%Y-%m-%d %H:%M")
    for col in ("input_value", "output_value", "fee"):
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(8)
    return out.rename(
        columns={
            "tx_id": "Transaction",
            "timestamp": "Time (UTC)",
            "block_height": "Block",
            "input_address": "From",
            "output_address": "To",
            "input_value": "Input (BTC)",
            "output_value": "Output (BTC)",
            "fee": "Fee (BTC)",
            "scenario": "Scenario",
            "geo_country": "Country",
            "asn": "ASN",
        }
    )


def _risk_gauge(score: float) -> Any:
    if not PLOTLY_AVAILABLE:
        return None
    color = RISK_COLORS["Critical"] if score >= 80 else RISK_COLORS["High"] if score >= 60 else RISK_COLORS["Medium"] if score >= 30 else RISK_COLORS["Low"]
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"font": {"color": TEXT, "size": 30}, "suffix": "/100"},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": MUTED, "tickfont": {"color": MUTED}},
                "bar": {"color": color, "thickness": .28},
                "bgcolor": "rgba(143,165,189,.10)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 30], "color": "rgba(56,189,248,.08)"},
                    {"range": [30, 60], "color": "rgba(250,204,21,.08)"},
                    {"range": [60, 80], "color": "rgba(251,146,60,.08)"},
                    {"range": [80, 100], "color": "rgba(251,113,133,.08)"},
                ],
            },
        )
    )
    return _plot_layout(fig, 225)


def _network_figure(graph: nx.MultiDiGraph, risk: pd.DataFrame, center: str, depth: int = 1, max_nodes: int = 55) -> tuple[Any, pd.DataFrame]:
    if graph is None or center not in graph or graph.number_of_nodes() == 0:
        return None, pd.DataFrame()
    undirected = nx.Graph(graph)
    distances = nx.single_source_shortest_path_length(undirected, center, cutoff=max(1, depth))
    candidate_nodes = list(distances)
    if len(candidate_nodes) > max_nodes:
        candidate_nodes = sorted(candidate_nodes, key=lambda node: graph.degree(node), reverse=True)[:max_nodes]
        if center not in candidate_nodes:
            candidate_nodes[-1] = center
    subgraph = graph.subgraph(candidate_nodes).copy()
    if not PLOTLY_AVAILABLE:
        return None, pd.DataFrame({"address": list(subgraph.nodes)})

    layout = nx.spring_layout(nx.Graph(subgraph), seed=42, k=1.35 / max(1, len(subgraph.nodes) ** .33), iterations=65)
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_hover: list[str] = []
    edge_rows: list[dict[str, Any]] = []
    for index, (source, target, data) in enumerate(subgraph.edges(data=True)):
        if index >= 180:
            break
        x0, y0 = layout[source]
        x1, y1 = layout[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        value = _float(data.get("input_value", data.get("input_value_sats", 0)))
        edge_hover.extend([f"{_short(source)} → {_short(target)}<br>{value:,.6f} BTC", "", ""])
        edge_rows.append({"from": source, "to": target, "value_btc": value, "tx_id": data.get("tx_id", "")})

    risk_lookup = risk.drop_duplicates("address").set_index("address") if not risk.empty and "address" in risk else pd.DataFrame()
    node_x: list[float] = []
    node_y: list[float] = []
    node_text: list[str] = []
    node_scores: list[float] = []
    node_sizes: list[float] = []
    for node in subgraph.nodes:
        x, y = layout[node]
        node_x.append(x)
        node_y.append(y)
        score = _float(risk_lookup.loc[node, "risk_score"]) if not risk_lookup.empty and node in risk_lookup.index else 0.0
        level = _safe_text(risk_lookup.loc[node, "risk_level"]) if not risk_lookup.empty and node in risk_lookup.index else "Unscored"
        node_scores.append(score)
        node_sizes.append(18 if node == center else 11 + min(13, graph.degree(node)))
        node_text.append(
            f"<b>{_esc(_short(node, 12, 10))}</b><br>Risk: {score:.1f}<br>Level: {_esc(level)}<br>Degree: {graph.degree(node)}"
        )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1, color="rgba(143,165,189,.25)"),
            hoverinfo="text",
            text=edge_hover,
            name="Flow",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            hoverinfo="text",
            text=node_text,
            name="Address",
            marker=dict(
                size=node_sizes,
                color=node_scores,
                colorscale=[[0, "#38bdf8"], [.3, "#facc15"], [.6, "#fb923c"], [1, "#fb7185"]],
                cmin=0,
                cmax=100,
                line=dict(width=1.2, color="#d9efff"),
                colorbar=dict(title=dict(text="Risk", font=dict(color=MUTED)), tickfont=dict(color=MUTED)),
            ),
        )
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(showlegend=False)
    return _plot_layout(fig, 590), pd.DataFrame(edge_rows)


def _render_sidebar() -> tuple[str, Any, str, float, str]:
    rendered_brand = False
    if _dashboard_components is not None:
        brand_hook = getattr(_dashboard_components, "render_sidebar_brand", None)
        if callable(brand_hook):
            try:  # Optional component APIs should never block the local fallback.
                brand_hook(st.sidebar)
                rendered_brand = True
            except TypeError:
                try:
                    brand_hook()
                    rendered_brand = True
                except Exception:
                    rendered_brand = False
            except Exception:
                rendered_brand = False
    if not rendered_brand:
        st.sidebar.markdown(
            """
            <div class="btc-brand">
                <div class="btc-brand-mark">₿</div>
                <div><div class="btc-brand-name">BTC Trace</div><div class="btc-brand-sub">Analyst console</div></div>
            </div>
            <div class="tag green" style="margin:0 .35rem 1.05rem;">●  Offline analysis mode</div>
            """,
            unsafe_allow_html=True,
        )
    st.sidebar.markdown('<div class="side-caption">Workspace</div>', unsafe_allow_html=True)
    page = st.sidebar.radio("Navigation", list(NAV_ITEMS), format_func=lambda item: NAV_ITEMS[item], label_visibility="collapsed")

    mode = "path"
    with st.sidebar.expander("Data source", expanded=True):
        source_mode = st.radio("Load", ["Workspace path", "Upload file"], horizontal=True, label_visibility="collapsed")
        uploaded = None
        if source_mode == "Workspace path":
            path_value = st.text_input("Dataset path", "data/demo/sample_transactions.json", help="Relative paths resolve from the project root.")
            source = _resolve_path(path_value)
            source_label = source.name
            if not source.exists():
                st.warning("Path not found")
        else:
            mode = "upload"
            uploaded = st.file_uploader("CSV, JSON, or XML", type=["csv", "json", "jsonl", "xml"], label_visibility="collapsed")
            source = uploaded
            source_label = uploaded.name if uploaded is not None else "No file selected"
        contamination = st.slider("Anomaly sensitivity", min_value=0.02, max_value=0.20, value=0.08, step=0.01, help="Isolation Forest contamination passed to AnalyticsPipeline.")
        if st.button("↻  Recompute analysis", use_container_width=True):
            _run_pipeline.clear()
            st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown('<div class="side-caption">Scope</div>', unsafe_allow_html=True)
    st.sidebar.caption("Explainable scoring · graph correlation · entity clustering")
    st.sidebar.caption("All processing stays local to this workspace.")
    return page, source, source_label, contamination, mode


def _render_india_masthead() -> None:
    """Render the local Government of India emblem and prototype context."""

    emblem = ROOT / "dashboard" / "assets" / "emblem-of-india.svg"
    logo_slot, copy_slot, meta_slot = st.columns([0.10, 1.55, 0.65], gap="small")
    with logo_slot:
        if emblem.exists():
            try:
                st.image(str(emblem), width=58)
            except TypeError:
                st.image(str(emblem), use_column_width=False, width=58)
    with copy_slot:
        st.markdown(
            """
            <div class="so-india-masthead__copy">
                <p class="so-india-masthead__gov">Government of India</p>
                <p class="so-india-masthead__agency">SIH 2026 · National Technical Research Organisation</p>
                <p class="so-india-masthead__motto">सत्यमेव जयते · Offline Cryptocurrency Intelligence Console</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with meta_slot:
        st.markdown(
            """
            <div class="so-india-masthead__meta">
                <strong>RESTRICTED PROTOTYPE</strong><br>
                Synthetic data only · Local processing
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('<div class="so-tricolor-rule" aria-hidden="true"></div>', unsafe_allow_html=True)


def _render_hero(page: str, source_label: str, transactions: pd.DataFrame, risk: pd.DataFrame) -> None:
    unique_tx = _unique_transactions(transactions)
    timestamps = pd.to_datetime(_series(unique_tx, "timestamp"), errors="coerce", utc=True).dropna()
    if not timestamps.empty:
        date_copy = f"{timestamps.min():%d %b %Y} – {timestamps.max():%d %b %Y}"
    else:
        date_copy = "Timestamp range unavailable"
    alert_count = int((risk["risk_score"] >= 60).sum()) if not risk.empty else 0
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">Bitcoin Intelligence / { _esc(page) }</div>
            <div class="hero-title">A clear view of suspicious value flows.</div>
            <p class="hero-copy">Investigate explainable risk signals across transactions, addresses, and connected entities.</p>
            <div class="hero-meta">
                <span class="tag">▣  {_esc(source_label)}</span>
                <span class="tag">◷  {_esc(date_copy)}</span>
                <span class="tag orange">⚠  {_fmt_num(alert_count)} triage candidates</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_overview(result: Any) -> None:
    transactions = getattr(result, "transactions", pd.DataFrame())
    risk = _risk_frame(result)
    unique_tx = _unique_transactions(transactions)
    entities = getattr(result, "entities", pd.DataFrame())
    graph = getattr(result, "graph", nx.MultiDiGraph())
    total_volume = pd.to_numeric(_series(unique_tx, "input_value"), errors="coerce").fillna(0).sum()
    critical = int((risk["risk_score"] >= 80).sum()) if not risk.empty else 0
    high_plus = int((risk["risk_score"] >= 60).sum()) if not risk.empty else 0
    entity_count = int(entities["entity_id"].nunique()) if not entities.empty and "entity_id" in entities else 0

    st.markdown('<div class="section-kicker">Command summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Network posture at a glance</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-copy">The latest pipeline run, summarized for fast orientation before investigation.</p>', unsafe_allow_html=True)
    kpis = st.columns(5)
    with kpis[0]:
        _metric_card("Transactions", _fmt_num(len(unique_tx)), "unique transaction IDs", "blue")
    with kpis[1]:
        _metric_card("Observed volume", _fmt_btc(total_volume), "input-side value", "green")
    with kpis[2]:
        _metric_card("Triage queue", _fmt_num(high_plus), "score ≥ 60", "orange")
    with kpis[3]:
        _metric_card("Critical", _fmt_num(critical), "score ≥ 80", "red")
    with kpis[4]:
        _metric_card("Entities", _fmt_num(entity_count), f"{graph.number_of_nodes():,} graph nodes", "blue")

    st.write("")
    left, right = st.columns([1, 1.55], gap="large")
    with left:
        _section("Risk posture", "Address risk distribution", "Risk levels are produced by the explainable scoring pipeline.")
        risk_fig, counts = _risk_distribution(risk)
        if risk_fig is not None:
            _plotly_chart(risk_fig)
        elif not counts.empty:
            st.bar_chart(counts)
        else:
            st.info("No scored addresses are available.")
    with right:
        _section("Activity pulse", "Value flow over time", "Unique transactions are bucketed in UTC; short windows use hourly bins.")
        timeline_fig, timeline = _timeline_chart(transactions, risk)
        if timeline_fig is not None:
            _plotly_chart(timeline_fig)
        elif not timeline.empty:
            st.line_chart(timeline.set_index("bucket")[["volume_btc", "transactions"]])
        else:
            st.info("No parseable timestamps are available for a timeline.")

    st.write("")
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        _section("Investigator queue", "Highest-priority leads", "Start with the addresses carrying the strongest combined anomaly and mixing signals.")
        if risk.empty or high_plus == 0:
            st.markdown('<div class="info-banner">No addresses crossed the default triage threshold of 60.</div>', unsafe_allow_html=True)
        else:
            _dataframe(_alert_table(risk[risk["risk_score"] >= 60].head(8)), hide_index=True, height=330)
    with right:
        _section("Pipeline coverage", "What the graph knows", "A compact readout of the normalized dataset and connected-component model.")
        coverage = pd.DataFrame(
            {
                "Measure": ["Graph nodes", "Graph edges", "Scored addresses", "Connected entities", "Normalized edge rows"],
                "Value": [graph.number_of_nodes(), graph.number_of_edges(), len(risk), entity_count, len(transactions)],
            }
        )
        _dataframe(coverage, hide_index=True, height=245)


def _render_alerts(result: Any) -> None:
    transactions = getattr(result, "transactions", pd.DataFrame())
    risk = _risk_frame(result)
    if risk.empty:
        _section("Alert triage", "No scored addresses", "Run the pipeline with a dataset containing normalized address flows.")
        st.info("There are no alerts to review.")
        return

    _section("Alert triage", "Ranked, explainable leads", "Filter the queue, select a lead, and review the address-level evidence behind its score.")
    controls = st.columns([1, 1.25, 1.5, 1.2])
    with controls[0]:
        threshold = st.slider("Minimum score", 0, 100, 60, 5)
    with controls[1]:
        selected_levels = st.multiselect("Risk levels", RISK_ORDER, default=RISK_ORDER)
    with controls[2]:
        alert_search = st.text_input("Find address or entity", placeholder="prefix, entity ID…")
    with controls[3]:
        limit = st.number_input("Rows", min_value=10, max_value=500, value=100, step=10)

    filtered = risk[risk["risk_score"] >= threshold].copy()
    if selected_levels:
        filtered = filtered[filtered["risk_level"].isin(selected_levels)]
    else:
        filtered = filtered.iloc[0:0]
    if alert_search.strip():
        needle = alert_search.strip().lower()
        searchable = filtered.apply(lambda row: " ".join(_safe_text(value) for value in row.values).lower(), axis=1)
        filtered = filtered[searchable.str.contains(needle, regex=False, na=False)]
    filtered = filtered.head(int(limit)).reset_index(drop=True)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        _metric_card("Visible leads", _fmt_num(len(filtered)), f"of {len(risk):,} scored addresses", "blue")
    with metric_cols[1]:
        _metric_card("Critical", _fmt_num(int((filtered["risk_score"] >= 80).sum())), "in current view", "red")
    with metric_cols[2]:
        _metric_card("High", _fmt_num(int(((filtered["risk_score"] >= 60) & (filtered["risk_score"] < 80)).sum())), "in current view", "orange")
    with metric_cols[3]:
        _metric_card("Threshold", f"{threshold}/100", "score floor", "green")

    if filtered.empty:
        st.markdown('<div class="info-banner">No leads match those filters. Lower the score floor or broaden the level selection.</div>', unsafe_allow_html=True)
        return

    _dataframe(_alert_table(filtered), hide_index=True, height=295)
    options = filtered["address"].tolist()
    selected_address = st.selectbox(
        "Selected alert",
        options,
        format_func=lambda address: f"{_short(address, 12, 9)}  ·  {_float(filtered.loc[filtered.address == address, 'risk_score'].iloc[0]):.1f}  ·  {filtered.loc[filtered.address == address, 'risk_level'].iloc[0]}",
    )
    selected_rows = filtered[filtered["address"] == selected_address]
    selected = selected_rows.iloc[0]
    score = _float(selected.get("risk_score"))
    level = _safe_text(selected.get("risk_level", "Unknown"))
    entity_id = _safe_text(selected.get("entity_id", "Unknown"))

    st.divider()
    _section("Selected evidence", "Why this address is in the queue", f"{_short(selected_address, 14, 10)} · {entity_id}")
    detail_left, detail_mid, detail_right = st.columns([1.05, 1.2, 1.5], gap="large")
    with detail_left:
        gauge = _risk_gauge(score)
        if gauge is not None:
            _plotly_chart(gauge)
        else:
            st.metric("Risk score", f"{score:.1f}/100")
        badge_color = RISK_COLORS.get(level, MUTED)
        st.markdown(f'<div class="tag" style="border-color:{badge_color};color:{badge_color};">●  {_esc(level)} risk</div>', unsafe_allow_html=True)
    with detail_mid:
        signal_rows = [
            ("Anomaly score", _fmt_num(selected.get("anomaly_score", 0), 2)),
            ("Peeling signal", _fmt_num(selected.get("peeling_score", 0), 3)),
            ("Mixer signal", _fmt_num(selected.get("mixer_score", 0), 3)),
            ("Fan-out ratio", _fmt_num(selected.get("fanout_ratio", 0), 2)),
            ("Transactions", _fmt_num(selected.get("tx_count", 0))),
            ("Entity size", _fmt_num(selected.get("entity_size", 0))),
        ]
        signal_table = pd.DataFrame(signal_rows, columns=["Signal", "Observed"])
        _dataframe(signal_table, hide_index=True, height=250)
    with detail_right:
        explanation = _safe_text(selected.get("explanation", "No explanation recorded."))
        st.markdown(f'<div class="detail-card"><div class="detail-label">Pipeline explanation</div><div class="detail-value">{_esc(explanation)}</div></div>', unsafe_allow_html=True)
        st.write("")
        related = transactions[
            (_series(transactions, "input_address", "") == selected_address)
            | (_series(transactions, "output_address", "") == selected_address)
        ].copy()
        related_unique = _unique_transactions(related)
        st.markdown(f'<div class="detail-card"><div class="detail-label">Observed activity</div><div class="detail-value">{_fmt_num(len(related_unique))} related transactions · {_fmt_btc(pd.to_numeric(_series(related_unique, "input_value"), errors="coerce").fillna(0).sum())}</div></div>', unsafe_allow_html=True)

    entity_rows = _entity_frame(result, risk)
    if entity_id != "Unknown" and not entity_rows.empty:
        members = entity_rows[entity_rows["entity_id"].astype(str) == entity_id].copy()
        if not members.empty:
            st.write("")
            _section("Entity context", "Connected members", "Addresses in the same connected component as the selected alert.")
            _dataframe(_alert_table(members.sort_values("risk_score", ascending=False).head(20)), hide_index=True, height=250)

    st.write("")
    _section("Transaction evidence", "Flows touching the selected address", "The table is deduplicated by transaction ID even when a transaction has multiple input/output edges.")
    if related_unique.empty:
        st.info("No normalized transaction rows directly reference this address.")
    else:
        _dataframe(_transaction_table(related_unique.head(80)), hide_index=True, height=300)


def _render_entities(result: Any) -> None:
    risk = _risk_frame(result)
    entity_rows = _entity_frame(result, risk)
    transactions = getattr(result, "transactions", pd.DataFrame())
    summary = _entity_summary(entity_rows, transactions)
    if summary.empty:
        _section("Entity intelligence", "No connected entities", "Entity clusters are derived from connected components in the transaction graph.")
        st.info("No entity rows were produced by the pipeline.")
        return

    _section("Entity intelligence", "Connected address clusters", "Move from an individual alert to the wider connected component and its observed activity.")
    controls = st.columns([1, 1.5, 1])
    with controls[0]:
        min_size = st.number_input("Minimum members", min_value=1, max_value=int(max(1, summary["members"].max())), value=1, step=1)
    with controls[1]:
        entity_search = st.text_input("Find entity", placeholder="entity-0001 or address prefix…")
    with controls[2]:
        entity_limit = st.number_input("Rows", min_value=10, max_value=500, value=100, step=10)

    visible = summary[summary["members"] >= min_size].copy()
    if entity_search.strip():
        needle = entity_search.strip().lower()
        entity_address_map = entity_rows.groupby("entity_id")["address"].apply(lambda values: " ".join(values.astype(str))).to_dict()
        visible = visible[
            visible["entity_id"].astype(str).str.lower().str.contains(needle, regex=False)
            | visible["entity_id"].map(entity_address_map).fillna("").str.lower().str.contains(needle, regex=False)
        ]
    visible = visible.head(int(entity_limit)).reset_index(drop=True)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        _metric_card("Entities", _fmt_num(len(summary)), "connected components", "blue")
    with metric_cols[1]:
        _metric_card("Visible", _fmt_num(len(visible)), "matching current filters", "green")
    with metric_cols[2]:
        _metric_card("Largest", _fmt_num(summary["members"].max()), "addresses in one entity", "orange")
    with metric_cols[3]:
        _metric_card("Flagged entities", _fmt_num(int((summary["alert_count"] > 0).sum())), "with score ≥ 60", "red")

    if visible.empty:
        st.info("No entities match those filters.")
        return

    entity_table = visible.copy()
    entity_table["max_risk"] = entity_table["max_risk"].round(2)
    entity_table["volume_btc"] = entity_table["volume_btc"].round(6)
    entity_table = entity_table.rename(
        columns={
            "entity_id": "Entity",
            "members": "Members",
            "entity_size": "Component size",
            "tx_count": "Tx count",
            "volume_btc": "Volume (BTC)",
            "max_risk": "Max risk",
            "alert_count": "Alerts",
            "risk_level": "Level",
        }
    )
    _dataframe(entity_table, hide_index=True, height=300)

    selected_entity = st.selectbox(
        "Selected entity",
        visible["entity_id"].tolist(),
        format_func=lambda entity: f"{entity}  ·  {int(visible.loc[visible.entity_id == entity, 'members'].iloc[0])} members  ·  {visible.loc[visible.entity_id == entity, 'max_risk'].iloc[0]:.1f} risk",
    )
    members = entity_rows[entity_rows["entity_id"] == selected_entity].copy().sort_values("risk_score", ascending=False)
    profile = visible[visible["entity_id"] == selected_entity].iloc[0]
    st.divider()
    _section("Entity profile", selected_entity, "Member-level risk and connected transaction activity.")
    profile_cols = st.columns(5)
    with profile_cols[0]:
        _metric_card("Members", _fmt_num(profile["members"]), "addresses", "blue")
    with profile_cols[1]:
        _metric_card("Max risk", f"{_float(profile['max_risk']):.1f}/100", _safe_text(profile["risk_level"]), "red" if _float(profile["max_risk"]) >= 60 else "orange")
    with profile_cols[2]:
        _metric_card("Entity volume", _fmt_btc(profile["volume_btc"]), "summed address activity", "green")
    with profile_cols[3]:
        _metric_card("Transactions", _fmt_num(profile["tx_count"]), "address-level observations", "blue")
    with profile_cols[4]:
        _metric_card("Alerts", _fmt_num(profile["alert_count"]), "members ≥ 60", "orange")

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        _section("Members", "Address-level evidence", "Risk signals for every member in this component.")
        _dataframe(_alert_table(members.head(100)), hide_index=True, height=360)
    with right:
        _section("Activity", "Entity transaction flow", "Unique transactions touching any member address.")
        member_addresses = set(members["address"].astype(str))
        related = transactions[
            _series(transactions, "input_address", "").astype(str).isin(member_addresses)
            | _series(transactions, "output_address", "").astype(str).isin(member_addresses)
        ]
        related_unique = _unique_transactions(related)
        _dataframe(_transaction_table(related_unique.head(80)), hide_index=True, height=360)

    if not members.empty:
        center = members.iloc[0]["address"]
        graph = getattr(result, "graph", nx.MultiDiGraph())
        graph_fig, _ = _network_figure(graph, risk, center, depth=1, max_nodes=45)
        if graph_fig is not None:
            st.write("")
            _section("Entity topology", "Immediate graph neighborhood", "The selected member is the center node; color indicates address risk.")
            _plotly_chart(graph_fig)


def _render_transactions(result: Any) -> None:
    transactions = getattr(result, "transactions", pd.DataFrame())
    unique_tx = _unique_transactions(transactions)
    if unique_tx.empty:
        _section("Transaction explorer", "No normalized transactions", "Load a CSV, JSON, or XML dataset to begin searching.")
        st.info("No transaction rows are available.")
        return

    _section("Transaction explorer", "Search normalized flows", "Search transaction IDs, addresses, network metadata, or scenario labels, then inspect one transaction in context.")
    scenarios = sorted({_safe_text(value) for value in _series(unique_tx, "scenario", "").tolist() if _safe_text(value)})
    countries = sorted({_safe_text(value) for value in _series(unique_tx, "geo_country", "").tolist() if _safe_text(value)})
    controls = st.columns([1.5, 1.05, 1.05, 1])
    with controls[0]:
        search = st.text_input("Search", placeholder="tx ID, address, IP, ASN…")
    with controls[1]:
        selected_scenarios = st.multiselect("Scenario", scenarios, default=[])
    with controls[2]:
        selected_countries = st.multiselect("Country", countries, default=[])
    with controls[3]:
        max_rows = st.number_input("Rows", min_value=25, max_value=1000, value=200, step=25)

    filtered = unique_tx.copy()
    if selected_scenarios:
        filtered = filtered[_series(filtered, "scenario", "").astype(str).isin(selected_scenarios)]
    if selected_countries:
        filtered = filtered[_series(filtered, "geo_country", "").astype(str).isin(selected_countries)]
    if search.strip():
        needle = search.strip().lower()
        search_columns = [
            col
            for col in (
                "tx_id",
                "input_address",
                "output_address",
                "input_addresses",
                "output_addresses",
                "src_ip",
                "dst_ip",
                "asn",
                "scenario",
                "geo_country",
            )
            if col in filtered.columns
        ]
        mask = pd.Series(False, index=filtered.index)
        for column in search_columns:
            mask |= filtered[column].map(_safe_text).str.lower().str.contains(needle, regex=False, na=False)
        filtered = filtered[mask]
    filtered = filtered.sort_values("timestamp", ascending=False, na_position="last").head(int(max_rows)).reset_index(drop=True)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        _metric_card("Matches", _fmt_num(len(filtered)), f"of {len(unique_tx):,} unique transactions", "blue")
    with metric_cols[1]:
        _metric_card("Volume", _fmt_btc(pd.to_numeric(_series(filtered, "input_value"), errors="coerce").fillna(0).sum()), "current results", "green")
    with metric_cols[2]:
        _metric_card("Countries", _fmt_num(_series(filtered, "geo_country", "").replace("", pd.NA).nunique()), "current results", "orange")
    with metric_cols[3]:
        _metric_card("Latest block", _fmt_num(pd.to_numeric(_series(filtered, "block_height"), errors="coerce").max()), "current results", "blue")

    if filtered.empty:
        st.markdown('<div class="info-banner">No transactions match those search filters.</div>', unsafe_allow_html=True)
        return
    _dataframe(_transaction_table(filtered), hide_index=True, height=350)
    tx_ids = filtered["tx_id"].astype(str).tolist()
    selected_tx_id = st.selectbox("Selected transaction", tx_ids, format_func=lambda txid: _short(txid, 16, 12))
    selected_rows = unique_tx[unique_tx["tx_id"].astype(str) == selected_tx_id]
    if selected_rows.empty:
        return
    selected = selected_rows.iloc[0]
    st.divider()
    _section("Transaction evidence", _short(selected_tx_id, 18, 14), "Raw normalized fields are retained by the pipeline; expanded input/output lists are shown below.")
    detail_cols = st.columns(5)
    with detail_cols[0]:
        _metric_card("Input value", _fmt_btc(selected.get("input_value", 0)), "observed", "blue")
    with detail_cols[1]:
        _metric_card("Output value", _fmt_btc(selected.get("output_value", 0)), "observed", "green")
    with detail_cols[2]:
        _metric_card("Fee", _fmt_btc(selected.get("fee", 0), 6), "normalized", "orange")
    with detail_cols[3]:
        _metric_card("Block", _fmt_num(selected.get("block_height", 0)), "chain height", "blue")
    with detail_cols[4]:
        _metric_card("Scenario", _safe_text(selected.get("scenario", "unknown")), "source label", "red")

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="detail-card"><div class="detail-label">Inputs</div></div>', unsafe_allow_html=True)
        inputs = selected.get("inputs", selected.get("input_addresses", []))
        input_rows = []
        if isinstance(inputs, list):
            for value in inputs:
                if isinstance(value, dict):
                    input_rows.append(value)
                else:
                    input_rows.append({"address": value})
        if not input_rows:
            input_rows = [{"address": selected.get("input_address", "unknown")}]
        _dataframe(pd.DataFrame(input_rows), hide_index=True)
    with right:
        st.markdown('<div class="detail-card"><div class="detail-label">Outputs</div></div>', unsafe_allow_html=True)
        outputs = selected.get("outputs", selected.get("output_addresses", []))
        output_rows = []
        if isinstance(outputs, list):
            for value in outputs:
                if isinstance(value, dict):
                    output_rows.append(value)
                else:
                    output_rows.append({"address": value})
        if not output_rows:
            output_rows = [{"address": selected.get("output_address", "unknown")}]
        _dataframe(pd.DataFrame(output_rows), hide_index=True)

    metadata = {
        key: _safe_text(selected.get(key))
        for key in ("timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "geo_country", "asn", "script_type", "labels")
        if key in selected
    }
    st.markdown('<div class="detail-card"><div class="detail-label">Network metadata</div></div>', unsafe_allow_html=True)
    st.json(metadata, expanded=False)


def _render_network(result: Any) -> None:
    graph = getattr(result, "graph", nx.MultiDiGraph())
    risk = _risk_frame(result)
    transactions = getattr(result, "transactions", pd.DataFrame())
    if graph is None or graph.number_of_nodes() == 0:
        _section("Network intelligence", "No graph available", "The graph view is built from normalized input/output address edges.")
        st.info("No graph nodes were produced by the pipeline.")
        return

    _section("Network intelligence", "Trace the local transaction graph", "Select a center address to inspect its immediate neighborhood and the time pattern of the dataset.")
    risk_addresses = risk["address"].tolist() if not risk.empty and "address" in risk else []
    degree_addresses = [node for node, _ in sorted(graph.degree, key=lambda pair: pair[1], reverse=True)]
    options = list(dict.fromkeys(risk_addresses + degree_addresses))
    controls = st.columns([2, .8, .9, 1])
    with controls[0]:
        center = st.selectbox("Center address", options, format_func=lambda value: _short(value, 16, 11))
    with controls[1]:
        depth = st.selectbox("Hops", [1, 2], index=0)
    with controls[2]:
        max_nodes = st.number_input("Nodes", min_value=15, max_value=120, value=55, step=5)
    with controls[3]:
        graph_search = st.text_input("Jump to address", placeholder="prefix…")
    if graph_search.strip():
        matches = [node for node in options if graph_search.strip().lower() in str(node).lower()]
        if matches:
            center = st.selectbox("Matching address", matches, format_func=lambda value: _short(value, 16, 11), key="matching_address")
        else:
            st.caption("No address matched that prefix; showing the selected center.")

    selected_risk = risk[risk["address"] == center]
    center_score = _float(selected_risk.iloc[0].get("risk_score")) if not selected_risk.empty else 0.0
    center_level = _safe_text(selected_risk.iloc[0].get("risk_level")) if not selected_risk.empty else "Unscored"
    graph_fig, edge_rows = _network_figure(graph, risk, center, int(depth), int(max_nodes))
    if graph_fig is not None:
        _plotly_chart(graph_fig)
    else:
        st.info("Plotly is not installed; install project dependencies to render the interactive network view.")

    view_cols = st.columns(4)
    with view_cols[0]:
        _metric_card("Center risk", f"{center_score:.1f}/100", center_level, "red" if center_score >= 60 else "blue")
    with view_cols[1]:
        _metric_card("Neighbors", _fmt_num(max(0, graph.degree(center))), f"{depth}-hop view", "blue")
    with view_cols[2]:
        _metric_card("Visible nodes", _fmt_num(len(set(edge_rows["from"]) | set(edge_rows["to"])) if not edge_rows.empty else 1), "rendered subgraph", "green")
    with view_cols[3]:
        _metric_card("Visible edges", _fmt_num(len(edge_rows)), "capped for readability", "orange")

    if not edge_rows.empty:
        with st.expander("Show visible edge records"):
            edge_display = edge_rows.copy()
            edge_display["from"] = edge_display["from"].map(_short)
            edge_display["to"] = edge_display["to"].map(_short)
            edge_display["value_btc"] = edge_display["value_btc"].round(8)
            _dataframe(edge_display, hide_index=True)

    st.write("")
    _section("Timeline", "Transaction activity pulse", "Use the graph for topology and the timeline for temporal concentration.")
    timeline_fig, timeline = _timeline_chart(transactions, risk)
    if timeline_fig is not None:
        _plotly_chart(timeline_fig)
    elif not timeline.empty:
        st.line_chart(timeline.set_index("bucket")[["volume_btc", "transactions"]])
    else:
        st.info("No parseable timestamps are available for a timeline.")


def main() -> None:
    st.set_page_config(page_title="BTC Trace · Analyst Console", page_icon="₿", layout="wide", initial_sidebar_state="expanded")
    _apply_optional_theme()
    page, source, source_label, contamination, source_kind = _render_sidebar()
    _render_india_masthead()

    if source_kind == "path":
        if source is None or not Path(source).exists():
            st.markdown('<div class="hero"><div class="hero-kicker">Data source required</div><div class="hero-title">Connect a local dataset to begin.</div><p class="hero-copy">Choose a workspace path or upload a CSV, JSON, or XML export from the sidebar.</p></div>', unsafe_allow_html=True)
            st.stop()
    elif source is None:
        st.markdown('<div class="hero"><div class="hero-kicker">Data source required</div><div class="hero-title">Upload a dataset to begin.</div><p class="hero-copy">The console accepts the same offline CSV, JSON, and XML records supported by the analytics package.</p></div>', unsafe_allow_html=True)
        st.stop()

    try:
        with st.spinner("Running local analytics pipeline…"):
            cache_version = int(Path(source).stat().st_mtime_ns) if source_kind == "path" else 0
            result = _run_pipeline(
                str(source) if source_kind == "path" else source,
                contamination,
                cache_version,
            )
    except Exception as exc:
        st.error(f"Unable to analyse dataset: {exc}")
        st.caption("Check that the selected file follows the CSV, JSON, or XML transaction schema.")
        st.stop()

    transactions = getattr(result, "transactions", pd.DataFrame())
    risk = _risk_frame(result)
    _render_hero(page, source_label, transactions, risk)

    if page == "Overview":
        _render_overview(result)
    elif page == "Alerts":
        _render_alerts(result)
    elif page == "Entities":
        _render_entities(result)
    elif page == "Transactions":
        _render_transactions(result)
    else:
        _render_network(result)


if __name__ == "__main__":
    main()

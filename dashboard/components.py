"""Reusable Streamlit components for the BTC-Trace security dashboard.

The helpers in this module deliberately use Streamlit primitives and small
HTML fragments only.  They can be adopted incrementally by dashboard views
without requiring a component server, a charting package, or a front-end
build step.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape
from math import isfinite
from numbers import Number
from pathlib import Path
from typing import Any, Final

import streamlit as st


RISK_LEVELS: Final[tuple[str, ...]] = ("critical", "high", "medium", "low")
TONE_NAMES: Final[set[str]] = {
    "critical",
    "high",
    "medium",
    "low",
    "success",
    "info",
    "warning",
    "danger",
    "neutral",
}

RISK_TABLE_COLUMNS: Final[tuple[str, ...]] = (
    "address",
    "risk_score",
    "risk_level",
    "anomaly_score",
    "explanation",
    "entity_id",
    "entity_size",
)
ALERT_TABLE_COLUMNS: Final[tuple[str, ...]] = RISK_TABLE_COLUMNS
ENTITY_TABLE_COLUMNS: Final[tuple[str, ...]] = ("entity_id", "address", "entity_size")
TRANSACTION_TABLE_COLUMNS: Final[tuple[str, ...]] = (
    "tx_id",
    "timestamp",
    "input_address",
    "output_address",
    "input_value",
    "output_value",
    "fee",
    "block_height",
)


@dataclass(frozen=True)
class KpiMetric:
    """Input model accepted by :func:`render_kpi_grid`."""

    label: str
    value: Any
    detail: str | None = None
    delta: str | None = None
    tone: str = "neutral"
    icon: str | None = None


KPI = KpiMetric


def _write(markup: str) -> None:
    """Write a trusted component fragment using the compatible Streamlit API."""

    st.markdown(markup, unsafe_allow_html=True)


def _tone(value: Any, fallback: str = "neutral") -> str:
    candidate = str(value or fallback).strip().lower().replace(" ", "-")
    return candidate if candidate in TONE_NAMES else fallback


def _missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(value != value)  # Handles float NaN without importing pandas.
    except (TypeError, ValueError):
        return False


def _text(value: Any, fallback: str = "—") -> str:
    if _missing(value):
        return fallback
    return str(value)


def _html_text(value: Any, fallback: str = "—") -> str:
    return escape(_text(value, fallback))


def _display_number(value: Any, decimals: int = 0) -> str:
    if _missing(value):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _text(value)
    if not isfinite(number):
        return "—"
    if decimals == 0 and number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.{decimals}f}"


def _display_value(value: Any) -> str:
    """Give numeric KPI values readable grouping without changing caller text."""

    if isinstance(value, Number) and not isinstance(value, bool):
        decimals = 2 if isinstance(value, float) and not value.is_integer() else 0
        return _display_number(value, decimals=decimals)
    return _text(value)


def format_btc(value: Any, decimals: int = 8) -> str:
    """Format an amount in BTC while keeping precision visible for small values."""

    if _missing(value):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _text(value)
    if not isfinite(number):
        return "—"
    rendered = f"{number:,.{decimals}f}".rstrip("0").rstrip(".")
    return f"{rendered or '0'} BTC"


def format_score(value: Any) -> str:
    """Format the 0-100 risk/anomaly scores used by the analytics pipeline."""

    return _display_number(value, decimals=2)


def format_address(value: Any, head: int = 8, tail: int = 6) -> str:
    """Keep a wallet address readable in compact cards without losing its ends."""

    value_text = _text(value)
    if value_text == "—" or len(value_text) <= head + tail + 3:
        return value_text
    return f"{value_text[:head]}…{value_text[-tail:]}"


def badge_html(label: Any, tone: str = "neutral", icon: str | None = None) -> str:
    """Return a safe badge fragment for use inside another component."""

    badge_tone = _tone(tone)
    icon_markup = (
        f'<span aria-hidden="true">{escape(str(icon))}</span>' if icon else ""
    )
    return (
        f'<span class="so-badge so-badge--{badge_tone}">'
        f"{icon_markup}{_html_text(label)}"
        "</span>"
    )


def risk_badge_html(level: Any) -> str:
    """Return a badge whose color follows a pipeline risk level."""

    level_text = _text(level, "Unknown")
    tone = _tone(level_text, "neutral")
    if tone not in RISK_LEVELS:
        tone = "neutral"
    return badge_html(level_text, tone=tone)


def render_badge(label: Any, tone: str = "neutral", icon: str | None = None) -> None:
    """Render a compact status badge."""

    _write(badge_html(label, tone=tone, icon=icon))


def render_risk_badge(level: Any) -> None:
    """Render a badge for ``risk_level`` values from an ``AnalysisResult``."""

    _write(risk_badge_html(level))


def render_page_header(
    title: str,
    description: str | None = None,
    *,
    eyebrow: str = "SECURITY OPERATIONS",
    status: str | None = None,
    status_tone: str = "success",
) -> None:
    """Render a high-contrast page heading with an optional status badge."""

    status_markup = (
        f'<div class="so-page-header__meta">{badge_html(status, status_tone, "●")}</div>'
        if status
        else ""
    )
    description_markup = (
        f'<p class="so-page-description">{_html_text(description)}</p>'
        if description
        else ""
    )
    _write(
        '<header class="so-page-header">'
        '<div class="so-page-header__copy">'
        f'<p class="so-eyebrow">{_html_text(eyebrow)}</p>'
        f'<h1 class="so-page-title">{_html_text(title)}</h1>'
        f"{description_markup}"
        "</div>"
        f"{status_markup}"
        "</header>"
    )


def render_section_header(
    title: str,
    subtitle: str | None = None,
    *,
    eyebrow: str | None = None,
    badge: str | None = None,
    badge_tone: str = "neutral",
) -> None:
    """Render a section title with optional context and count/status badge."""

    eyebrow_markup = (
        f'<p class="so-eyebrow">{_html_text(eyebrow)}</p>' if eyebrow else ""
    )
    subtitle_markup = (
        f'<p class="so-section-header__subtitle">{_html_text(subtitle)}</p>'
        if subtitle
        else ""
    )
    badge_markup = (
        f'<div class="so-section-header__meta">{badge_html(badge, badge_tone)}</div>'
        if badge
        else ""
    )
    _write(
        '<div class="so-section-header">'
        "<div>"
        f"{eyebrow_markup}"
        f'<h2 class="so-section-header__title">{_html_text(title)}</h2>'
        f"{subtitle_markup}"
        "</div>"
        f"{badge_markup}"
        "</div>"
    )


def render_kpi_card(
    label: str,
    value: Any,
    *,
    detail: str | None = None,
    delta: Any | None = None,
    tone: str = "neutral",
    icon: str | None = None,
) -> None:
    """Render one dashboard KPI card with a semantic accent tone."""

    card_tone = _tone(tone)
    icon_markup = (
        f'<span class="so-kpi-card__icon" aria-hidden="true">{escape(str(icon))}</span>'
        if icon
        else ""
    )
    detail_markup = (
        f'<span class="so-kpi-card__detail">{_html_text(detail)}</span>'
        if detail
        else '<span class="so-kpi-card__detail">&nbsp;</span>'
    )
    delta_markup = (
        f'<span class="so-kpi-card__delta">{_html_text(delta)}</span>'
        if delta is not None
        else ""
    )
    _write(
        f'<article class="so-kpi-card so-kpi-card--{card_tone}">'
        f'<div class="so-kpi-card__top">{icon_markup}'
        f'<span>{_html_text(label)}</span></div>'
        f'<div class="so-kpi-card__value">{_html_text(_display_value(value))}</div>'
        f'<div class="so-kpi-card__footer">{detail_markup}{delta_markup}</div>'
        "</article>"
    )


def _coerce_metric(metric: KpiMetric | Mapping[str, Any]) -> KpiMetric:
    if isinstance(metric, KpiMetric):
        return metric
    if isinstance(metric, Mapping):
        return KpiMetric(
            label=str(metric.get("label", "Metric")),
            value=metric.get("value", "—"),
            detail=metric.get("detail"),
            delta=metric.get("delta"),
            tone=str(metric.get("tone", "neutral")),
            icon=metric.get("icon"),
        )
    raise TypeError("metrics must contain KpiMetric instances or mappings")


def render_kpi_grid(
    metrics: Sequence[KpiMetric | Mapping[str, Any]], *, columns: int = 4
) -> None:
    """Render KPI cards in responsive Streamlit columns."""

    if not metrics:
        return
    column_count = max(1, min(int(columns), len(metrics)))
    for start in range(0, len(metrics), column_count):
        row = [_coerce_metric(metric) for metric in metrics[start : start + column_count]]
        slots = st.columns(len(row))
        for slot, metric in zip(slots, row):
            with slot:
                render_kpi_card(
                    metric.label,
                    metric.value,
                    detail=metric.detail,
                    delta=metric.delta,
                    tone=metric.tone,
                    icon=metric.icon,
                )


def render_empty_state(
    message: str,
    *,
    title: str = "Nothing to investigate",
    icon: str = "✓",
) -> None:
    """Render a calm, explanatory empty state instead of a blank panel."""

    _write(
        '<div class="so-empty-state">'
        f'<div aria-hidden="true" style="font-size:1.5rem;margin-bottom:.45rem">{escape(icon)}</div>'
        f'<p class="so-empty-state__title">{_html_text(title)}</p>'
        f'<p class="so-empty-state__message">{_html_text(message)}</p>'
        "</div>"
    )


def render_sidebar_brand(
    container: Any = None,
    name: str = "Trace-X AI",
    subtitle: str = "Evidence Linked Bitcoin Transaction Intelligence",
    mark: str = "₿",
    emblem_path: str | Path | None = None,
) -> None:
    """Render the India GovTech product identity in a Streamlit container.

    The emblem is loaded from the repository instead of a remote URL so the
    application remains usable on an isolated judging network.  The visual
    treatment labels the build as an SIH prototype and does not imply official
    government endorsement.
    """

    target = container if container is not None else st.sidebar
    path = Path(emblem_path) if emblem_path else Path(__file__).parent / "assets" / "emblem-of-india.svg"
    if path.exists():
        try:
            target.image(str(path), width=54)
        except TypeError:
            target.image(str(path), use_column_width=False, width=54)
    else:
        target.markdown(
            f'<div class="so-sidebar-brand__mark" aria-hidden="true">{escape(mark)}</div>',
            unsafe_allow_html=True,
        )
    target.markdown(
        '<div class="so-sidebar-brand">'
        '<p class="so-sidebar-brand__gov">GOVERNMENT OF INDIA</p>'
        f'<p class="so-sidebar-brand__name">{_html_text(name)}</p>'
        f'<p class="so-sidebar-brand__subtitle">{_html_text(subtitle)}</p>'
        '<div class="so-sidebar-brand__rule" aria-hidden="true"></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def _available_columns(data: Any, preferred: Sequence[str] | None) -> list[str]:
    available = list(getattr(data, "columns", ()))
    if not preferred:
        return available
    return [column for column in preferred if column in available]


def _table_view(data: Any, columns: Sequence[str] | None, limit: int | None) -> Any:
    selected = _available_columns(data, columns)
    if selected and hasattr(data, "loc"):
        view = data.loc[:, selected].copy()
    else:
        view = data.copy() if hasattr(data, "copy") else data
    if limit is not None and hasattr(view, "head"):
        view = view.head(max(0, int(limit)))
    return view


def _column_config(kind: str) -> dict[str, Any]:
    """Build optional native column formatting, with a safe old-version fallback."""

    config_namespace = getattr(st, "column_config", None)
    if config_namespace is None:
        return {}
    try:
        config: dict[str, Any] = {}
        text_column = getattr(config_namespace, "TextColumn", None)
        number_column = getattr(config_namespace, "NumberColumn", None)
        progress_column = getattr(config_namespace, "ProgressColumn", None)
        datetime_column = getattr(config_namespace, "DatetimeColumn", None)
        if text_column:
            config["address"] = text_column("Address", width="medium")
            config["risk_level"] = text_column("Risk level", width="small")
            config["explanation"] = text_column("Why it surfaced", width="large")
            config["entity_id"] = text_column("Entity", width="small")
            config["tx_id"] = text_column("Transaction", width="medium")
            config["input_address"] = text_column("From", width="medium")
            config["output_address"] = text_column("To", width="medium")
        if number_column:
            config["entity_size"] = number_column("Cluster size", format="%d")
            config["block_height"] = number_column("Block", format="%d")
            for amount in ("input_value", "output_value", "fee"):
                config[amount] = number_column(amount.replace("_", " ").title(), format="%.8f")
            config["anomaly_score"] = number_column("Anomaly score", format="%.2f")
        if progress_column and kind in {"risk", "alerts"}:
            config["risk_score"] = progress_column(
                "Risk score", format="%.2f", min_value=0, max_value=100
            )
        elif number_column and kind in {"risk", "alerts"}:
            config["risk_score"] = number_column("Risk score", format="%.2f")
        if datetime_column:
            config["timestamp"] = datetime_column("Timestamp", format="YYYY-MM-DD HH:mm")
        return config
    except (AttributeError, TypeError, ValueError):
        # Streamlit's column_config surface has grown over time; tables still
        # render correctly when a particular formatting option is unavailable.
        return {}


def render_data_table(
    data: Any,
    *,
    columns: Sequence[str] | None = None,
    limit: int | None = None,
    height: int | None = None,
    kind: str = "generic",
) -> None:
    """Render a dataframe with consistent sizing and optional native formatting."""

    view = _table_view(data, columns, limit)
    # ``width='stretch'`` is the current Streamlit API.  The fallback below
    # keeps the helpers usable with older versions that only expose the
    # deprecated ``use_container_width`` flag.
    kwargs: dict[str, Any] = {"width": "stretch", "hide_index": True}
    if height is not None:
        kwargs["height"] = int(height)
    config = _column_config(kind)
    if config:
        kwargs["column_config"] = config
    try:
        st.dataframe(view, **kwargs)
    except TypeError:
        # Keep support for Streamlit versions that predate one of the optional
        # dataframe keywords while preserving the same data view.
        kwargs.pop("column_config", None)
        kwargs.pop("width", None)
        kwargs["use_container_width"] = True
        try:
            st.dataframe(view, **kwargs)
        except TypeError:
            kwargs.pop("use_container_width", None)
            st.dataframe(view, **kwargs)


def render_risk_table(data: Any, *, limit: int | None = 15, height: int | None = None) -> None:
    """Render the ranked risk columns produced by ``AnalyticsPipeline``."""

    render_data_table(
        data,
        columns=RISK_TABLE_COLUMNS,
        limit=limit,
        height=height,
        kind="risk",
    )


def render_alert_table(data: Any, *, limit: int | None = 100, height: int | None = None) -> None:
    """Render the explainable alert subset produced by ``ranked_alerts``."""

    render_data_table(
        data,
        columns=ALERT_TABLE_COLUMNS,
        limit=limit,
        height=height,
        kind="alerts",
    )


def render_entity_table(data: Any, *, limit: int | None = None, height: int | None = None) -> None:
    """Render connected entity cluster membership."""

    render_data_table(
        data,
        columns=ENTITY_TABLE_COLUMNS,
        limit=limit,
        height=height,
        kind="entities",
    )


def render_transaction_table(
    data: Any, *, limit: int | None = None, height: int | None = None
) -> None:
    """Render normalized transaction flow fields from the analytics result."""

    render_data_table(
        data,
        columns=TRANSACTION_TABLE_COLUMNS,
        limit=limit,
        height=height,
        kind="transactions",
    )


def _records(data: Any, limit: int | None) -> list[Mapping[str, Any]]:
    if data is None:
        return []
    view = data.head(limit) if limit is not None and hasattr(data, "head") else data
    if hasattr(view, "to_dict"):
        return list(view.to_dict("records"))
    if isinstance(view, Sequence) and not isinstance(view, (str, bytes)):
        return [record for record in view if isinstance(record, Mapping)]
    return []


def render_alert_cards(data: Any, *, limit: int = 6) -> None:
    """Render a compact card stack for the highest-priority alerts."""

    records = _records(data, limit)
    if not records:
        render_empty_state(
            "No addresses crossed the current triage threshold.",
            title="No active alerts",
        )
        return
    for record in records:
        level = _text(record.get("risk_level"), "Unknown")
        tone = _tone(level, "neutral")
        if tone not in RISK_LEVELS:
            tone = "neutral"
        score = format_score(record.get("risk_score"))
        entity = _text(record.get("entity_id"))
        entity_size = _display_number(record.get("entity_size"))
        _write(
            f'<article class="so-alert-card so-alert-card--{tone}">'
            '<div class="so-alert-card__top">'
            f'<span class="so-alert-card__address" title="{_html_text(record.get("address"))}">'
            f"{_html_text(format_address(record.get('address')))}</span>"
            f"{risk_badge_html(level)}"
            "</div>"
            f'<p class="so-alert-card__reason">{_html_text(record.get("explanation"), "No explanation recorded.")}</p>'
            '<div class="so-alert-card__bottom">'
            f"<span>score {escape(score)}</span>"
            f"<span>{_html_text(entity)} · {escape(entity_size)} address(es)</span>"
            "</div>"
            "</article>"
        )


__all__ = [
    "ALERT_TABLE_COLUMNS",
    "ENTITY_TABLE_COLUMNS",
    "KPI",
    "KpiMetric",
    "RISK_LEVELS",
    "RISK_TABLE_COLUMNS",
    "TRANSACTION_TABLE_COLUMNS",
    "badge_html",
    "format_address",
    "format_btc",
    "format_score",
    "render_alert_cards",
    "render_alert_table",
    "render_badge",
    "render_data_table",
    "render_empty_state",
    "render_entity_table",
    "render_kpi_card",
    "render_kpi_grid",
    "render_page_header",
    "render_risk_badge",
    "render_risk_table",
    "render_section_header",
    "render_sidebar_brand",
    "render_transaction_table",
    "risk_badge_html",
]

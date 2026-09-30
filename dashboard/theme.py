"""Visual tokens and CSS for the Bitcoin monitoring dashboard.

The dashboard is intentionally offline-first, so the theme does not fetch web
fonts, icons, or any other remote asset.  ``apply_theme`` can be called near
the top of any Streamlit view and is safe to call again on reruns.
"""

from __future__ import annotations

from typing import Final, Mapping

import streamlit as st


COLORS: Final[Mapping[str, str]] = {
    "ink": "#10233f",
    "canvas": "#f4f7fb",
    "surface": "#ffffff",
    "surface_elevated": "#ffffff",
    "surface_hover": "#eef4fb",
    "border": "#d9e2ee",
    "border_strong": "#b8c9dc",
    "text": "#10233f",
    "text_soft": "#40536b",
    "muted": "#6b7e95",
    "cyan": "#174f92",
    "cyan_deep": "#0f3d77",
    "green": "#138808",
    "amber": "#d97706",
    "orange": "#e87817",
    "red": "#be3144",
    "purple": "#6d4bc2",
    "blue": "#155eaa",
}


RISK_COLORS: Final[Mapping[str, str]] = {
    "critical": COLORS["red"],
    "high": COLORS["orange"],
    "medium": COLORS["amber"],
    "low": COLORS["green"],
    "unknown": COLORS["muted"],
}


STATUS_COLORS: Final[Mapping[str, str]] = {
    "success": COLORS["green"],
    "info": COLORS["blue"],
    "warning": COLORS["amber"],
    "danger": COLORS["red"],
    "neutral": COLORS["muted"],
}


DASHBOARD_CSS: Final[str] = r"""
/* -------------------------------------------------------------------------
   BTC-Trace security operations theme
   ------------------------------------------------------------------------- */
:root {
    --so-ink: #071019;
    --so-canvas: #0a1119;
    --so-surface: #101b25;
    --so-surface-elevated: #142433;
    --so-surface-hover: #192d3e;
    --so-border: #263b4d;
    --so-border-strong: #35536a;
    --so-text: #edf5f7;
    --so-text-soft: #c4d5dd;
    --so-muted: #8299aa;
    --so-cyan: #5ce1e6;
    --so-cyan-deep: #1ba6b5;
    --so-green: #59d9a4;
    --so-amber: #f3c969;
    --so-orange: #ff9b63;
    --so-red: #ff647d;
    --so-purple: #ae9cf5;
    --so-blue: #70c9ff;
    --so-radius: 12px;
    --so-radius-sm: 8px;
    --so-shadow: 0 12px 32px rgba(0, 0, 0, 0.20);
    --so-font: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
    --so-mono: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

html, body, [class*="css"] {
    font-family: var(--so-font);
}

.stApp {
    color: var(--so-text);
    background:
        radial-gradient(circle at 88% -10%, rgba(27, 166, 181, 0.12), transparent 34rem),
        radial-gradient(circle at 4% 18%, rgba(112, 201, 255, 0.06), transparent 26rem),
        var(--so-canvas);
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

[data-testid="stHeader"] {
    background: rgba(10, 17, 25, 0.72);
}

[data-testid="stToolbar"] {
    right: 1rem;
}

.block-container {
    max-width: 1600px;
    padding: 2.2rem 3rem 3.5rem;
}

/* Sidebar ---------------------------------------------------------------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1721 0%, #09121b 100%);
    border-right: 1px solid var(--so-border);
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1.6rem 1.15rem 2rem;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--so-text-soft);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: var(--so-muted);
}

/* Typography -------------------------------------------------------------- */
h1, h2, h3, h4 {
    color: var(--so-text);
    font-weight: 650;
    letter-spacing: -0.025em;
}

h1 {
    font-size: clamp(2rem, 3vw, 3rem);
    line-height: 1.08;
}

h2 {
    font-size: clamp(1.35rem, 2vw, 1.75rem);
}

h3 {
    font-size: 1.1rem;
}

p, li {
    color: var(--so-text-soft);
}

code, pre, .so-mono {
    font-family: var(--so-mono);
}

/* Native Streamlit controls ------------------------------------------------ */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] {
    color: var(--so-text);
    background: var(--so-surface);
    border-color: var(--so-border);
    border-radius: var(--so-radius-sm);
}

div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="textarea"]:focus-within {
    border-color: var(--so-cyan);
    box-shadow: 0 0 0 1px var(--so-cyan), 0 0 0 4px rgba(92, 225, 230, 0.10);
}

div[data-baseweb="select"] svg {
    fill: var(--so-muted);
}

.stButton > button {
    color: var(--so-text);
    background: var(--so-surface-elevated);
    border: 1px solid var(--so-border-strong);
    border-radius: var(--so-radius-sm);
    font-weight: 600;
    transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
}

.stButton > button:hover {
    color: var(--so-text);
    background: var(--so-surface-hover);
    border-color: var(--so-cyan);
    transform: translateY(-1px);
}

.stButton > button:focus {
    box-shadow: 0 0 0 3px rgba(92, 225, 230, 0.18);
}

[data-testid="stFileUploader"] section {
    background: rgba(16, 27, 37, 0.75);
    border: 1px dashed var(--so-border-strong);
    border-radius: var(--so-radius);
}

[data-testid="stAlert"] {
    background: var(--so-surface);
    border: 1px solid var(--so-border);
    border-radius: var(--so-radius-sm);
}

/* The custom reusable building blocks ------------------------------------ */
.so-page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1.5rem;
    margin: 0 0 2rem;
    padding-bottom: 1.35rem;
    border-bottom: 1px solid var(--so-border);
}

.so-page-header__copy {
    min-width: 0;
}

.so-page-header__meta {
    flex: 0 0 auto;
    padding-top: 0.3rem;
}

.so-eyebrow {
    margin: 0 0 0.55rem;
    color: var(--so-cyan);
    font-family: var(--so-mono);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    line-height: 1.2;
    text-transform: uppercase;
}

.so-page-title {
    margin: 0;
    color: var(--so-text);
    font-size: clamp(1.8rem, 3vw, 2.65rem);
    font-weight: 700;
    letter-spacing: -0.045em;
    line-height: 1.08;
}

.so-page-description {
    max-width: 760px;
    margin: 0.7rem 0 0;
    color: var(--so-muted);
    font-size: 0.97rem;
    line-height: 1.55;
}

.so-section-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1rem;
    margin: 1.85rem 0 0.85rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid var(--so-border);
}

.so-section-header__title {
    margin: 0;
    color: var(--so-text);
    font-size: 1.1rem;
    font-weight: 650;
    letter-spacing: -0.015em;
}

.so-section-header__subtitle {
    margin: 0.32rem 0 0;
    color: var(--so-muted);
    font-size: 0.82rem;
    line-height: 1.45;
}

.so-section-header__meta {
    flex: 0 0 auto;
}

.so-kpi-card {
    position: relative;
    min-height: 132px;
    overflow: hidden;
    padding: 1.1rem 1.15rem 1rem;
    background: linear-gradient(145deg, rgba(20, 36, 51, 0.96), rgba(16, 27, 37, 0.96));
    border: 1px solid var(--so-border);
    border-radius: var(--so-radius);
    box-shadow: var(--so-shadow);
}

.so-kpi-card::after {
    position: absolute;
    right: -2.8rem;
    bottom: -3.6rem;
    width: 8rem;
    height: 8rem;
    border: 1px solid currentColor;
    border-radius: 50%;
    opacity: 0.10;
    content: "";
}

.so-kpi-card--critical { color: var(--so-red); border-top-color: var(--so-red); }
.so-kpi-card--high { color: var(--so-orange); border-top-color: var(--so-orange); }
.so-kpi-card--medium { color: var(--so-amber); border-top-color: var(--so-amber); }
.so-kpi-card--low,
.so-kpi-card--success { color: var(--so-green); border-top-color: var(--so-green); }
.so-kpi-card--info { color: var(--so-blue); border-top-color: var(--so-blue); }
.so-kpi-card--neutral { color: var(--so-cyan); border-top-color: var(--so-cyan); }

.so-kpi-card__top {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--so-muted);
    font-family: var(--so-mono);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    line-height: 1.2;
    text-transform: uppercase;
}

.so-kpi-card__icon {
    display: inline-grid;
    width: 1.35rem;
    height: 1.35rem;
    place-items: center;
    color: currentColor;
    font-size: 0.9rem;
}

.so-kpi-card__value {
    position: relative;
    z-index: 1;
    margin-top: 0.72rem;
    color: var(--so-text);
    font-size: clamp(1.55rem, 2.5vw, 2.05rem);
    font-weight: 700;
    letter-spacing: -0.045em;
    line-height: 1;
}

.so-kpi-card__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.65rem;
    margin-top: 0.7rem;
}

.so-kpi-card__detail {
    overflow: hidden;
    color: var(--so-muted);
    font-size: 0.75rem;
    line-height: 1.35;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.so-kpi-card__delta {
    flex: 0 0 auto;
    color: currentColor;
    font-family: var(--so-mono);
    font-size: 0.72rem;
    font-weight: 700;
}

.so-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.27rem 0.55rem;
    border: 1px solid currentColor;
    border-radius: 999px;
    color: var(--so-muted);
    background: rgba(130, 153, 170, 0.10);
    font-family: var(--so-mono);
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    line-height: 1;
    text-transform: uppercase;
    white-space: nowrap;
}

.so-badge--critical { color: var(--so-red); background: rgba(255, 100, 125, 0.11); }
.so-badge--high { color: var(--so-orange); background: rgba(255, 155, 99, 0.11); }
.so-badge--medium,
.so-badge--warning { color: var(--so-amber); background: rgba(243, 201, 105, 0.11); }
.so-badge--low,
.so-badge--success { color: var(--so-green); background: rgba(89, 217, 164, 0.11); }
.so-badge--info { color: var(--so-blue); background: rgba(112, 201, 255, 0.11); }
.so-badge--danger { color: var(--so-red); background: rgba(255, 100, 125, 0.11); }

.so-alert-card {
    margin: 0.7rem 0;
    padding: 0.95rem 1rem;
    background: rgba(16, 27, 37, 0.86);
    border: 1px solid var(--so-border);
    border-left: 3px solid var(--so-border-strong);
    border-radius: var(--so-radius-sm);
}

.so-alert-card--critical { border-left-color: var(--so-red); }
.so-alert-card--high { border-left-color: var(--so-orange); }
.so-alert-card--medium { border-left-color: var(--so-amber); }
.so-alert-card--low { border-left-color: var(--so-green); }

.so-alert-card__top,
.so-alert-card__bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.8rem;
}

.so-alert-card__address {
    overflow: hidden;
    color: var(--so-text);
    font-family: var(--so-mono);
    font-size: 0.82rem;
    font-weight: 650;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.so-alert-card__reason {
    margin: 0.65rem 0;
    color: var(--so-text-soft);
    font-size: 0.82rem;
    line-height: 1.45;
}

.so-alert-card__bottom {
    color: var(--so-muted);
    font-family: var(--so-mono);
    font-size: 0.68rem;
}

.so-empty-state {
    padding: 2.2rem 1.25rem;
    color: var(--so-muted);
    background: rgba(16, 27, 37, 0.55);
    border: 1px dashed var(--so-border-strong);
    border-radius: var(--so-radius);
    text-align: center;
}

.so-empty-state__title {
    margin: 0;
    color: var(--so-text-soft);
    font-size: 1rem;
    font-weight: 650;
}

.so-empty-state__message {
    margin: 0.4rem 0 0;
    color: var(--so-muted);
    font-size: 0.83rem;
}

.so-sidebar-brand {
    margin: 0 0 1.45rem;
    padding: 0.15rem 0 1.15rem;
    border-bottom: 1px solid var(--so-border);
}

.so-sidebar-brand__mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    margin-bottom: 0.7rem;
    color: var(--so-ink);
    background: var(--so-cyan);
    border-radius: 7px;
    font-size: 1.05rem;
    font-weight: 800;
}

.so-sidebar-brand__name {
    margin: 0;
    color: var(--so-text);
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.so-sidebar-brand__subtitle {
    margin: 0.3rem 0 0;
    color: var(--so-muted);
    font-size: 0.72rem;
    line-height: 1.45;
}

div[data-testid="stDataFrame"] {
    overflow: hidden;
    border: 1px solid var(--so-border);
    border-radius: var(--so-radius-sm);
}

@media (max-width: 900px) {
    .block-container { padding: 1.5rem 1.25rem 2.5rem; }
    .so-page-header { flex-direction: column; gap: 0.9rem; }
    .so-page-header__meta { padding-top: 0; }
}

@media (prefers-reduced-motion: reduce) {
    .stButton > button { transition: none; }
}

/* India GovTech presentation layer --------------------------------------- */
:root {
    --so-ink: #10233f;
    --so-canvas: #f4f7fb;
    --so-surface: #ffffff;
    --so-surface-elevated: #ffffff;
    --so-surface-hover: #eef4fb;
    --so-border: #d9e2ee;
    --so-border-strong: #b8c9dc;
    --so-text: #10233f;
    --so-text-soft: #40536b;
    --so-muted: #6b7e95;
    --so-cyan: #174f92;
    --so-cyan-deep: #0f3d77;
    --so-green: #138808;
    --so-amber: #d97706;
    --so-orange: #e87817;
    --so-red: #be3144;
    --so-purple: #6d4bc2;
    --so-blue: #155eaa;
    --so-shadow: 0 8px 24px rgba(16, 35, 63, 0.08);
}

.stApp {
    background: linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%);
}

[data-testid="stAppViewContainer"] { background: transparent; }
[data-testid="stHeader"] { background: rgba(247, 249, 252, .86); }
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #d6e0ec;
    box-shadow: 8px 0 28px rgba(16, 35, 63, .05);
}
[data-testid="stSidebar"] > div:first-child { padding: 1.2rem 1.05rem 2rem; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption { color: #647891; }
.block-container { max-width: 1560px; padding: 1.8rem 3rem 3.5rem; }

h1, h2, h3, h4 { color: #10233f; }
p, li { color: #40536b; }
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] {
    color: #10233f;
    background: #ffffff;
    border-color: #cbd8e7;
}
.stButton > button {
    color: #ffffff;
    background: #174f92;
    border-color: #174f92;
}
.stButton > button:hover { color: #ffffff; background: #0f3d77; border-color: #0f3d77; }
[data-testid="stFileUploader"] section { background: #f8fafc; border-color: #bdcbdd; }
div[data-testid="stDataFrame"] { border-color: #d6e0ec; background: #ffffff; }

.so-sidebar-brand { margin: .45rem 0 1.25rem; padding: 0 0 .95rem; border-bottom: 1px solid #e2e8f0; }
.so-sidebar-brand__gov {
    margin: 0 0 .35rem; color: #174f92; font-family: var(--so-mono);
    font-size: .58rem; font-weight: 800; letter-spacing: .12em;
}
.so-sidebar-brand__name { margin: 0; color: #10233f; font-size: 1rem; font-weight: 750; }
.so-sidebar-brand__subtitle { margin: .22rem 0 0; color: #6b7e95; font-size: .7rem; }
.so-sidebar-brand__rule {
    height: 3px; margin: .85rem 0 .55rem;
    background: linear-gradient(90deg, #ff9933 0 33%, #174f92 33% 66%, #138808 66% 100%);
    border-radius: 999px;
}
.so-sidebar-brand__motto { margin: 0; color: #174f92; font-size: .74rem; font-weight: 650; }
.so-sidebar-brand__notice { margin: .25rem 0 0; color: #8494a8; font-size: .61rem; letter-spacing: .04em; text-transform: uppercase; }

.so-india-masthead {
    display: flex; align-items: center; justify-content: space-between; gap: 1rem;
    margin: 0 0 1.1rem; padding: .7rem 0 .8rem; border-bottom: 1px solid #d8e2ed;
}
.so-india-masthead__copy { min-width: 0; }
.so-india-masthead__gov { margin: 0; color: #174f92; font-size: .72rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
.so-india-masthead__agency { margin: .16rem 0 0; color: #10233f; font-size: .86rem; font-weight: 650; }
.so-india-masthead__motto { margin: .18rem 0 0; color: #6b7e95; font-size: .71rem; }
.so-india-masthead__meta { color: #6b7e95; font-family: var(--so-mono); font-size: .66rem; text-align: right; text-transform: uppercase; }
.so-tricolor-rule { height: 4px; margin: 0 0 1.35rem; background: linear-gradient(90deg, #ff9933 0 33.33%, #ffffff 33.33% 66.66%, #138808 66.66% 100%); border: 1px solid #e2e8f0; border-radius: 999px; }

.hero {
    position: relative; overflow: hidden; border: 1px solid #cfdae8; border-radius: 14px;
    padding: 1.35rem 1.55rem; background: #ffffff; box-shadow: 0 10px 28px rgba(16,35,63,.07);
}
.hero::before { position: absolute; left: 0; top: 0; right: 0; height: 4px; background: linear-gradient(90deg,#ff9933 0 33.33%,#174f92 33.33% 66.66%,#138808 66.66%); content: ""; }
.hero-kicker, .section-kicker { color: #174f92; }
.hero-title, .section-title { color: #10233f; }
.hero-copy, .section-copy { color: #6b7e95; }
.tag { color: #174f92; background: #eef5fd; border-color: #c7d9ee; }
.tag.green { color: #137a2a; background: #edf8ef; border-color: #c4e3c8; }
.tag.orange { color: #af5b12; background: #fff4e9; border-color: #f3d1ae; }
.kpi-card, .so-kpi-card { background: #ffffff; border-color: #d6e0ec; box-shadow: 0 8px 22px rgba(16,35,63,.06); }
.kpi-label, .so-kpi-card__top { color: #6b7e95; }
.kpi-value, .so-kpi-card__value { color: #10233f; }
.kpi-note, .so-kpi-card__detail { color: #8494a8; }
.detail-card { background: #ffffff; border-color: #d6e0ec; }
.detail-label { color: #6b7e95; }
.detail-value { color: #10233f; }
.info-banner { color: #174f92; background: #eef5fd; border-left-color: #174f92; }
.alert-banner { color: #8f2538; background: #fff1f3; border-left-color: #be3144; }
hr { border-color: #d6e0ec; }
"""


def apply_theme() -> None:
    """Inject the dashboard theme into the current Streamlit page."""

    st.markdown(f"<style>{DASHBOARD_CSS}</style>", unsafe_allow_html=True)


def inject_theme() -> None:
    """Backward-friendly alias for :func:`apply_theme`."""

    apply_theme()


__all__ = [
    "COLORS",
    "DASHBOARD_CSS",
    "RISK_COLORS",
    "STATUS_COLORS",
    "apply_theme",
    "inject_theme",
]

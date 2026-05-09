"""Reusable chart helpers with rich, vibrant design system."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Design system colors ────────────────────────────────────────────────
COLORS = {
    "primary": "#3B82F6",
    "secondary": "#60A5FA",
    "accent": "#F97316",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "purple": "#8B5CF6",
    "pink": "#EC4899",
    "teal": "#14B8A6",
    "indigo": "#6366F1",
    "muted": "#94A3B8",
}

DOMAIN_COLORS = {
    "teachers": "#3B82F6",
    "lesson_plans": "#10B981",
    "observations": "#F97316",
    "training": "#8B5CF6",
    "coaching": "#EC4899",
    "students": "#14B8A6",
    "events": "#6366F1",
    "platform": "#F59E0B",
    "other": "#94A3B8",
}

# Vibrant multi-color sequence for charts (10 colors, high contrast)
COLOR_SEQUENCE = [
    "#3B82F6",  # blue
    "#10B981",  # emerald
    "#F97316",  # orange
    "#8B5CF6",  # violet
    "#EC4899",  # pink
    "#14B8A6",  # teal
    "#F59E0B",  # amber
    "#6366F1",  # indigo
    "#EF4444",  # red
    "#06B6D4",  # cyan
]

# Softer sequence for area/fill charts
COLOR_SEQUENCE_SOFT = [
    "#93C5FD",  # blue-300
    "#6EE7B7",  # emerald-300
    "#FDBA74",  # orange-300
    "#C4B5FD",  # violet-300
    "#F9A8D4",  # pink-300
    "#5EEAD4",  # teal-300
    "#FCD34D",  # amber-300
    "#A5B4FC",  # indigo-300
    "#FCA5A5",  # red-300
    "#67E8F9",  # cyan-300
]

LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    margin=dict(l=20, r=20, t=40, b=20),
    height=350,
    font=dict(family="Inter, system-ui, sans-serif", color="#0F172A", size=12),
    xaxis=dict(gridcolor="#F1F5F9", gridwidth=1),
    yaxis=dict(gridcolor="#F1F5F9", gridwidth=1),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#E2E8F0",
        font_size=12,
        font_family="Inter, system-ui, sans-serif",
    ),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)


def kpi_card(label: str, value: str | int | float, delta: str | None = None) -> None:
    """Render a KPI metric card."""
    import streamlit as st

    st.metric(label=label, value=value, delta=delta)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
) -> go.Figure:
    """Create a styled line chart with smooth curves."""
    fig = px.line(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(line=dict(width=2.5, shape="spline"))
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
    barmode: str = "group",
) -> go.Figure:
    """Create a styled bar chart with rounded corners."""
    fig = px.bar(
        df, x=x, y=y, title=title, color=color, barmode=barmode,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(marker_cornerradius=4)
    return fig


def stacked_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
) -> go.Figure:
    """Create a styled stacked bar chart with domain colors."""
    fig = px.bar(
        df, x=x, y=y, color=color, title=title, barmode="stack",
        color_discrete_map=DOMAIN_COLORS,
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(marker_cornerradius=3)
    return fig


def donut_chart(
    labels: list[str],
    values: list[int | float],
    title: str = "",
    colors: list[str] | None = None,
) -> go.Figure:
    """Create a styled donut chart with pull effect on largest segment."""
    sorted_pairs = sorted(zip(values, labels, strict=True), reverse=True)
    pull_vals = [0.04 if i == 0 else 0 for i in range(len(sorted_pairs))]

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(
            colors=colors or list(DOMAIN_COLORS.values()),
            line=dict(color="white", width=2),
        ),
        textinfo="label+percent", textposition="outside",
        textfont_size=11,
        pull=pull_vals,
    ))
    fig.update_layout(
        **{**LAYOUT_DEFAULTS, "showlegend": False},
        title=title,
    )
    return fig


def freshness_indicator(hours_ago: float) -> str:
    """Return HTML color dot based on staleness."""
    if hours_ago < 6:
        return '<span style="color:#10B981;">&#9679;</span>'
    elif hours_ago < 24:
        return '<span style="color:#F59E0B;">&#9679;</span>'
    return '<span style="color:#EF4444;">&#9679;</span>'

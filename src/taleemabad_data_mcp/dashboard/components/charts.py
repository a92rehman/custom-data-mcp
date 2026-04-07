"""Reusable chart helpers with consistent design system."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Design system colors
COLORS = {
    "primary": "#3B82F6",
    "secondary": "#60A5FA",
    "accent": "#F97316",
    "success": "#22C55E",
    "warning": "#EAB308",
    "danger": "#EF4444",
    "muted": "#94A3B8",
}

DOMAIN_COLORS = {
    "teachers": "#3B82F6",
    "lesson_plans": "#22C55E",
    "observations": "#F97316",
    "training": "#8B5CF6",
    "other": "#94A3B8",
}

LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    margin=dict(l=20, r=20, t=40, b=20),
    height=350,
    font=dict(family="Fira Sans, system-ui, sans-serif", color="#1E293B"),
    xaxis=dict(gridcolor="#F1F5F9"),
    yaxis=dict(gridcolor="#F1F5F9"),
    hovermode="x unified",
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
    """Create a styled line chart."""
    fig = px.line(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=[COLORS["primary"], COLORS["accent"], COLORS["success"]],
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(line=dict(width=2))
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
    barmode: str = "group",
) -> go.Figure:
    """Create a styled bar chart."""
    fig = px.bar(
        df, x=x, y=y, title=title, color=color, barmode=barmode,
        color_discrete_sequence=[COLORS["primary"], COLORS["danger"], COLORS["success"]],
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
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
    return fig


def donut_chart(
    labels: list[str],
    values: list[int | float],
    title: str = "",
    colors: list[str] | None = None,
) -> go.Figure:
    """Create a styled donut chart."""
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors or list(DOMAIN_COLORS.values())),
        textinfo="label+percent", textposition="outside",
        textfont_size=11,
    ))
    fig.update_layout(
        **{**LAYOUT_DEFAULTS, "showlegend": False},
        title=title,
    )
    return fig


def freshness_indicator(hours_ago: float) -> str:
    """Return HTML color dot based on staleness."""
    if hours_ago < 6:
        return '<span style="color:#22C55E;">&#9679;</span>'
    elif hours_ago < 24:
        return '<span style="color:#EAB308;">&#9679;</span>'
    return '<span style="color:#EF4444;">&#9679;</span>'

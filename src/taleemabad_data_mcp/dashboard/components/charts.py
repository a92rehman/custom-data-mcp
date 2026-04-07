"""Reusable chart helpers for dashboard pages."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def kpi_card(label: str, value: str | int | float, delta: str | None = None) -> None:
    """Render a KPI metric card using Streamlit's metric component."""
    import streamlit as st
    st.metric(label=label, value=value, delta=delta)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
) -> go.Figure:
    """Create a Plotly line chart."""
    fig = px.line(df, x=x, y=y, title=title, color=color)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
    barmode: str = "group",
) -> go.Figure:
    """Create a Plotly bar chart."""
    fig = px.bar(df, x=x, y=y, title=title, color=color, barmode=barmode)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def stacked_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
) -> go.Figure:
    """Create a Plotly stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title, barmode="stack")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def freshness_color(hours_ago: float) -> str:
    """Return color indicator based on staleness hours."""
    if hours_ago < 6:
        return "🟢"
    elif hours_ago < 24:
        return "🟡"
    return "🔴"

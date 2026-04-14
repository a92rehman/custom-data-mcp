"""Query Analytics — deep dive into activity patterns and user behavior."""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from taleemabad_data_mcp.dashboard.components.auto_refresh import (
    clear_cache_if_needed,
    inject_auto_refresh,
)
from taleemabad_data_mcp.dashboard.components.charts import stacked_bar_chart
from taleemabad_data_mcp.dashboard.components.filters import get_refresh_seconds, render_filters
from taleemabad_data_mcp.dashboard.components.styles import (
    CHART_H,
    CHART_H_SM,
    COLORS,
    inject_page_css,
    page_header,
    section_header,
)
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log

inject_page_css()

page_header("Query Analytics", "Understand who is asking what, when, and how queries perform")

filters = render_filters()
inject_auto_refresh(get_refresh_seconds())
clear_cache_if_needed(get_refresh_seconds())
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

df["date"] = pd.to_datetime(df["timestamp"]).dt.date
df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
real = df[df["error_type"] != "dry_run"]
successful = real[real["error_type"].isna()]

# -- KPI row --
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Queries", f"{len(real):,}")
c2.metric("Unique Users", real["user_name"].nunique())
c3.metric("Domains Used", real["domain"].nunique())
avg_exec = (
    successful["execution_ms"].mean()
    if not successful.empty and "execution_ms" in successful.columns
    else 0
)
c4.metric("Avg Response", f"{avg_exec:.0f}ms")
success_pct = len(successful) / len(real) * 100 if len(real) > 0 else 0
c5.metric("Success Rate", f"{success_pct:.0f}%")

st.markdown("")

# -- Row 1: Volume by domain + Query outcome breakdown --
col1, col2 = st.columns(2)

with col1:
    section_header("Daily Volume by Domain", "purple")
    vol = real.groupby(["date", "domain"]).size().reset_index(name="Queries")
    st.plotly_chart(
        stacked_bar_chart(vol, "date", "Queries", "domain"),
        use_container_width=True,
    )

with col2:
    section_header("Query Outcomes", "green")
    df["outcome"] = df["error_type"].apply(
        lambda x: "Dry Run" if x == "dry_run" else (
            "Error" if pd.notna(x) else "Success"
        )
    )
    outcome_daily = (
        df.groupby(["date", "outcome"]).size().reset_index(name="Count")
    )
    color_map = {"Success": "#10B981", "Error": "#EF4444", "Dry Run": "#94A3B8"}
    fig = go.Figure()
    for outcome, color in color_map.items():
        subset = outcome_daily[outcome_daily["outcome"] == outcome]
        if not subset.empty:
            fig.add_trace(go.Bar(
                x=subset["date"], y=subset["Count"],
                name=outcome, marker_color=color,
                marker_cornerradius=3,
            ))
    fig.update_layout(
        template="plotly_white", barmode="stack",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
        legend=dict(orientation="h", yanchor="top", y=1.1, x=0),
        xaxis=dict(title=None), yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Row 2: Peak hours heatmap + Queries per user --
col3, col4 = st.columns(2)

with col3:
    section_header("Peak Usage Hours", "orange")
    hourly = real.groupby("hour").size().reset_index(name="Queries")
    all_hours = pd.DataFrame({"hour": range(24)})
    hourly = all_hours.merge(hourly, on="hour", how="left").fillna(0)
    fig = go.Figure(go.Bar(
        x=hourly["hour"], y=hourly["Queries"],
        marker_color=[
            COLORS["purple"] if q > hourly["Queries"].quantile(0.75)
            else COLORS["teal"] if q > hourly["Queries"].quantile(0.25)
            else "#E2E8F0"
            for q in hourly["Queries"]
        ],
        marker_cornerradius=3,
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
        xaxis=dict(
            title="Hour of Day",
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h}:00" for h in range(0, 24, 2)],
        ),
        yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    section_header("Queries per User", "")
    qpu = (
        real.groupby("user_name").size()
        .reset_index(name="Queries")
        .sort_values("Queries", ascending=True)
    )
    fig = go.Figure(go.Bar(
        x=qpu["Queries"], y=qpu["user_name"],
        orientation="h", marker_color=COLORS["indigo"],
        text=qpu["Queries"], textposition="auto",
        marker_cornerradius=3,
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
        xaxis=dict(title=None), yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Recent queries table --
section_header("Recent Queries", "teal")
display_cols = [
    "timestamp", "user_name", "domain", "query_text",
    "cost_usd", "error_type",
]
available = [c for c in display_cols if c in df.columns]
st.dataframe(df[available].head(50), use_container_width=True, hide_index=True)

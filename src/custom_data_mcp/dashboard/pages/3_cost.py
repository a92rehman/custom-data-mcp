"""Cost — BigQuery spend analysis and optimization insights."""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from custom_data_mcp.dashboard.components.auto_refresh import (
    clear_cache_if_needed,
    inject_auto_refresh,
)
from custom_data_mcp.dashboard.components.charts import DOMAIN_COLORS
from custom_data_mcp.dashboard.components.filters import get_refresh_seconds, render_filters
from custom_data_mcp.dashboard.components.styles import (
    CHART_H,
    CHART_H_SM,
    COLORS,
    inject_page_css,
    page_header,
    section_header,
)
from custom_data_mcp.dashboard.data.queries import get_activity_log

inject_page_css()

page_header("Cost Tracking", "BigQuery spend analysis — who is querying what, and how much does it cost?")

filters = render_filters()
inject_auto_refresh(get_refresh_seconds())
clear_cache_if_needed(get_refresh_seconds())
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

cost_df = df[df["cost_usd"].notna() & (df["cost_usd"] > 0)].copy()

# -- KPI row --
total_cost = cost_df["cost_usd"].sum() if not cost_df.empty else 0
total_bytes = cost_df["cost_bytes"].sum() if not cost_df.empty else 0
avg_cost = cost_df["cost_usd"].mean() if not cost_df.empty else 0
num_queries = len(cost_df)
max_query = cost_df["cost_usd"].max() if not cost_df.empty else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Spend", f"${total_cost:.2f}")
c2.metric("Data Scanned", f"{total_bytes / (1024**3):.1f} GB")
c3.metric("Avg per Query", f"${avg_cost:.4f}")
c4.metric("Billed Queries", f"{num_queries:,}")
c5.metric("Most Expensive", f"${max_query:.4f}")

st.markdown("")

if cost_df.empty:
    st.info("No queries with cost data in this period.")
    st.stop()

# -- Row 1: Spend trend + Cumulative spend --
cost_df["date"] = pd.to_datetime(cost_df["timestamp"]).dt.date
col1, col2 = st.columns(2)

with col1:
    section_header("Daily Spend", "orange")
    daily = cost_df.groupby("date")["cost_usd"].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["date"], y=daily["cost_usd"],
        marker_color=COLORS["accent"],
        marker_cornerradius=4,
        text=[f"${v:.3f}" for v in daily["cost_usd"]],
        textposition="outside", textfont_size=9,
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
        xaxis=dict(title=None), yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("Cumulative Spend", "amber")
    daily_sorted = daily.sort_values("date")
    daily_sorted["cumulative"] = daily_sorted["cost_usd"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_sorted["date"], y=daily_sorted["cumulative"],
        mode="lines+markers", fill="tozeroy",
        line=dict(color=COLORS["purple"], width=2),
        marker=dict(size=4),
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
        xaxis=dict(title=None), yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Row 2: Cost by domain + Cost by user --
col3, col4 = st.columns(2)

with col3:
    section_header("Cost by Domain", "purple")
    by_domain = (
        cost_df.groupby("domain")["cost_usd"]
        .sum().reset_index().sort_values("cost_usd", ascending=True)
    )
    d_colors = [
        DOMAIN_COLORS.get(d, "#94A3B8") for d in by_domain["domain"]
    ]
    fig = go.Figure(go.Bar(
        x=by_domain["cost_usd"], y=by_domain["domain"],
        orientation="h", marker_color=d_colors,
        marker_cornerradius=4,
        text=[f"${v:.3f}" for v in by_domain["cost_usd"]],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
        xaxis=dict(title=None), yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    section_header("Cost by User", "")
    by_user = (
        cost_df.groupby("user_name")["cost_usd"]
        .sum().reset_index().sort_values("cost_usd", ascending=True)
    )
    fig = go.Figure(go.Bar(
        x=by_user["cost_usd"], y=by_user["user_name"],
        orientation="h", marker_color=COLORS["teal"],
        marker_cornerradius=4,
        text=[f"${v:.3f}" for v in by_user["cost_usd"]],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
        xaxis=dict(title=None), yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Most expensive queries --
section_header("Most Expensive Queries", "red")
top = cost_df.nlargest(10, "cost_usd")
display_cols = [
    "timestamp", "user_name", "domain", "cost_usd",
    "cost_bytes", "query_text",
]
available = [c for c in display_cols if c in top.columns]
st.dataframe(top[available], use_container_width=True, hide_index=True)

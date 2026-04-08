"""Errors — failed queries, governance gaps, and patterns to fix."""

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
from taleemabad_data_mcp.dashboard.components.charts import DOMAIN_COLORS
from taleemabad_data_mcp.dashboard.components.filters import get_refresh_seconds, render_filters
from taleemabad_data_mcp.dashboard.components.styles import (
    CHART_H,
    CHART_H_SM,
    COLORS,
    inject_page_css,
)
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log

inject_page_css()

st.header("Errors & Governance Gaps")
st.caption("Failed queries, missing rules, and patterns to fix")

filters = render_filters()
inject_auto_refresh(get_refresh_seconds())
clear_cache_if_needed(get_refresh_seconds())
st.markdown("---")
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

real = df[df["error_type"] != "dry_run"]
errors = real[real["error_type"].notna()].copy()
total = len(real)

# -- KPI row --
err_rate = len(errors) / total * 100 if total > 0 else 0
unique_types = errors["error_type"].nunique() if not errors.empty else 0
most_common = (
    errors["error_type"].value_counts().index[0]
    if not errors.empty else "None"
)
affected_users = errors["user_name"].nunique() if not errors.empty else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Errors", len(errors))
c2.metric("Error Rate", f"{err_rate:.1f}%")
c3.metric("Error Types", unique_types)
c4.metric("Most Common", most_common)
c5.metric("Affected Users", affected_users)

st.markdown("")

if errors.empty:
    st.success("No errors in this period! All queries completed successfully.")
    st.stop()

errors["date"] = pd.to_datetime(errors["timestamp"]).dt.date

# -- Row 1: Error trend + Error type distribution --
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown(
        '<div class="section-header">Errors Over Time</div>',
        unsafe_allow_html=True,
    )
    daily_err = errors.groupby("date").size().reset_index(name="Errors")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_err["date"], y=daily_err["Errors"],
        mode="lines+markers", fill="tozeroy",
        line=dict(color=COLORS["danger"], width=2),
        fillcolor="rgba(239,68,68,0.1)",
        marker=dict(size=5),
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
        xaxis=dict(title=None), yaxis=dict(title=None),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown(
        '<div class="section-header">Error Type Breakdown</div>',
        unsafe_allow_html=True,
    )
    type_counts = (
        errors.groupby("error_type").size()
        .reset_index(name="Count").sort_values("Count", ascending=False)
    )
    color_list = [COLORS["danger"], COLORS["accent"], COLORS["warning"]]
    fig = go.Figure(go.Pie(
        labels=type_counts["error_type"],
        values=type_counts["Count"],
        hole=0.5,
        marker=dict(
            colors=color_list[:len(type_counts)]
            + ["#CBD5E1"] * max(0, len(type_counts) - len(color_list)),
        ),
        textinfo="label+value",
        textposition="outside",
        textfont_size=11,
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Row 2: Errors by domain + Errors by user --
col3, col4 = st.columns(2)

with col3:
    st.markdown(
        '<div class="section-header">Errors by Domain</div>',
        unsafe_allow_html=True,
    )
    by_domain = (
        errors.groupby("domain").size()
        .reset_index(name="Count").sort_values("Count", ascending=True)
    )
    d_colors = [
        DOMAIN_COLORS.get(d, "#94A3B8") for d in by_domain["domain"]
    ]
    fig = go.Figure(go.Bar(
        x=by_domain["Count"], y=by_domain["domain"],
        orientation="h", marker_color=d_colors,
        text=by_domain["Count"], textposition="auto",
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
        xaxis=dict(title=None), yaxis=dict(title=None),
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.markdown(
        '<div class="section-header">Errors by User</div>',
        unsafe_allow_html=True,
    )
    by_user = (
        errors.groupby("user_name").size()
        .reset_index(name="Count").sort_values("Count", ascending=True)
    )
    fig = go.Figure(go.Bar(
        x=by_user["Count"], y=by_user["user_name"],
        orientation="h", marker_color=COLORS["danger"],
        text=by_user["Count"], textposition="auto",
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
        xaxis=dict(title=None), yaxis=dict(title=None),
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Governance gaps --
st.markdown(
    '<div class="section-header">Governance Gaps</div>',
    unsafe_allow_html=True,
)
gaps = errors[
    (errors["error_type"] == "NoMatchingMetric")
    | (
        errors["error_message"]
        .str.contains("no governed", case=False, na=False)
    )
]
if not gaps.empty:
    st.warning(
        f"Found {len(gaps)} queries that did not match any governed rule."
    )
    st.dataframe(
        gaps[
            ["timestamp", "user_name", "query_text", "error_message"]
        ].head(50),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success(
        "No governance gaps — all queries matched governed rules."
    )

# -- Full error log --
st.markdown(
    '<div class="section-header">Error Details</div>',
    unsafe_allow_html=True,
)
st.dataframe(
    errors[
        ["timestamp", "user_name", "error_type", "domain",
         "error_message", "query_text"]
    ].head(50),
    use_container_width=True,
    hide_index=True,
)

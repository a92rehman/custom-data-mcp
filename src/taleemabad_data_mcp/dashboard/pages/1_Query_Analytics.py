"""Detailed query analytics — drill into activity patterns."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import (
    bar_chart,
    line_chart,
    stacked_bar_chart,
)
from taleemabad_data_mcp.dashboard.components.filters import render_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log

st.header("Query Analytics")
st.caption("Deep dive into query patterns, volume, and user behavior")

filters = render_filters()
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

df["date"] = pd.to_datetime(df["timestamp"]).dt.date
real = df[df["error_type"] != "dry_run"]

# Volume by domain over time
st.subheader("Query Volume by Domain")
vol = real.groupby(["date", "domain"]).size().reset_index(name="Queries")
st.plotly_chart(
    stacked_bar_chart(vol, "date", "Queries", "domain", ""),
    use_container_width=True,
)

# Users over time
col1, col2 = st.columns(2)

with col1:
    st.subheader("Daily Active Users")
    dau = real.groupby("date")["user_name"].nunique().reset_index()
    dau.columns = ["Date", "Users"]
    st.plotly_chart(
        line_chart(dau, "Date", "Users"), use_container_width=True,
    )

with col2:
    st.subheader("Queries per User")
    qpu = (
        real.groupby("user_name").size()
        .reset_index(name="Queries")
        .sort_values("Queries", ascending=False)
    )
    st.plotly_chart(
        bar_chart(qpu, "user_name", "Queries"), use_container_width=True,
    )

# Query types breakdown
st.subheader("Dry Runs vs Executed Queries")
df["type"] = df["error_type"].apply(
    lambda x: "Dry Run" if x == "dry_run" else ("Error" if pd.notna(x) else "Success")
)
type_daily = df.groupby(["date", "type"]).size().reset_index(name="Count")
st.plotly_chart(
    stacked_bar_chart(type_daily, "date", "Count", "type", ""),
    use_container_width=True,
)

# Recent queries table
st.subheader("Recent Queries")
display_cols = ["timestamp", "user_name", "domain", "query_text", "cost_usd", "error_type"]
available = [c for c in display_cols if c in df.columns]
st.dataframe(
    df[available].head(50),
    use_container_width=True,
    hide_index=True,
)

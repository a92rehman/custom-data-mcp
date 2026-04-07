"""Errors & governance gaps."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card, line_chart
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log

st.header("Errors & Governance Gaps")

filters = render_sidebar_filters()
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

errors = df[(df["error_type"].notna()) & (df["error_type"] != "dry_run")].copy()
total = len(df[df["error_type"] != "dry_run"])

col1, col2, col3 = st.columns(3)

with col1:
    kpi_card("Total Errors", len(errors))

with col2:
    error_rate = f"{len(errors) / total * 100:.1f}%" if total > 0 else "0%"
    kpi_card("Error Rate", error_rate)

with col3:
    unique_types = errors["error_type"].nunique() if not errors.empty else 0
    kpi_card("Error Types", unique_types)

st.divider()

if errors.empty:
    st.success("No errors in this period!")
    st.stop()

errors["date"] = pd.to_datetime(errors["timestamp"]).dt.date
daily_errors = errors.groupby("date").size().reset_index(name="Errors")
st.plotly_chart(line_chart(daily_errors, "date", "Errors", "Errors Over Time"), use_container_width=True)

type_counts = errors.groupby("error_type").size().reset_index(name="Count").sort_values("Count", ascending=False)
st.plotly_chart(bar_chart(type_counts, "error_type", "Count", "Errors by Type"), use_container_width=True)

st.subheader("Governance Gaps")
gaps = errors[
    (errors["error_type"] == "NoMatchingMetric")
    | (errors["error_message"].str.contains("no governed", case=False, na=False))
]
if not gaps.empty:
    st.dataframe(
        gaps[["timestamp", "user_name", "query_text", "error_message"]].head(50),
        use_container_width=True,
    )
else:
    st.info("No governance gaps detected — all queries matched governed rules.")

st.subheader("Error Details")
st.dataframe(
    errors[["timestamp", "user_name", "error_type", "error_message", "query_text"]].head(50),
    use_container_width=True,
)

"""Expectation vs Reality — feedback deep dive."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log, get_feedback

st.header("Expectation vs Reality")
st.caption("Are MCP answers meeting user expectations? Feedback collected voluntarily.")

filters = render_sidebar_filters()
fb = get_feedback(days=filters["days"])
activity = get_activity_log(**filters)

if fb.empty:
    st.info(
        "No feedback data found. Feedback is collected when users "
        "voluntarily rate query results."
    )
    st.stop()

col1, col2, col3 = st.columns(3)

up_count = (fb["rating"] == "up").sum()
down_count = (fb["rating"] == "down").sum()
total_fb = len(fb)

with col1:
    kpi_card("Thumbs Up", int(up_count))
with col2:
    kpi_card("Thumbs Down", int(down_count))
with col3:
    total_queries = len(activity) if not activity.empty else 0
    ratio = (1 - total_fb / total_queries) * 100 if total_queries > 0 else 0
    unrated_pct = f"{ratio:.0f}%" if total_queries > 0 else "N/A"
    kpi_card("Unrated Queries", unrated_pct)

st.divider()

fb["date"] = pd.to_datetime(fb["timestamp"]).dt.date
timeline = fb.groupby(["date", "rating"]).size().reset_index(name="Count")
st.plotly_chart(
    bar_chart(timeline, "date", "Count", "Feedback Over Time", color="rating"),
    use_container_width=True,
)

if "domain" in fb.columns:
    domain_sat = fb.groupby(["domain", "rating"]).size().reset_index(name="Count")
    st.plotly_chart(
        bar_chart(domain_sat, "domain", "Count", "Satisfaction by Domain", color="rating"),
        use_container_width=True,
    )

user_sat = fb.groupby(["user_name", "rating"]).size().unstack(fill_value=0).reset_index()
st.subheader("Satisfaction by User")
st.dataframe(user_sat, use_container_width=True)

comments = fb[fb["comment"].notna() & (fb["comment"] != "")]
if not comments.empty:
    st.subheader("Recent Comments")
    st.dataframe(
        comments[["timestamp", "user_name", "rating", "comment", "query_text"]].head(50),
        use_container_width=True,
    )
else:
    st.info("No comments yet.")

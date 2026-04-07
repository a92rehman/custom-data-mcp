"""Overview page — active users, query volume, feedback summary."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card, line_chart, stacked_bar_chart
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log, get_feedback

st.header("Overview")

filters = render_sidebar_filters()
df = get_activity_log(**filters)
fb = get_feedback(days=filters["days"])

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card("Total Queries", len(df))

with col2:
    active_users = df["user_name"].nunique()
    kpi_card("Active Users", active_users)

with col3:
    if not fb.empty:
        up_count = (fb["rating"] == "up").sum()
        total_fb = len(fb)
        sat_rate = f"{up_count / total_fb * 100:.0f}%" if total_fb > 0 else "N/A"
    else:
        sat_rate = "N/A"
    kpi_card("Satisfaction Rate", sat_rate)

with col4:
    avg_cost = df["cost_usd"].mean() if "cost_usd" in df.columns else 0
    kpi_card("Avg Cost/Query", f"${avg_cost:.4f}")

st.divider()

df["date"] = pd.to_datetime(df["timestamp"]).dt.date
dau = df.groupby("date")["user_name"].nunique().reset_index()
dau.columns = ["Date", "Active Users"]
st.plotly_chart(line_chart(dau, "Date", "Active Users", "Daily Active Users"), use_container_width=True)

vol = df.groupby(["date", "domain"]).size().reset_index(name="Queries")
st.plotly_chart(
    stacked_bar_chart(vol, "date", "Queries", "domain", "Query Volume by Domain"),
    use_container_width=True,
)

if not fb.empty:
    fb["date"] = pd.to_datetime(fb["timestamp"]).dt.date
    fb_daily = fb.groupby(["date", "rating"]).size().reset_index(name="Count")
    st.plotly_chart(
        bar_chart(fb_daily, "date", "Count", "Feedback Trend", color="rating"),
        use_container_width=True,
    )

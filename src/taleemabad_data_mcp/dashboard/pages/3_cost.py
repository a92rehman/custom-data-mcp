"""Cost tracking — BigQuery spend analysis."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card, line_chart
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log

st.header("Cost Tracking")

filters = render_sidebar_filters()
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

cost_df = df[df["cost_usd"].notna() & (df["cost_usd"] > 0)].copy()

col1, col2, col3 = st.columns(3)

with col1:
    total_cost = cost_df["cost_usd"].sum() if not cost_df.empty else 0
    kpi_card("Total Spend", f"${total_cost:.2f}")

with col2:
    total_bytes = cost_df["cost_bytes"].sum() if not cost_df.empty else 0
    gb = total_bytes / (1024 ** 3)
    kpi_card("Total Data Scanned", f"{gb:.1f} GB")

with col3:
    avg_cost = cost_df["cost_usd"].mean() if not cost_df.empty else 0
    kpi_card("Avg Cost/Query", f"${avg_cost:.4f}")

st.divider()

if cost_df.empty:
    st.info("No queries with cost data in this period.")
    st.stop()

cost_df["date"] = pd.to_datetime(cost_df["timestamp"]).dt.date
daily_cost = cost_df.groupby("date")["cost_usd"].sum().reset_index()
daily_cost.columns = ["Date", "Cost (USD)"]
st.plotly_chart(line_chart(daily_cost, "Date", "Cost (USD)", "Daily Spend"), use_container_width=True)

user_cost = cost_df.groupby("user_name")["cost_usd"].sum().reset_index().sort_values("cost_usd", ascending=False)
user_cost.columns = ["User", "Cost (USD)"]
st.plotly_chart(bar_chart(user_cost.head(10), "User", "Cost (USD)", "Top Spenders"), use_container_width=True)

domain_cost = cost_df.groupby("domain")["cost_usd"].sum().reset_index().sort_values("cost_usd", ascending=False)
domain_cost.columns = ["Domain", "Cost (USD)"]
st.plotly_chart(bar_chart(domain_cost, "Domain", "Cost (USD)", "Cost by Domain"), use_container_width=True)

large = cost_df.nlargest(10, "cost_bytes")
if not large.empty:
    st.subheader("Largest Queries")
    st.dataframe(
        large[["timestamp", "user_name", "domain", "cost_usd", "cost_bytes", "query_text"]],
        use_container_width=True,
    )

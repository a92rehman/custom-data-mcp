"""Data freshness status for key tables."""

from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import freshness_color
from taleemabad_data_mcp.dashboard.data.queries import get_table_freshness

st.header("Data Freshness")

st.markdown("Freshness of key BigQuery tables used by governed metrics.")

try:
    df = get_table_freshness()

    if df.empty:
        st.warning("Could not retrieve freshness data. Check BigQuery permissions.")
        st.stop()

    now = datetime.now(UTC)
    df["hours_ago"] = df["last_modified"].apply(
        lambda ts: (now - ts.replace(tzinfo=UTC)).total_seconds() / 3600
        if pd.notna(ts) else None
    )
    df["status"] = df["hours_ago"].apply(
        lambda h: freshness_color(h) if pd.notna(h) else "⚪"
    )
    df["last_modified_str"] = df["last_modified"].apply(
        lambda ts: ts.strftime("%Y-%m-%d %H:%M UTC") if pd.notna(ts) else "Unknown"
    )
    df["hours_ago_str"] = df["hours_ago"].apply(
        lambda h: f"{h:.1f}h" if pd.notna(h) else "Unknown"
    )

    display = df[["status", "table_name", "last_modified_str", "hours_ago_str"]].copy()
    display.columns = ["Status", "Table", "Last Modified", "Age"]

    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("""
    **Legend:** 🟢 Fresh (<6h) | 🟡 Aging (6-24h) | 🔴 Stale (>24h) | ⚪ Unknown
    """)

except Exception as e:
    st.error(f"Error fetching freshness data: {e}")

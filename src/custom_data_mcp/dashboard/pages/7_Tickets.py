"""Tickets — system health tickets from self-healing loops.

This page reads from local JSONL only — no BigQuery credentials required.
It avoids importing the BQ client chain so it works on machines without GCP setup.
"""

import json
import sys as _sys
from datetime import UTC, datetime, timedelta
from pathlib import Path as _Path

_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Import only styles (no filters — those pull in BQ client)
from custom_data_mcp.dashboard.components.styles import (
    CHART_H,
    CHART_H_SM,
    COLORS,
    inject_page_css,
    page_header,
    section_header,
)

inject_page_css()

page_header("System Tickets", "Self-healing loop tickets — query fixes and infrastructure issues")


def _load_tickets_from_jsonl(days: int = 30) -> pd.DataFrame:
    """Load tickets from local JSONL file. No BigQuery needed."""
    cols = [
        "ticket_id", "created_at", "updated_at", "user_email", "hostname",
        "loop", "category", "symptom", "severity", "status",
        "diagnosis", "resolution_notes", "escalated_to", "related_event_id",
    ]
    local_file = _Path.home() / ".claude" / "custom-data-logs" / "tickets.jsonl"
    if not local_file.exists():
        return pd.DataFrame(columns=cols)

    cutoff = datetime.now(UTC) - timedelta(days=days)
    ticket_map: dict[str, dict] = {}
    try:
        for line in local_file.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            t = json.loads(line)
            ticket_map[t["ticket_id"]] = t  # keep latest version per ticket
    except Exception:
        return pd.DataFrame(columns=cols)

    rows = []
    for t in ticket_map.values():
        created = pd.Timestamp(t.get("created_at", ""))
        if pd.notna(created):
            if created.tz_localize(None) >= pd.Timestamp(cutoff.replace(tzinfo=None)):
                rows.append({c: t.get(c) for c in cols})

    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)


# Sidebar: date range
days = st.sidebar.slider("Days", 7, 90, 30, key="ticket_days")
df = _load_tickets_from_jsonl(days=days)

if df.empty:
    st.info("No tickets found. The self-healing system has not opened any tickets yet.")
    st.stop()

# Ensure datetime columns
for col in ("created_at", "updated_at"):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# -- KPI row --
CATEGORY_COLORS = {
    "connection": COLORS.get("danger", "#EF4444"),
    "identity": COLORS.get("warning", "#F59E0B"),
    "rules": COLORS.get("accent", "#3B82F6"),
    "plugin": COLORS.get("purple", "#8B5CF6"),
    "schema": "#EC4899",
    "syntax": "#F97316",
    "partition": "#14B8A6",
    "cost": "#6366F1",
    "other": "#94A3B8",
}

open_count = len(df[df["status"].isin(["open", "diagnosing"])])
auto_fixed = len(df[df["status"] == "auto_fixed"])
escalated = len(df[df["status"] == "escalated"])
user_action = len(df[df["status"] == "user_action_required"])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Tickets", len(df))
c2.metric("Open", open_count)
c3.metric("Auto-Fixed", auto_fixed)
c4.metric("Escalated", escalated)
c5.metric("User Action", user_action)

st.markdown("")

# -- Row 1: Auto-fix success rate over time + Top symptoms --
col1, col2 = st.columns(2)

with col1:
    section_header("Auto-Fix Success Rate (7d rolling)", "green")
    if "created_at" in df.columns and pd.api.types.is_datetime64_any_dtype(df["created_at"]):
        df_dated = df.dropna(subset=["created_at"]).copy()
        df_dated["date"] = df_dated["created_at"].dt.date

        closed = df_dated[df_dated["status"].isin(["auto_fixed", "escalated", "abandoned", "user_action_required"])]
        if not closed.empty:
            daily = closed.groupby("date").agg(
                total=("status", "size"),
                fixed=("status", lambda x: (x == "auto_fixed").sum()),
            ).reset_index()
            daily["rate"] = (daily["fixed"] / daily["total"] * 100).round(1)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily["date"], y=daily["rate"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color="#10B981", width=2),
                fillcolor="rgba(16,185,129,0.08)",
                marker=dict(size=5),
            ))
            fig.update_layout(
                template="plotly_white",
                margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
                yaxis=dict(title="Success %", range=[0, 105]),
                xaxis=dict(title=None),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, system-ui, sans-serif"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No closed tickets yet to calculate success rate.")
    else:
        st.info("No dated ticket data available.")

with col2:
    section_header("Top Recurring Symptoms", "orange")
    symptom_counts = (
        df.groupby("symptom").size()
        .reset_index(name="Count").sort_values("Count", ascending=True).tail(10)
    )
    if not symptom_counts.empty:
        fig = go.Figure(go.Bar(
            x=symptom_counts["Count"], y=symptom_counts["symptom"],
            orientation="h",
            marker_color=COLORS.get("warning", "#F59E0B"),
            text=symptom_counts["Count"], textposition="auto",
            marker_cornerradius=3,
        ))
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
            xaxis=dict(title=None), yaxis=dict(title=None),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No symptom data.")

# -- Row 2: Category breakdown --
section_header("Tickets by Category", "purple")
cat_counts = (
    df.groupby("category").size()
    .reset_index(name="Count").sort_values("Count", ascending=False)
)
if not cat_counts.empty:
    cat_colors = [CATEGORY_COLORS.get(c, "#94A3B8") for c in cat_counts["category"]]
    fig = go.Figure(go.Bar(
        x=cat_counts["category"], y=cat_counts["Count"],
        marker_color=cat_colors,
        text=cat_counts["Count"], textposition="auto",
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

# -- Ticket detail table --
section_header("Ticket Details", "blue")

# Filters
filter_cols = st.columns(4)
with filter_cols[0]:
    status_filter = st.multiselect("Status", df["status"].unique().tolist(), key="tkt_status")
with filter_cols[1]:
    cat_filter = st.multiselect("Category", df["category"].unique().tolist(), key="tkt_cat")
with filter_cols[2]:
    loop_filter = st.multiselect("Loop", df["loop"].unique().tolist(), key="tkt_loop")
with filter_cols[3]:
    sev_filter = st.multiselect("Severity", df["severity"].unique().tolist(), key="tkt_sev")

filtered = df.copy()
if status_filter:
    filtered = filtered[filtered["status"].isin(status_filter)]
if cat_filter:
    filtered = filtered[filtered["category"].isin(cat_filter)]
if loop_filter:
    filtered = filtered[filtered["loop"].isin(loop_filter)]
if sev_filter:
    filtered = filtered[filtered["severity"].isin(sev_filter)]

display_cols = [
    "ticket_id", "created_at", "loop", "category", "symptom",
    "severity", "status", "diagnosis", "resolution_notes", "escalated_to",
]
available = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available].head(100),
    use_container_width=True,
    hide_index=True,
    column_config={
        "escalated_to": st.column_config.LinkColumn("GitHub Issue"),
    } if "escalated_to" in available else None,
)

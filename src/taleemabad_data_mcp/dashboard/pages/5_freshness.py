"""Freshness — how up-to-date are the data tables powering governed metrics."""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

from datetime import UTC, datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from taleemabad_data_mcp.dashboard.components.styles import COLORS, inject_page_css
from taleemabad_data_mcp.dashboard.data.queries import get_table_freshness

inject_page_css()

st.header("Data Freshness")
st.caption(
    "How recently were the key BigQuery tables updated? "
    "Stale tables mean users might see outdated numbers."
)

# Table-to-domain mapping for context
TABLE_INFO = {
    "user_school_profiles": {
        "domain": "Teachers",
        "desc": "One row per teacher with school assignments",
    },
    "events_partitioned": {
        "domain": "Lesson Plans",
        "desc": "All app events (LP starts, completions, training)",
    },
    "coaching_observation": {
        "domain": "Observations",
        "desc": "Classroom observation records (FICO scores)",
    },
    "teacher_training_level": {
        "domain": "Training",
        "desc": "Training level definitions and ordering",
    },
    "teacher_training_assessment": {
        "domain": "Training",
        "desc": "Assessment scores and pass/fail results",
    },
    "lp_info_all_types": {
        "domain": "Lesson Plans",
        "desc": "Pre-computed LP data per teacher per day",
    },
    "FDE_Schools": {
        "domain": "Teachers",
        "desc": "ICT/Islamabad school reference table",
    },
}

try:
    df = get_table_freshness()
except Exception as e:
    st.error(
        f"Could not connect to BigQuery to check table freshness: {e}"
    )
    st.stop()

if df.empty:
    st.warning(
        "No freshness data available. "
        "This might mean the tables do not exist or permissions are missing."
    )
    st.stop()

now = datetime.now(UTC)

df["hours_ago"] = df["last_modified"].apply(
    lambda ts: (now - ts.replace(tzinfo=UTC)).total_seconds() / 3600
    if pd.notna(ts) else None
)

# -- KPI row --
fresh_count = int((df["hours_ago"] < 6).sum())
aging_count = int(((df["hours_ago"] >= 6) & (df["hours_ago"] < 24)).sum())
stale_count = int((df["hours_ago"] >= 24).sum())
avg_age = df["hours_ago"].mean() if not df["hours_ago"].isna().all() else 0
oldest = df["hours_ago"].max() if not df["hours_ago"].isna().all() else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Fresh (<6h)", fresh_count)
c2.metric("Aging (6-24h)", aging_count)
c3.metric("Stale (>24h)", stale_count)
c4.metric("Avg Age", f"{avg_age:.0f}h")
c5.metric("Oldest Table", f"{oldest:.0f}h")

st.markdown("")

# -- Visual freshness bars --
st.markdown(
    '<div class="section-header">Table Freshness Status</div>',
    unsafe_allow_html=True,
)

df_sorted = df.sort_values("hours_ago", ascending=True)

for _, row in df_sorted.iterrows():
    tname = row["table_name"]
    hours = row["hours_ago"]
    info = TABLE_INFO.get(tname, {"domain": "Other", "desc": ""})

    if pd.isna(hours):
        color = "#CBD5E1"
        status = "Unknown"
        bar_width = 0
    elif hours < 6:
        color = COLORS["success"]
        status = f"{hours:.1f}h ago"
        bar_width = max(5, min(100, 100 - hours / 24 * 100))
    elif hours < 24:
        color = COLORS["warning"]
        status = f"{hours:.0f}h ago"
        bar_width = max(5, min(100, 100 - hours / 48 * 100))
    else:
        color = COLORS["danger"]
        status = f"{hours:.0f}h ago"
        bar_width = max(5, min(100, 100 - hours / 168 * 100))

    last_mod = (
        row["last_modified"].strftime("%b %d, %H:%M UTC")
        if pd.notna(row["last_modified"]) else "Unknown"
    )

    st.markdown(
        f"<div style='background:white;border:1px solid #E2E8F0;"
        f"border-radius:10px;padding:14px 18px;margin-bottom:8px;"
        f"box-shadow:0 1px 3px rgba(0,0,0,0.04);'>"
        f"<div style='display:flex;justify-content:space-between;"
        f"align-items:center;margin-bottom:6px;'>"
        f"<div>"
        f"<span style='font-weight:600;color:#1E293B;'>{tname}</span>"
        f"<span style='color:#94A3B8;font-size:0.8rem;margin-left:8px;'>"
        f"{info['domain']}</span></div>"
        f"<span style='font-weight:600;color:{color};'>{status}</span>"
        f"</div>"
        f"<div style='background:#F1F5F9;border-radius:4px;height:8px;"
        f"overflow:hidden;'>"
        f"<div style='background:{color};height:100%;"
        f"width:{bar_width}%;border-radius:4px;"
        f"transition:width 0.3s;'></div></div>"
        f"<div style='display:flex;justify-content:space-between;"
        f"margin-top:4px;font-size:0.75rem;color:#94A3B8;'>"
        f"<span>{info['desc']}</span>"
        f"<span>Updated: {last_mod}</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# -- Freshness distribution chart --
st.markdown("")
st.markdown(
    '<div class="section-header">Freshness Distribution</div>',
    unsafe_allow_html=True,
)

fig = go.Figure(go.Bar(
    x=df_sorted["table_name"],
    y=df_sorted["hours_ago"],
    marker_color=[
        COLORS["success"] if h < 6
        else COLORS["warning"] if h < 24
        else COLORS["danger"]
        for h in df_sorted["hours_ago"].fillna(0)
    ],
    text=[f"{h:.0f}h" for h in df_sorted["hours_ago"].fillna(0)],
    textposition="outside",
    textfont_size=10,
))

# Add threshold lines
fig.add_hline(
    y=6, line_dash="dot", line_color=COLORS["warning"],
    annotation_text="6h (fresh threshold)",
    annotation_position="top right",
    annotation_font_size=10,
    annotation_font_color=COLORS["warning"],
)
fig.add_hline(
    y=24, line_dash="dot", line_color=COLORS["danger"],
    annotation_text="24h (stale threshold)",
    annotation_position="top right",
    annotation_font_size=10,
    annotation_font_color=COLORS["danger"],
)

fig.update_layout(
    template="plotly_white",
    margin=dict(l=10, r=10, t=10, b=10), height=300,
    xaxis=dict(title=None, tickangle=-30),
    yaxis=dict(title="Hours Since Last Update"),
)
st.plotly_chart(fig, use_container_width=True)

# -- Legend --
st.markdown(
    "<div style='text-align:center;color:#94A3B8;font-size:0.8rem;'>"
    "<span style='color:#22C55E;'>&#9679;</span> Fresh (&lt;6h)"
    " &nbsp;&nbsp; "
    "<span style='color:#EAB308;'>&#9679;</span> Aging (6-24h)"
    " &nbsp;&nbsp; "
    "<span style='color:#EF4444;'>&#9679;</span> Stale (&gt;24h)"
    "</div>",
    unsafe_allow_html=True,
)

"""Executive overview — the full story at a glance."""

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
from taleemabad_data_mcp.dashboard.components.filters import get_refresh_seconds, render_filters
from taleemabad_data_mcp.dashboard.data.queries import (
    get_activity_log,
    get_feedback,
    get_table_freshness,
)

# -- Design system --
COLORS = {
    "primary": "#3B82F6",
    "secondary": "#60A5FA",
    "accent": "#F97316",
    "success": "#22C55E",
    "warning": "#EAB308",
    "danger": "#EF4444",
}

DOMAIN_COLORS = {
    "teachers": "#3B82F6",
    "lesson_plans": "#22C55E",
    "observations": "#F97316",
    "training": "#8B5CF6",
    "other": "#94A3B8",
}

CHART_H = 260

# -- Custom CSS --
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Fira Sans', system-ui, sans-serif; }
    .block-container { padding-top: 1.2rem; padding-bottom: 0.5rem; }

    /* KPI card with click-to-reveal info */
    .kpi-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 16px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        position: relative; min-height: 88px;
    }
    .kpi-card .kpi-label { font-weight: 500; color: #64748B; font-size: 0.82rem; }
    .kpi-card .kpi-value {
        font-size: 1.55rem; font-weight: 700; color: #1E293B; margin: 4px 0 0;
    }
    .kpi-card details { position: absolute; top: 8px; right: 10px; }
    .kpi-card details summary {
        width: 20px; height: 20px; border-radius: 50%;
        background: #F1F5F9; border: 1px solid #CBD5E1;
        color: #64748B; font-size: 11px; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; transition: all 0.2s;
        list-style: none; text-align: center; line-height: 20px;
    }
    .kpi-card details summary::-webkit-details-marker { display: none; }
    .kpi-card details summary:hover {
        background: #3B82F6; color: white; border-color: #3B82F6;
    }
    .kpi-card details[open] summary {
        background: #3B82F6; color: white; border-color: #3B82F6;
    }
    .kpi-card details .kpi-detail {
        position: absolute; top: 28px; right: 0;
        width: 280px; padding: 12px 14px; background: #1E293B;
        color: #F1F5F9; font-size: 0.78rem; font-weight: 400;
        border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        z-index: 200; line-height: 1.5;
    }
    .kpi-card details .kpi-detail::before {
        content: ''; position: absolute; top: -6px; right: 8px;
        border-left: 6px solid transparent; border-right: 6px solid transparent;
        border-bottom: 6px solid #1E293B;
    }
    .kpi-card details .kpi-detail strong { color: #60A5FA; }

    .section-header {
        font-size: 0.95rem; font-weight: 600; color: #1E293B;
        margin: 0.6rem 0 0.3rem 0; padding-bottom: 0.25rem;
        border-bottom: 2px solid #3B82F6;
    }
    .mini-stat { text-align: center; padding: 6px 0; }
    .mini-stat .value { font-size: 1.3rem; font-weight: 700; color: #1E293B; }
    .mini-stat .label { font-size: 0.75rem; color: #64748B; }
</style>
""", unsafe_allow_html=True)

# -- Header + filters --
st.markdown(
    '<h2 style="margin-bottom:0;color:#1E293B;">Taleemabad MCP Observatory</h2>'
    '<p style="color:#64748B;margin-top:0;margin-bottom:0.8rem;">'
    "Governed data layer — adoption, quality, cost at a glance</p>",
    unsafe_allow_html=True,
)

filters = render_filters()
inject_auto_refresh(get_refresh_seconds())
clear_cache_if_needed(get_refresh_seconds())
st.markdown("---")

df = get_activity_log(**filters)
fb = get_feedback(days=filters["days"])

if df.empty:
    st.info(
        "No activity data found. Use the MCP tools in Claude Code to generate data."
    )
    st.stop()

# -- Derived metrics --
real_queries = df[df["error_type"] != "dry_run"]
errors = real_queries[real_queries["error_type"].notna()]
successful = real_queries[real_queries["error_type"].isna()]
cost_df = df[df["cost_usd"].notna() & (df["cost_usd"] > 0)]

total_queries = len(real_queries)
active_users = df["user_name"].nunique()
total_cost = cost_df["cost_usd"].sum() if not cost_df.empty else 0
error_rate = len(errors) / total_queries * 100 if total_queries > 0 else 0
success_rate = len(successful) / total_queries * 100 if total_queries > 0 else 0

if not fb.empty:
    up_count = int((fb["rating"] == "up").sum())
    down_count = int((fb["rating"] == "down").sum())
    satisfaction = up_count / len(fb) * 100 if len(fb) > 0 else 0
    feedback_count = len(fb)
else:
    up_count, down_count, satisfaction, feedback_count = 0, 0, 0, 0

# Confidence = 70% success rate + 30% satisfaction
confidence = (
    success_rate * 0.7 + satisfaction * 0.3
    if feedback_count > 0 else success_rate
)

# ======================================================================
# ROW 1: KPI cards with click-to-reveal (!) info
# ======================================================================
KPI_HELP = {
    "Active Users": (
        "How many people are actually using this system. "
        "We count each person who asked at least one question "
        "in the selected time period. "
        "<br/><br/><strong>Why it matters:</strong> "
        "More active users means the team is adopting the governed data layer "
        "instead of writing their own queries."
    ),
    "Total Queries": (
        "The total number of questions people asked the system. "
        "This only counts real questions — not cost estimates (dry runs). "
        "It includes both questions that got answers and ones that failed."
        "<br/><br/><strong>Why it matters:</strong> "
        "Growing query volume means the system is becoming the go-to source "
        "for data questions."
    ),
    "Confidence": (
        "How much we can trust the system to give correct answers. "
        "This is a combined score made of two parts:"
        "<br/><br/><strong>70%</strong> comes from the "
        "<strong>success rate</strong> — "
        "how often queries run without errors."
        "<br/><strong>30%</strong> comes from "
        "<strong>user satisfaction</strong> — "
        "how often people give a thumbs up to the answers they receive."
        "<br/><br/><strong>How to read it:</strong> "
        "90%+ is excellent. 70-90% is good. Below 70% needs attention. "
        "If confidence is low, check the Errors page to see what is failing."
    ),
    "Satisfaction": (
        "When someone gets an answer, they can optionally give it a "
        "thumbs up or thumbs down. This number shows the percentage "
        "of thumbs up out of all ratings received."
        "<br/><br/><strong>How it works:</strong> "
        "Feedback is completely voluntary — no one is forced to rate. "
        "So this reflects genuine user sentiment, not forced surveys."
        "<br/><br/><strong>N/A</strong> means nobody has given feedback yet."
        "<br/><strong>Why it matters:</strong> "
        "Even if queries succeed technically, satisfaction tells us if "
        "the answers actually matched what people expected."
    ),
    "Error Rate": (
        "The percentage of questions that failed to get an answer. "
        "Failures happen when a query has a syntax problem, "
        "the user does not have permission, or the requested table "
        "does not exist."
        "<br/><br/><strong>How to read it:</strong> "
        "Below 5% is healthy. Above 10% needs investigation. "
        "Check the Errors page to see which types of errors are happening "
        "and which questions are failing."
    ),
    "Total Cost": (
        "How much money was spent on BigQuery to answer all these questions. "
        "BigQuery charges based on how much data each query scans."
        "<br/><br/><strong>How it is calculated:</strong> "
        "Google charges $6.25 for every terabyte (TB) of data scanned. "
        "We track the exact bytes each query uses and convert to dollars."
        "<br/><br/><strong>Why it matters:</strong> "
        "This helps ensure the system stays cost-efficient. "
        "Check the Cost page to see who is running expensive queries."
    ),
}

kpi_data = [
    ("Active Users", str(active_users)),
    ("Total Queries", f"{total_queries:,}"),
    ("Confidence", f"{confidence:.0f}%"),
    ("Satisfaction", f"{satisfaction:.0f}%" if feedback_count else "N/A"),
    ("Error Rate", f"{error_rate:.1f}%"),
    ("Total Cost", f"${total_cost:.2f}"),
]


def _kpi_html(label: str, value: str, info: str) -> str:
    """KPI card HTML with click-to-reveal info button."""
    return (
        f'<div class="kpi-card">'
        f"<details><summary>!</summary>"
        f'<div class="kpi-detail">{info}</div>'
        f"</details>"
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f"</div>"
    )


cols = st.columns(6)
for col, (label, value) in zip(cols, kpi_data, strict=True):
    with col:
        st.markdown(
            _kpi_html(label, value, KPI_HELP[label]),
            unsafe_allow_html=True,
        )

st.markdown("")

# ======================================================================
# ROW 2: Activity trend + Domain breakdown (3:2)
# ======================================================================
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown(
        '<div class="section-header">Activity Trend</div>',
        unsafe_allow_html=True,
    )
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    daily = df.groupby("date").agg(
        queries=("event_id", "count"),
        users=("user_name", "nunique"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["queries"],
        name="Queries", mode="lines+markers",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=4),
    ))
    fig.add_trace(go.Bar(
        x=daily["date"], y=daily["users"],
        name="Unique Users", yaxis="y2",
        marker_color=COLORS["secondary"], opacity=0.35,
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=CHART_H,
        legend=dict(orientation="h", yanchor="top", y=1.12, x=0),
        yaxis=dict(title=None, showgrid=True, gridcolor="#F1F5F9"),
        yaxis2=dict(
            title=None, overlaying="y", side="right", showgrid=False,
        ),
        xaxis=dict(title=None),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown(
        '<div class="section-header">Queries by Domain</div>',
        unsafe_allow_html=True,
    )
    domain_counts = (
        df.groupby("domain").size().reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    colors = [
        DOMAIN_COLORS.get(d, "#94A3B8") for d in domain_counts["domain"]
    ]
    fig = go.Figure(go.Pie(
        labels=domain_counts["domain"],
        values=domain_counts["count"],
        hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+percent",
        textposition="outside",
        textfont_size=11,
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=CHART_H,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# ======================================================================
# ROW 3: Feedback + Cost + Top Users (equal 3 columns)
# ======================================================================
r3a, r3b, r3c = st.columns(3)

with r3a:
    st.markdown(
        '<div class="section-header">Feedback Snapshot</div>',
        unsafe_allow_html=True,
    )
    fc1, fc2, fc3 = st.columns(3)
    fc1.markdown(
        f'<div class="mini-stat"><div class="value" style="color:#22C55E;">'
        f"{up_count}</div><div class='label'>Thumbs Up</div></div>",
        unsafe_allow_html=True,
    )
    fc2.markdown(
        f'<div class="mini-stat"><div class="value" style="color:#EF4444;">'
        f"{down_count}</div><div class='label'>Thumbs Down</div></div>",
        unsafe_allow_html=True,
    )
    rated_pct = feedback_count / total_queries * 100 if total_queries else 0
    fc3.markdown(
        f'<div class="mini-stat"><div class="value">'
        f"{rated_pct:.0f}%</div><div class='label'>Rated</div></div>",
        unsafe_allow_html=True,
    )
    if not fb.empty:
        fb_domain = fb.groupby("domain")["rating"].apply(
            lambda x: (x == "up").sum() / len(x) * 100
        ).reset_index(name="sat_pct")
        fb_domain = fb_domain.sort_values("sat_pct", ascending=True)
        d_colors = [
            DOMAIN_COLORS.get(d, "#94A3B8") for d in fb_domain["domain"]
        ]
        fig = go.Figure(go.Bar(
            x=fb_domain["sat_pct"], y=fb_domain["domain"],
            orientation="h", marker_color=d_colors,
            text=[f"{v:.0f}%" for v in fb_domain["sat_pct"]],
            textposition="auto",
        ))
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=10, r=10, t=5, b=10),
            height=160, xaxis=dict(title=None, range=[0, 100]),
            yaxis=dict(title=None),
        )
        st.plotly_chart(fig, use_container_width=True)

with r3b:
    st.markdown(
        '<div class="section-header">Cost by Domain</div>',
        unsafe_allow_html=True,
    )
    total_bytes = cost_df["cost_bytes"].sum() if not cost_df.empty else 0
    avg_cost = cost_df["cost_usd"].mean() if not cost_df.empty else 0
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(
        f'<div class="mini-stat"><div class="value">'
        f"${total_cost:.2f}</div><div class='label'>Total</div></div>",
        unsafe_allow_html=True,
    )
    cc2.markdown(
        f'<div class="mini-stat"><div class="value">'
        f"{total_bytes / (1024 ** 3):.1f} GB</div>"
        f"<div class='label'>Scanned</div></div>",
        unsafe_allow_html=True,
    )
    cc3.markdown(
        f'<div class="mini-stat"><div class="value">'
        f"${avg_cost:.4f}</div><div class='label'>Avg/Query</div></div>",
        unsafe_allow_html=True,
    )
    if not cost_df.empty:
        cost_by_domain = (
            cost_df.groupby("domain")["cost_usd"]
            .sum().reset_index().sort_values("cost_usd", ascending=True)
        )
        d_colors = [
            DOMAIN_COLORS.get(d, "#94A3B8")
            for d in cost_by_domain["domain"]
        ]
        fig = go.Figure(go.Bar(
            x=cost_by_domain["cost_usd"],
            y=cost_by_domain["domain"],
            orientation="h", marker_color=d_colors,
            text=[f"${v:.3f}" for v in cost_by_domain["cost_usd"]],
            textposition="auto",
        ))
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=10, r=10, t=5, b=10),
            height=160, xaxis=dict(title=None),
            yaxis=dict(title=None),
        )
        st.plotly_chart(fig, use_container_width=True)

with r3c:
    st.markdown(
        '<div class="section-header">Most Active Users</div>',
        unsafe_allow_html=True,
    )
    queries_per_user = total_queries / active_users if active_users else 0
    top_user = real_queries["user_name"].value_counts()
    top_count = int(top_user.iloc[0]) if len(top_user) > 0 else 0
    uc1, uc2, uc3 = st.columns(3)
    uc1.markdown(
        f'<div class="mini-stat"><div class="value">'
        f"{active_users}</div><div class='label'>Users</div></div>",
        unsafe_allow_html=True,
    )
    uc2.markdown(
        f'<div class="mini-stat"><div class="value">'
        f"{queries_per_user:.0f}</div>"
        f"<div class='label'>Avg Queries</div></div>",
        unsafe_allow_html=True,
    )
    uc3.markdown(
        f'<div class="mini-stat"><div class="value">'
        f"{top_count}</div>"
        f"<div class='label'>Top User</div></div>",
        unsafe_allow_html=True,
    )
    user_activity = (
        real_queries.groupby("user_name")
        .size().reset_index(name="queries")
        .sort_values("queries", ascending=True).tail(7)
    )
    fig = go.Figure(go.Bar(
        x=user_activity["queries"],
        y=user_activity["user_name"],
        orientation="h",
        marker_color=COLORS["primary"],
        text=user_activity["queries"],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=5, b=10),
        height=160, xaxis=dict(title=None),
        yaxis=dict(title=None),
    )
    st.plotly_chart(fig, use_container_width=True)

# ======================================================================
# ROW 4: Errors + Freshness + Recent Feedback (equal 3 columns)
# ======================================================================
r4a, r4b, r4c = st.columns(3)

with r4a:
    st.markdown(
        '<div class="section-header">Error Summary</div>',
        unsafe_allow_html=True,
    )
    if not errors.empty:
        err_types = (
            errors.groupby("error_type")
            .size().reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        for _, row in err_types.iterrows():
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:5px 0;border-bottom:1px solid #F1F5F9;'>"
                f"<span style='color:#64748B;'>{row['error_type']}</span>"
                f"<span style='font-weight:600;color:#EF4444;'>"
                f"{row['count']}</span></div>",
                unsafe_allow_html=True,
            )
    else:
        st.success("No errors in this period")

with r4b:
    st.markdown(
        '<div class="section-header">Data Freshness</div>',
        unsafe_allow_html=True,
    )
    try:
        freshness = get_table_freshness()
        if not freshness.empty:
            from datetime import UTC, datetime
            now = datetime.now(UTC)
            for _, row in freshness.iterrows():
                if pd.notna(row["last_modified"]):
                    hours = (
                        now - row["last_modified"].replace(tzinfo=UTC)
                    ).total_seconds() / 3600
                    if hours < 6:
                        dot = (
                            '<span style="color:#22C55E;">&#9679;</span>'
                        )
                    elif hours < 24:
                        dot = (
                            '<span style="color:#EAB308;">&#9679;</span>'
                        )
                    else:
                        dot = (
                            '<span style="color:#EF4444;">&#9679;</span>'
                        )
                    st.markdown(
                        f"<div style='display:flex;"
                        f"justify-content:space-between;"
                        f"padding:4px 0;border-bottom:1px solid #F1F5F9;"
                        f"font-size:0.85rem;'>"
                        f"<span>{dot} {row['table_name']}</span>"
                        f"<span style='color:#64748B;'>"
                        f"{hours:.0f}h ago</span></div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No freshness data")
    except Exception:
        st.warning("Could not load freshness data")

with r4c:
    st.markdown(
        '<div class="section-header">Recent Feedback</div>',
        unsafe_allow_html=True,
    )
    if not fb.empty:
        recent = fb.head(6)
        for _, row in recent.iterrows():
            icon = (
                '<span style="color:#22C55E;">&#9650;</span>'
                if row["rating"] == "up"
                else '<span style="color:#EF4444;">&#9660;</span>'
            )
            q = str(row.get("query_text", ""))[:45]
            comment = (
                str(row.get("comment", ""))
                if pd.notna(row.get("comment")) else ""
            )
            comment_html = (
                "<br/><em style='color:#64748B;font-size:0.8rem;'>"
                + comment + "</em>"
                if comment else ""
            )
            st.markdown(
                f"<div style='padding:4px 0;"
                f"border-bottom:1px solid #F1F5F9;"
                f"font-size:0.85rem;'>"
                f"{icon} <strong>{row['user_name']}</strong>: {q}"
                f"{comment_html}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No feedback yet")

# -- Footer --
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#94A3B8;font-size:0.8rem;">'
    "Use the sidebar for deep dives into Query Analytics, "
    "Feedback, Cost, Errors, or Freshness.</p>",
    unsafe_allow_html=True,
)

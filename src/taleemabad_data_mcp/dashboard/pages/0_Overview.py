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

    /* Section containers — colored backgrounds to separate groups.
       Uses outline + background on the Streamlit column wrapper via
       adjacent-sibling targeting. We inject open/close divs around content. */
    .section-box {
        border-radius: 14px; padding: 18px 16px 14px 16px;
        margin-bottom: 8px; min-height: 100%;
    }
    .section-box-blue {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 2px solid #93C5FD;
    }
    .section-box-green {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 2px solid #86EFAC;
    }
    .section-box-orange {
        background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
        border: 2px solid #FDBA74;
    }
    .section-box-purple {
        background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%);
        border: 2px solid #C4B5FD;
    }
    .section-box-slate {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
        border: 2px solid #CBD5E1;
    }
    .section-box-red {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 2px solid #FCA5A5;
    }

    .section-box .section-header { margin-top: 0; }
    .section-box .kpi-card { background: rgba(255,255,255,0.85); }
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
# ROW 3: Feedback + Cost + Top Users — KPI tiles + bar charts
# ======================================================================
rated_pct = feedback_count / total_queries * 100 if total_queries else 0
total_bytes = cost_df["cost_bytes"].sum() if not cost_df.empty else 0
avg_cost = cost_df["cost_usd"].mean() if not cost_df.empty else 0
queries_per_user = total_queries / active_users if active_users else 0
top_user_series = real_queries["user_name"].value_counts()
top_user_name = top_user_series.index[0] if len(top_user_series) > 0 else "—"

TILE = (
    '<div class="kpi-card" style="min-height:70px;text-align:center;">'
    '<div class="kpi-label">{label}</div>'
    '<div class="kpi-value"{style}>{value}</div></div>'
)

r3a, r3b, r3c = st.columns(3)

with r3a:
    st.markdown('<div class="section-box section-box-green">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Feedback Snapshot</div>',
                unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    fc1.markdown(TILE.format(label="Thumbs Up", value=up_count,
                             style=' style="color:#22C55E;"'), unsafe_allow_html=True)
    fc2.markdown(TILE.format(label="Thumbs Down", value=down_count,
                             style=' style="color:#EF4444;"'), unsafe_allow_html=True)
    fc3.markdown(TILE.format(label="Rated", value=f"{rated_pct:.0f}%",
                             style=""), unsafe_allow_html=True)
    if not fb.empty:
        fb_domain = fb.groupby("domain")["rating"].apply(
            lambda x: (x == "up").sum() / len(x) * 100
        ).reset_index(name="sat_pct").sort_values("sat_pct", ascending=True)
        fig = go.Figure(go.Bar(
            x=fb_domain["sat_pct"], y=fb_domain["domain"], orientation="h",
            marker_color=[DOMAIN_COLORS.get(d, "#94A3B8") for d in fb_domain["domain"]],
            text=[f"{v:.0f}%" for v in fb_domain["sat_pct"]], textposition="auto",
        ))
        fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=5, b=10),
                          height=150, xaxis=dict(title=None, range=[0, 100]),
                          yaxis=dict(title=None), plot_bgcolor="rgba(0,0,0,0)",
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r3b:
    st.markdown('<div class="section-box section-box-orange">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Cost by Domain</div>',
                unsafe_allow_html=True)
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(TILE.format(label="Total Cost", value=f"${total_cost:.2f}",
                             style=""), unsafe_allow_html=True)
    cc2.markdown(TILE.format(label="Data Scanned",
                             value=f"{total_bytes / (1024 ** 3):.1f} GB",
                             style=""), unsafe_allow_html=True)
    cc3.markdown(TILE.format(label="Avg/Query", value=f"${avg_cost:.4f}",
                             style=""), unsafe_allow_html=True)
    if not cost_df.empty:
        cost_by_domain = (
            cost_df.groupby("domain")["cost_usd"]
            .sum().reset_index().sort_values("cost_usd", ascending=True)
        )
        fig = go.Figure(go.Bar(
            x=cost_by_domain["cost_usd"], y=cost_by_domain["domain"], orientation="h",
            marker_color=[DOMAIN_COLORS.get(d, "#94A3B8") for d in cost_by_domain["domain"]],
            text=[f"${v:.3f}" for v in cost_by_domain["cost_usd"]], textposition="auto",
        ))
        fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=5, b=10),
                          height=150, xaxis=dict(title=None), yaxis=dict(title=None),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r3c:
    st.markdown('<div class="section-box section-box-blue">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Most Active Users</div>',
                unsafe_allow_html=True)
    uc1, uc2, uc3 = st.columns(3)
    uc1.markdown(TILE.format(label="Users", value=active_users,
                             style=""), unsafe_allow_html=True)
    uc2.markdown(TILE.format(label="Avg Queries", value=f"{queries_per_user:.0f}",
                             style=""), unsafe_allow_html=True)
    uc3.markdown(TILE.format(label="Top User", value=top_user_name,
                             style=""), unsafe_allow_html=True)
    user_activity = (
        real_queries.groupby("user_name")
        .size().reset_index(name="queries")
        .sort_values("queries", ascending=True).tail(7)
    )
    fig = go.Figure(go.Bar(
        x=user_activity["queries"], y=user_activity["user_name"], orientation="h",
        marker_color=COLORS["primary"],
        text=user_activity["queries"], textposition="auto",
    ))
    fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=5, b=10),
                      height=150, xaxis=dict(title=None), yaxis=dict(title=None),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# ROW 4: Errors + Freshness + Feedback — summary KPI cards
# ======================================================================
error_count = len(errors)
error_types_count = errors["error_type"].nunique() if not errors.empty else 0

try:
    freshness = get_table_freshness()
    if not freshness.empty:
        from datetime import UTC, datetime
        now = datetime.now(UTC)
        freshness["hours_ago"] = freshness["last_modified"].apply(
            lambda ts: (now - ts.replace(tzinfo=UTC)).total_seconds() / 3600
            if pd.notna(ts) else None
        )
        fresh_count = int((freshness["hours_ago"] < 6).sum())
        stale_count = int((freshness["hours_ago"] >= 24).sum())
        tables_tracked = len(freshness)
    else:
        fresh_count, stale_count, tables_tracked = 0, 0, 0
except Exception:
    fresh_count, stale_count, tables_tracked = 0, 0, 0

r4a, r4b, r4c = st.columns(3)

with r4a:
    st.markdown('<div class="section-box section-box-red">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Errors</div>', unsafe_allow_html=True)
    ec1, ec2 = st.columns(2)
    err_color = COLORS["success"] if error_count == 0 else COLORS["danger"]
    ec1.markdown(TILE.format(label="Failed Queries", value=error_count,
                             style=f' style="color:{err_color};"'), unsafe_allow_html=True)
    ec2.markdown(TILE.format(label="Error Types", value=error_types_count,
                             style=""), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4b:
    st.markdown('<div class="section-box section-box-purple">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Data Freshness</div>', unsafe_allow_html=True)
    dc1, dc2, dc3 = st.columns(3)
    dc1.markdown(TILE.format(label="Tables", value=tables_tracked,
                             style=""), unsafe_allow_html=True)
    dc2.markdown(TILE.format(label="Fresh (&lt;6h)", value=fresh_count,
                             style=f' style="color:{COLORS["success"]};"'),
                 unsafe_allow_html=True)
    dc3.markdown(TILE.format(label="Stale (&gt;24h)", value=stale_count,
                             style=f' style="color:{COLORS["danger"]};"'),
                 unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r4c:
    st.markdown('<div class="section-box section-box-slate">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Feedback</div>', unsafe_allow_html=True)
    fbc1, fbc2 = st.columns(2)
    fbc1.markdown(TILE.format(label="Total Ratings", value=feedback_count,
                              style=""), unsafe_allow_html=True)
    sat_display = f"{satisfaction:.0f}%" if feedback_count > 0 else "N/A"
    sat_color = COLORS["success"] if satisfaction >= 70 else COLORS["warning"]
    fbc2.markdown(TILE.format(label="Satisfaction", value=sat_display,
                              style=f' style="color:{sat_color};"'), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# ROW 5: Action Items — auto-generated from data
# ======================================================================
st.markdown("")
st.markdown('<div class="section-header">Action Items</div>', unsafe_allow_html=True)

actions = []

# Check for errors
if error_count > 0:
    top_err = errors["error_type"].value_counts().index[0]
    actions.append({
        "icon": "&#9888;",  # warning
        "color": COLORS["danger"],
        "title": f"{error_count} failed queries",
        "detail": f"Most common: <strong>{top_err}</strong> — check the Errors tab",
        "priority": "high",
    })

# Check for stale tables
if stale_count > 0:
    stale_names = freshness[freshness["hours_ago"] >= 24]["table_name"].tolist()[:3]
    stale_preview = ", ".join(stale_names)
    actions.append({
        "icon": "&#9203;",  # clock
        "color": COLORS["warning"],
        "title": f"{stale_count} stale tables (>24h)",
        "detail": f"Including: <strong>{stale_preview}</strong> — data pipeline may need attention",
        "priority": "medium",
    })

# Check for misconfigured users
bad_users = [u for u in df["user_name"].unique() if "${" in str(u) or u == "unknown"]
if bad_users:
    actions.append({
        "icon": "&#128100;",  # person
        "color": COLORS["warning"],
        "title": f"{len(bad_users)} misconfigured user(s)",
        "detail": f"Users logged as <strong>{', '.join(bad_users)}</strong> — "
                  "they need to run <code>/taleemabad-setup</code> or update to v0.12.3+",
        "priority": "medium",
    })

# Check for no feedback
if feedback_count == 0 and total_queries > 10:
    actions.append({
        "icon": "&#128172;",  # speech bubble
        "color": COLORS["secondary"],
        "title": "No user feedback yet",
        "detail": f"{total_queries} queries but 0 ratings — "
                  "consider encouraging team to give thumbs up/down on results",
        "priority": "low",
    })

# Check for low adoption (few users)
if active_users < 3 and total_queries > 0:
    actions.append({
        "icon": "&#128101;",  # group
        "color": COLORS["secondary"],
        "title": f"Low adoption — only {active_users} user(s)",
        "detail": "Consider onboarding more team members to the governed data layer",
        "priority": "low",
    })

# Check for high error rate
if error_rate > 10:
    actions.append({
        "icon": "&#9762;",  # biohazard
        "color": COLORS["danger"],
        "title": f"High error rate: {error_rate:.0f}%",
        "detail": "More than 1 in 10 queries are failing — review query patterns and rule coverage",
        "priority": "high",
    })

# All clear
if not actions:
    st.markdown(
        '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;'
        'padding:16px;text-align:center;color:#166534;">'
        '&#10004; All clear — no action items right now</div>',
        unsafe_allow_html=True,
    )
else:
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: priority_order.get(a["priority"], 9))

    for action in actions:
        bg = "#FEF2F2" if action["priority"] == "high" else (
            "#FFFBEB" if action["priority"] == "medium" else "#F8FAFC"
        )
        border = action["color"]
        st.markdown(
            f'<div style="background:{bg};border-left:4px solid {border};'
            f'border-radius:8px;padding:12px 16px;margin-bottom:8px;'
            f'box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
            f'<div style="font-weight:600;color:#1E293B;">'
            f'{action["icon"]} {action["title"]}</div>'
            f'<div style="color:#64748B;font-size:0.85rem;margin-top:4px;">'
            f'{action["detail"]}</div></div>',
            unsafe_allow_html=True,
        )

# -- Footer --
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#94A3B8;font-size:0.8rem;">'
    "Use the sidebar for deep dives into Query Analytics, "
    "Feedback, Cost, Errors, or Freshness.</p>",
    unsafe_allow_html=True,
)

"""Freshness — actionable data pipeline health.

Thresholds:
- Fresh: < 24 hours since last update
- Aging: 24h–72h (1–3 days) — OK but flagged
- Stale: > 72h (3+ days) — critical, needs attention

Scope: tables that users actually query (from audit log).
"""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

from datetime import UTC, datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from custom_data_mcp.dashboard.components.styles import (
    COLORS, inject_page_css, page_header, section_header,
)
from custom_data_mcp.dashboard.data.queries import (
    get_table_freshness,
    get_dataset_freshness,
)

inject_page_css()

# ── Page CSS ──
st.markdown("""
<style>
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.25); }
        50% { box-shadow: 0 0 0 6px rgba(239,68,68,0); }
    }
    .stale-alert { animation: pulse-red 2.5s ease-in-out infinite; }
    .freshness-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .freshness-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }
    .domain-row { transition: background 0.15s ease; }
    .domain-row:hover { background: rgba(0,0,0,0.03) !important; }

    .status-icon {
        display: inline-flex; align-items: center; justify-content: center;
        width: 18px; height: 18px; border-radius: 50%;
        font-size: 10px; font-weight: 700; line-height: 1;
    }
    .status-icon--fresh { background: #D1FAE5; color: #065F46; }
    .status-icon--aging { background: #FEF3C7; color: #92400E; border-radius: 3px; }
    .status-icon--stale { background: #FEE2E2; color: #991B1B; border-radius: 2px;
        transform: rotate(45deg); }
    .status-icon--stale span { transform: rotate(-45deg); display: block; }
</style>
""", unsafe_allow_html=True)

page_header(
    "Data Freshness",
    "Pipeline health — tables queried by users, grouped by dataset, with actionable alerts",
)

# ── Thresholds (user requirements) ──
FRESH_HOURS = 24       # < 24h = Fresh
AGING_HOURS = 72       # 24h–72h = Aging (OK with alert)
# > 72h = Stale (critical)

# ── Table metadata ──
TABLE_INFO = {
    # ICT / tbproddb
    "user_school_profiles": {"dataset": "tbproddb", "domain": "Teachers", "desc": "Teacher-school assignments", "priority": "high"},
    "events_partitioned": {"dataset": "tbproddb", "domain": "Lesson Plans", "desc": "App events (LP, training)", "priority": "high"},
    "analytics_events": {"dataset": "tbproddb", "domain": "Events", "desc": "Canonical event table (70M+ rows)", "priority": "critical"},
    "coaching_observation": {"dataset": "tbproddb", "domain": "Observations", "desc": "FICO observation records", "priority": "high"},
    "coaching_observationanswer": {"dataset": "tbproddb", "domain": "Observations", "desc": "Per-question answers", "priority": "medium"},
    "coaching_observationquestion": {"dataset": "tbproddb", "domain": "Observations", "desc": "Question metadata", "priority": "low"},
    "coaching_questionoption": {"dataset": "tbproddb", "domain": "Observations", "desc": "Answer options", "priority": "low"},
    "coaching_teachervisit": {"dataset": "tbproddb", "domain": "Observations", "desc": "Teacher-visit links", "priority": "medium"},
    "teacher_training_level": {"dataset": "tbproddb", "domain": "Training", "desc": "Level definitions", "priority": "low"},
    "teacher_training_assessment": {"dataset": "tbproddb", "domain": "Training", "desc": "Assessment scores", "priority": "high"},
    "lp_info_all_types": {"dataset": "tbproddb", "domain": "Lesson Plans", "desc": "Pre-computed LP data", "priority": "high"},
    "FDE_Schools": {"dataset": "tbproddb", "domain": "Teachers", "desc": "ICT school reference", "priority": "low"},
    "users_user": {"dataset": "tbproddb", "domain": "Teachers", "desc": "Base user table", "priority": "medium"},
    "users_teacherprofile": {"dataset": "tbproddb", "domain": "Teachers", "desc": "Teacher profiles", "priority": "medium"},
    "schools_school": {"dataset": "tbproddb", "domain": "Teachers", "desc": "School details", "priority": "low"},
    "Fico_Observations": {"dataset": "tbproddb", "domain": "Observations", "desc": "Pre-processed summaries", "priority": "medium"},
    # RWP
    "lesson_plans": {"dataset": "RUMI_DB", "domain": "LP (RWP)", "desc": "Rumi AI lesson plans", "priority": "high"},
    "coaching_sessions": {"dataset": "RUMI_DB", "domain": "Coaching (RWP)", "desc": "AI coaching sessions", "priority": "high"},
    "coaching_quality_metrics": {"dataset": "RUMI_DB", "domain": "Coaching (RWP)", "desc": "Coaching quality", "priority": "medium"},
    "reading_assessments": {"dataset": "RUMI_DB", "domain": "Students (RWP)", "desc": "Reading assessments", "priority": "high"},
    "mentoring_visits": {"dataset": "TaleemHub_DB", "domain": "Coaching (RWP)", "desc": "Human mentoring visits", "priority": "medium"},
    "users": {"dataset": "RUMI_DB", "domain": "Users (RWP)", "desc": "User records", "priority": "medium"},
    "aser_assessments": {"dataset": "TaleemHub_DB", "domain": "Students (RWP)", "desc": "ASER sessions", "priority": "medium"},
    "aser_assessment_results": {"dataset": "TaleemHub_DB", "domain": "Students (RWP)", "desc": "ASER rubric scores", "priority": "medium"},
}
_DEFAULT_INFO = {"dataset": "unknown", "domain": "Other", "desc": "Queried by users", "priority": "low"}

_DATASET_LABELS = {
    "tbproddb": "ICT/Islamabad",
    "RUMI_DB": "Rumi AI (RWP)",
    "TaleemHub_DB": "TaleemHub (RWP)",
}
_DATASET_COLORS = {
    "tbproddb": "#3B82F6",
    "RUMI_DB": "#8B5CF6",
    "TaleemHub_DB": "#14B8A6",
}

_STATUS_CFG = {
    "Fresh":   {"color": "#10B981", "bg": "#D1FAE5", "icon": '<span class="status-icon status-icon--fresh">&#10003;</span>', "label": "Fresh (<24h)"},
    "Aging":   {"color": "#F59E0B", "bg": "#FEF3C7", "icon": '<span class="status-icon status-icon--aging">!</span>', "label": "Aging (1-3d)"},
    "Stale":   {"color": "#EF4444", "bg": "#FEE2E2", "icon": '<span class="status-icon status-icon--stale"><span>&#10005;</span></span>', "label": "Stale (>3d)"},
    "Unknown": {"color": "#94A3B8", "bg": "#F1F5F9", "icon": '<span class="status-icon" style="background:#F1F5F9;color:#64748B;">?</span>', "label": "Unknown"},
}

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_PRIORITY_BADGE = {
    "critical": '<span style="background:#FEE2E2;color:#991B1B;border-radius:4px;padding:1px 6px;font-size:0.7rem;font-weight:700;">CRITICAL</span>',
    "high": '<span style="background:#FEF3C7;color:#92400E;border-radius:4px;padding:1px 6px;font-size:0.7rem;font-weight:700;">HIGH</span>',
    "medium": '<span style="background:#DBEAFE;color:#1E40AF;border-radius:4px;padding:1px 6px;font-size:0.7rem;font-weight:700;">MED</span>',
    "low": '<span style="background:#F1F5F9;color:#475569;border-radius:4px;padding:1px 6px;font-size:0.7rem;font-weight:700;">LOW</span>',
}

# ── Load data ──
try:
    df = get_table_freshness()
except Exception as e:
    st.error(f"Could not connect to BigQuery: {e}")
    st.stop()

if df.empty:
    st.warning("No freshness data. Tables may not exist or permissions missing.")
    st.stop()

try:
    ds_freshness = get_dataset_freshness()
except Exception:
    ds_freshness = pd.DataFrame()

now = datetime.now(UTC)

# ── Enrich table data ──
df["hours_ago"] = df["last_modified"].apply(
    lambda ts: (now - ts.replace(tzinfo=UTC)).total_seconds() / 3600 if pd.notna(ts) else None
)
df["days_ago"] = df["hours_ago"].apply(lambda h: h / 24 if pd.notna(h) else None)
df["src_dataset"] = df["table_name"].apply(lambda t: TABLE_INFO.get(t, _DEFAULT_INFO)["dataset"])
# Use actual dataset from BQ if available, fall back to metadata
df["display_dataset"] = df.apply(
    lambda r: r["dataset"] if pd.notna(r.get("dataset")) else r["src_dataset"], axis=1
)
df["domain"] = df["table_name"].apply(lambda t: TABLE_INFO.get(t, _DEFAULT_INFO)["domain"])
df["priority"] = df["table_name"].apply(lambda t: TABLE_INFO.get(t, _DEFAULT_INFO)["priority"])
df["desc"] = df["table_name"].apply(lambda t: TABLE_INFO.get(t, _DEFAULT_INFO)["desc"])
df["status"] = df["hours_ago"].apply(
    lambda h: "Fresh" if pd.notna(h) and h < FRESH_HOURS else (
        "Aging" if pd.notna(h) and h < AGING_HOURS else ("Stale" if pd.notna(h) else "Unknown")
    )
)

# ── Metrics ──
fresh_count = int((df["status"] == "Fresh").sum())
aging_count = int((df["status"] == "Aging").sum())
stale_count = int((df["status"] == "Stale").sum())
total_tables = len(df)

# Pipeline health = weighted score: fresh=100, aging=50, stale=0
health_score = round(
    (fresh_count * 100 + aging_count * 50) / total_tables
) if total_tables > 0 else 0

if health_score >= 80:
    health_grade, grade_color, grade_bg = "Healthy", "#065F46", "#D1FAE5"
elif health_score >= 50:
    health_grade, grade_color, grade_bg = "Degraded", "#92400E", "#FEF3C7"
else:
    health_grade, grade_color, grade_bg = "Critical", "#991B1B", "#FEE2E2"

avg_age = df["hours_ago"].mean() if not df["hours_ago"].isna().all() else 0
oldest_hours = df["hours_ago"].max() if not df["hours_ago"].isna().all() else 0

critical_stale = df[(df["status"] == "Stale") & (df["priority"].isin(["critical", "high"]))]

# ======================================================================
# ROW 1: Symmetrical — KPIs | Gauge | KPIs
# ======================================================================

# Full-width stacked status bar
status_html = (
    '<div style="display:flex;border-radius:8px;overflow:hidden;height:28px;margin-bottom:14px;">'
)
for label, count, color in [("Fresh", fresh_count, "#10B981"), ("Aging", aging_count, "#F59E0B"), ("Stale", stale_count, "#EF4444")]:
    pct = count / total_tables * 100 if total_tables > 0 else 0
    if pct > 0:
        status_html += (
            f'<div style="width:{pct}%;background:{color};display:flex;align-items:center;'
            f'justify-content:center;color:white;font-size:0.75rem;font-weight:700;'
            f'min-width:40px;" title="{label}: {count} tables ({pct:.0f}%)">'
            f'{label} {count}</div>'
        )
status_html += '</div>'
st.markdown(status_html, unsafe_allow_html=True)

# Thresholds reminder
st.markdown(
    '<div style="text-align:center;font-size:0.78rem;color:#475569;margin-bottom:10px;">'
    '<span style="color:#10B981;font-weight:700;">Fresh</span> = updated within 24h'
    ' &nbsp;|&nbsp; '
    '<span style="color:#F59E0B;font-weight:700;">Aging</span> = 1-3 days'
    ' &nbsp;|&nbsp; '
    '<span style="color:#EF4444;font-weight:700;">Stale</span> = more than 3 days'
    '</div>',
    unsafe_allow_html=True,
)

# Symmetrical 3-col: KPIs | Gauge | KPIs — equal card heights via fixed HTML
_CARD = (
    '<div style="background:white;border:1px solid #E2E8F0;border-radius:12px;'
    'padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);'
    'border-top:3px solid {accent};height:88px;display:flex;flex-direction:column;justify-content:center;">'
    '<div style="font-size:0.75rem;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:0.04em;">{label}</div>'
    '<div style="font-size:1.5rem;font-weight:800;color:{value_color};margin-top:2px;letter-spacing:-0.02em;">{value}</div>'
    '{sub}'
    '</div>'
)

alert_count = len(critical_stale)
oldest_display = f"{oldest_hours / 24:.1f}d" if oldest_hours >= 24 else f"{oldest_hours:.0f}h"

col_l, col_c, col_r = st.columns([1, 1, 1])

with col_l:
    st.markdown(_CARD.format(
        accent="#3B82F6", label="User-Queried Tables", value=total_tables,
        value_color="#0F172A", sub='<div style="font-size:0.7rem;color:#475569;margin-top:2px;">from audit log (30 days)</div>',
    ), unsafe_allow_html=True)
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    st.markdown(_CARD.format(
        accent="#8B5CF6", label="Avg Table Age", value=f"{avg_age / 24:.1f} days",
        value_color="#0F172A", sub='<div style="font-size:0.7rem;color:#475569;margin-top:2px;">across all queried tables</div>',
    ), unsafe_allow_html=True)

with col_c:
    gauge_color = "#10B981" if health_score >= 70 else ("#F59E0B" if health_score >= 40 else "#EF4444")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health_score,
        number=dict(suffix="%", font=dict(size=40, color="#0F172A", family="Inter")),
        title=dict(
            text=f"<b style='color:{grade_color}'>{health_grade}</b>",
            font=dict(size=13, color="#475569"),
        ),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(size=9), tickcolor="#CBD5E1"),
            bar=dict(color=gauge_color, thickness=0.65),
            bgcolor="#F8FAFC", borderwidth=0,
            steps=[
                dict(range=[0, 40], color="#FEE2E2"),
                dict(range=[40, 70], color="#FEF3C7"),
                dict(range=[70, 100], color="#D1FAE5"),
            ],
            threshold=dict(line=dict(color="#0F172A", width=2), thickness=0.75, value=health_score),
        ),
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=0), height=184,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        '<div style="text-align:center;font-size:0.72rem;color:#475569;margin-top:-6px;">'
        'Score = (Fresh x 100 + Aging x 50) / Total'
        '</div>',
        unsafe_allow_html=True,
    )

with col_r:
    alert_color = "#EF4444" if alert_count > 0 else "#10B981"
    alert_sub = f'<div style="font-size:0.7rem;color:#EF4444;font-weight:600;margin-top:2px;">need immediate action</div>' if alert_count > 0 else '<div style="font-size:0.7rem;color:#10B981;font-weight:600;margin-top:2px;">all clear</div>'
    st.markdown(_CARD.format(
        accent="#EF4444" if alert_count > 0 else "#10B981",
        label="Critical Alerts", value=alert_count,
        value_color=alert_color, sub=alert_sub,
    ), unsafe_allow_html=True)
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    st.markdown(_CARD.format(
        accent="#F59E0B", label="Oldest Table", value=oldest_display,
        value_color="#0F172A", sub='<div style="font-size:0.7rem;color:#475569;margin-top:2px;">longest since update</div>',
    ), unsafe_allow_html=True)

# ======================================================================
# ROW 2: Dataset Migration Overview
# ======================================================================
st.markdown("")
section_header("Dataset Overview — Migration & Health", "purple")

if not ds_freshness.empty:
    ds_cols = st.columns(len(ds_freshness))
    for i, (_, ds_row) in enumerate(ds_freshness.iterrows()):
        ds_name = ds_row["dataset"]
        ds_label = _DATASET_LABELS.get(ds_name, ds_name)
        ds_color = _DATASET_COLORS.get(ds_name, "#94A3B8")
        ds_tables = int(ds_row["table_count"]) if pd.notna(ds_row["table_count"]) else 0

        # Earliest creation = when dataset was first migrated
        if pd.notna(ds_row.get("earliest_created")):
            created_ts = ds_row["earliest_created"]
            if hasattr(created_ts, 'replace'):
                created_ts = created_ts.replace(tzinfo=UTC)
            days_since_migration = (now - created_ts).total_seconds() / 86400
            migration_date = created_ts.strftime("%b %d, %Y")
        else:
            days_since_migration = None
            migration_date = "Unknown"

        # Newest modification = most recently updated table
        if pd.notna(ds_row.get("newest_modified")):
            newest_ts = ds_row["newest_modified"]
            if hasattr(newest_ts, 'replace'):
                newest_ts = newest_ts.replace(tzinfo=UTC)
            newest_hours = (now - newest_ts).total_seconds() / 3600
            newest_display = f"{newest_hours:.0f}h ago" if newest_hours < 24 else f"{newest_hours / 24:.1f}d ago"
            ds_status_color = "#10B981" if newest_hours < FRESH_HOURS else ("#F59E0B" if newest_hours < AGING_HOURS else "#EF4444")
        else:
            newest_display = "Unknown"
            ds_status_color = "#94A3B8"

        # Tables queried from this dataset
        ds_queried = len(df[df["display_dataset"] == ds_name])
        ds_stale = len(df[(df["display_dataset"] == ds_name) & (df["status"] == "Stale")])

        with ds_cols[i]:
            st.markdown(
                f'<div style="background:white;border:1px solid #E2E8F0;border-top:4px solid {ds_color};'
                f'border-radius:0 0 12px 12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
                f'<div style="font-weight:700;color:#0F172A;font-size:0.95rem;margin-bottom:8px;">{ds_label}</div>'
                f'<div style="font-size:0.78rem;color:#475569;line-height:1.8;">'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<span>Dataset</span><code style="font-size:0.75rem;background:#F1F5F9;padding:1px 4px;border-radius:3px;">{ds_name}</code></div>'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<span>Total tables</span><strong>{ds_tables}</strong></div>'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<span>Queried by users</span><strong>{ds_queried}</strong></div>'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<span>Migrated</span><strong>{migration_date}</strong></div>'
                + (f'<div style="display:flex;justify-content:space-between;">'
                   f'<span>Duration in BQ</span><strong>{days_since_migration:.0f} days</strong></div>'
                   if days_since_migration is not None else '')
                + f'<div style="display:flex;justify-content:space-between;">'
                f'<span>Last update</span><strong style="color:{ds_status_color};">{newest_display}</strong></div>'
                + (f'<div style="display:flex;justify-content:space-between;margin-top:4px;">'
                   f'<span style="color:#EF4444;font-weight:600;">Stale tables</span>'
                   f'<strong style="color:#EF4444;">{ds_stale}</strong></div>'
                   if ds_stale > 0 else
                   f'<div style="display:flex;justify-content:space-between;margin-top:4px;">'
                   f'<span style="color:#10B981;font-weight:600;">All fresh</span>'
                   f'<strong style="color:#10B981;">&#10003;</strong></div>')
                + f'</div></div>',
                unsafe_allow_html=True,
            )

# ======================================================================
# ROW 3: Tables Needing Attention — grouped by dataset
# ======================================================================
attention_tables = df[df["status"].isin(["Stale", "Aging"])].copy()

if not attention_tables.empty:
    st.markdown("")
    section_header(
        f"Tables Needing Attention — {len(attention_tables)} across "
        f"{attention_tables['display_dataset'].nunique()} datasets",
        "red",
    )

    attention_tables["priority_order"] = attention_tables["priority"].map(_PRIORITY_ORDER).fillna(3)
    attention_tables = attention_tables.sort_values(
        ["status", "priority_order", "hours_ago"],
        ascending=[True, True, False],
    )

    # Group by dataset
    for ds_name, ds_group in attention_tables.groupby("display_dataset", sort=False):
        ds_label = _DATASET_LABELS.get(ds_name, ds_name)
        ds_color = _DATASET_COLORS.get(ds_name, "#94A3B8")
        ds_stale = (ds_group["status"] == "Stale").sum()
        ds_aging = (ds_group["status"] == "Aging").sum()

        st.markdown(
            f'<div style="font-weight:700;color:#0F172A;font-size:0.88rem;margin:10px 0 4px;'
            f'padding:4px 10px;border-left:3px solid {ds_color};display:flex;align-items:center;gap:8px;">'
            f'{ds_label} <code style="font-size:0.72rem;background:#F1F5F9;padding:1px 4px;border-radius:3px;">{ds_name}</code>'
            f'<span style="font-size:0.78rem;font-weight:400;color:#475569;">'
            + (f'{ds_stale} stale, ' if ds_stale > 0 else '')
            + f'{ds_aging} aging</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Re-sort within group: stale first, then by priority
        ds_sorted = ds_group.sort_values(
            ["status", "priority_order", "hours_ago"],
            ascending=[True, True, False],  # Stale before Aging
        )

        for _, row in ds_sorted.iterrows():
            tname = row["table_name"]
            hours = row["hours_ago"]
            status = row["status"]
            priority = row["priority"]
            desc = row["desc"]
            domain = row["domain"]
            cfg = _STATUS_CFG[status]
            last_mod = row["last_modified"].strftime("%b %d %H:%M UTC") if pd.notna(row["last_modified"]) else "Unknown"
            days_display = f"{hours / 24:.1f}d" if pd.notna(hours) else "?"
            extra_class = ' stale-alert' if status == "Stale" and priority in ("critical", "high") else ''

            st.markdown(
                f'<div class="freshness-card{extra_class}" style="background:{cfg["bg"]};border:1px solid #E2E8F0;'
                f'border-left:4px solid {cfg["color"]};'
                f'border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:4px;'
                f'box-shadow:0 1px 2px rgba(0,0,0,0.03);">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div style="display:flex;align-items:center;gap:6px;">'
                f'{cfg["icon"]}'
                f'<span style="font-weight:700;color:#0F172A;font-size:0.86rem;">{tname}</span>'
                f'<span style="color:#475569;font-size:0.75rem;">{domain}</span>'
                f'{_PRIORITY_BADGE.get(priority, "")}'
                f'</div>'
                f'<div style="text-align:right;">'
                f'<span style="font-weight:700;color:{cfg["color"]};font-size:0.92rem;">{days_display}</span>'
                f'<span style="color:#475569;font-size:0.7rem;display:block;">{cfg["label"]}</span>'
                f'</div>'
                f'</div>'
                f'<div style="color:#475569;font-size:0.76rem;margin-top:4px;">'
                f'{desc} — Updated: {last_mod}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

else:
    st.markdown("")
    st.markdown(
        '<div style="background:#D1FAE5;border:1px solid #6EE7B7;border-radius:12px;'
        'padding:16px;text-align:center;color:#065F46;font-weight:600;">'
        'All user-queried tables are fresh (updated within 24 hours)</div>',
        unsafe_allow_html=True,
    )

# ======================================================================
# ROW 4: Domain Summary — full width with dataset info
# ======================================================================
st.markdown("")
section_header("Domain Summary", "purple")

domain_summary = df.groupby("domain").agg(
    tables=("table_name", "count"),
    avg_hours=("hours_ago", "mean"),
    stale=("status", lambda x: (x == "Stale").sum()),
    fresh=("status", lambda x: (x == "Fresh").sum()),
    aging=("status", lambda x: (x == "Aging").sum()),
    datasets=("display_dataset", lambda x: ", ".join(sorted(x.unique()))),
    table_list=("table_name", lambda x: ", ".join(sorted(x))),
).reset_index().sort_values(["stale", "aging", "avg_hours"], ascending=[False, False, False])

# Header row
st.markdown(
    '<div style="display:flex;align-items:center;gap:8px;padding:6px 12px;font-size:0.72rem;'
    'font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.05em;border-bottom:2px solid #CBD5E1;">'
    '<span style="width:130px;">Domain</span>'
    '<span style="width:70px;text-align:center;">Tables</span>'
    '<span style="flex:1;">Health Bar</span>'
    '<span style="width:90px;text-align:center;">Fresh / Total</span>'
    '<span style="width:70px;text-align:center;">Avg Age</span>'
    '<span style="width:130px;">Dataset</span>'
    '<span style="width:50px;text-align:center;">Status</span>'
    '</div>',
    unsafe_allow_html=True,
)

_DOMAIN_COLORS_MAP = {
    "Teachers": "#3B82F6", "Lesson Plans": "#10B981", "Events": "#6366F1",
    "Observations": "#F97316", "Training": "#8B5CF6", "LP (RWP)": "#14B8A6",
    "Coaching (RWP)": "#EC4899", "Students (RWP)": "#F59E0B",
    "Users (RWP)": "#60A5FA", "Other": "#94A3B8",
}

for _, drow in domain_summary.iterrows():
    domain = drow["domain"]
    dom_color = _DOMAIN_COLORS_MAP.get(domain, "#94A3B8")

    if drow["stale"] > 0:
        grade_label, grade_bg, grade_text = "ALERT", "#FEE2E2", "#991B1B"
    elif drow["aging"] > 0:
        grade_label, grade_bg, grade_text = "WARN", "#FEF3C7", "#92400E"
    else:
        grade_label, grade_bg, grade_text = "OK", "#D1FAE5", "#065F46"

    f_w = drow["fresh"] / drow["tables"] * 100 if drow["tables"] > 0 else 0
    a_w = drow["aging"] / drow["tables"] * 100 if drow["tables"] > 0 else 0
    s_w = drow["stale"] / drow["tables"] * 100 if drow["tables"] > 0 else 0
    avg_d = drow["avg_hours"] / 24

    # Dataset badges
    ds_list = drow["datasets"].split(", ")
    ds_badges = " ".join(
        f'<span style="font-size:0.68rem;background:#F1F5F9;color:#475569;border-radius:3px;'
        f'padding:1px 4px;border-left:2px solid {_DATASET_COLORS.get(ds, "#94A3B8")};">{ds}</span>'
        for ds in ds_list
    )

    st.markdown(
        f'<div class="domain-row" style="display:flex;align-items:center;gap:8px;padding:8px 12px;'
        f'margin-bottom:3px;border-radius:8px;background:white;border:1px solid #F1F5F9;'
        f'border-left:3px solid {dom_color};">'
        # Domain name
        f'<span style="font-weight:600;color:#0F172A;width:130px;font-size:0.84rem;">{domain}</span>'
        # Table count
        f'<span style="width:70px;text-align:center;font-weight:700;color:#0F172A;font-size:0.85rem;">{drow["tables"]}</span>'
        # Health bar
        f'<div style="flex:1;display:flex;border-radius:4px;overflow:hidden;height:12px;"'
        f' title="Fresh: {drow["fresh"]} | Aging: {drow["aging"]} | Stale: {drow["stale"]}">'
        f'<div style="width:{f_w}%;background:#10B981;"></div>'
        f'<div style="width:{a_w}%;background:#F59E0B;"></div>'
        f'<div style="width:{s_w}%;background:#EF4444;"></div>'
        f'</div>'
        # Fresh count
        f'<span style="color:#475569;font-size:0.8rem;width:90px;text-align:center;">'
        f'<strong>{drow["fresh"]}</strong> / {drow["tables"]}</span>'
        # Avg age
        f'<span style="color:#475569;font-size:0.8rem;width:70px;text-align:center;">{avg_d:.1f}d</span>'
        # Dataset badges
        f'<span style="width:130px;display:flex;flex-wrap:wrap;gap:2px;">{ds_badges}</span>'
        # Grade badge
        f'<span style="background:{grade_bg};color:{grade_text};border-radius:4px;'
        f'padding:2px 8px;font-size:0.72rem;font-weight:700;width:50px;text-align:center;">'
        f'{grade_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# Legend for health bar
st.markdown(
    '<div style="display:flex;justify-content:center;gap:16px;margin-top:6px;font-size:0.75rem;color:#475569;">'
    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#10B981;vertical-align:middle;"></span> Fresh (&lt;24h)</span>'
    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#F59E0B;vertical-align:middle;"></span> Aging (1-3d)</span>'
    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#EF4444;vertical-align:middle;"></span> Stale (&gt;3d)</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ======================================================================
# ROW 5: All Tables — tabbed by status
# ======================================================================
st.markdown("")
section_header("All User-Queried Tables", "")
st.caption(
    f"These are the {total_tables} tables that users have actually queried in the last 30 days "
    f"(tracked from the audit log). Tables not queried are not shown."
)

tab_all, tab_stale, tab_aging, tab_fresh = st.tabs([
    f"All ({total_tables})",
    f"Stale ({stale_count})",
    f"Aging ({aging_count})",
    f"Fresh ({fresh_count})",
])


def _render_table_rows(subset: pd.DataFrame) -> None:
    """Render a compact table for a subset of tables."""
    if subset.empty:
        st.info("No tables in this category.")
        return

    display = subset.copy()
    display["priority_order"] = display["priority"].map(_PRIORITY_ORDER).fillna(3)
    display = display.sort_values(["priority_order", "hours_ago"], ascending=[True, False])

    rows_html = ""
    for _, row in display.iterrows():
        cfg = _STATUS_CFG[row["status"]]
        ds_color = _DATASET_COLORS.get(row["display_dataset"], "#94A3B8")
        ds_label = _DATASET_LABELS.get(row["display_dataset"], row["display_dataset"])
        last_mod = row["last_modified"].strftime("%b %d %H:%M") if pd.notna(row["last_modified"]) else "—"
        age = f'{row["hours_ago"] / 24:.1f}d' if pd.notna(row["hours_ago"]) and row["hours_ago"] >= 24 else (
            f'{row["hours_ago"]:.0f}h' if pd.notna(row["hours_ago"]) else "—"
        )

        rows_html += (
            f'<tr style="border-bottom:1px solid #F1F5F9;">'
            f'<td style="padding:6px 8px;font-weight:600;color:#0F172A;font-size:0.84rem;">'
            f'{cfg["icon"]} {row["table_name"]}</td>'
            f'<td style="padding:6px 8px;font-size:0.78rem;">'
            f'<span style="border-left:3px solid {ds_color};padding-left:6px;">{ds_label}</span></td>'
            f'<td style="padding:6px 8px;font-size:0.78rem;color:#475569;">{row["domain"]}</td>'
            f'<td style="padding:6px 8px;">{_PRIORITY_BADGE.get(row["priority"], "")}</td>'
            f'<td style="padding:6px 8px;font-weight:700;color:{cfg["color"]};font-size:0.84rem;">{age}</td>'
            f'<td style="padding:6px 8px;font-size:0.78rem;color:#475569;">{last_mod}</td>'
            f'<td style="padding:6px 8px;"><span style="background:{cfg["bg"]};color:{cfg["color"]};'
            f'border-radius:4px;padding:1px 6px;font-size:0.7rem;font-weight:700;">'
            f'{row["status"]}</span></td>'
            f'</tr>'
        )

    th_style = 'style="text-align:left;font-size:0.72rem;font-weight:700;color:#475569;padding:6px 8px;border-bottom:2px solid #CBD5E1;text-transform:uppercase;letter-spacing:0.05em;"'
    st.markdown(
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;background:white;border:1px solid #E2E8F0;border-radius:10px;overflow:hidden;">'
        f'<thead style="background:#F8FAFC;"><tr>'
        f'<th {th_style}>Table</th>'
        f'<th {th_style}>Dataset</th>'
        f'<th {th_style}>Domain</th>'
        f'<th {th_style}>Priority</th>'
        f'<th {th_style}>Age</th>'
        f'<th {th_style}>Last Updated</th>'
        f'<th {th_style}>Status</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )


with tab_all:
    _render_table_rows(df)

with tab_stale:
    _render_table_rows(df[df["status"] == "Stale"])

with tab_aging:
    _render_table_rows(df[df["status"] == "Aging"])

with tab_fresh:
    _render_table_rows(df[df["status"] == "Fresh"])

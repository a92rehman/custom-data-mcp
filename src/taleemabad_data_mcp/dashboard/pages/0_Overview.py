"""Executive overview — ring charts, KPI cards with badges, domain bars.

All layout rows use pure HTML CSS Grid for perfect symmetry.
Navigation uses hidden Streamlit buttons at the page bottom.
"""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from taleemabad_data_mcp.dashboard.components.auto_refresh import (
    clear_cache_if_needed,
    inject_auto_refresh,
)
from taleemabad_data_mcp.dashboard.components.filters import get_refresh_seconds, render_filters
from taleemabad_data_mcp.dashboard.components.styles import (
    CHART_H,
    COLORS,
    DOMAIN_COLORS,
    GRADIENTS,
    inject_page_css,
    page_header,
    section_header,
)
from taleemabad_data_mcp.dashboard.data.queries import (
    get_activity_log,
    get_feedback,
    get_table_freshness,
)
from taleemabad_data_mcp.dashboard.data.projects import (
    load_projects,
    get_dataset_stats,
    get_governance_coverage,
)

inject_page_css()

st.markdown("""
<style>
    /* ── KPI Row ── */
    .kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px; }
    .kc {
        background: white; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 18px 20px; position: relative; overflow: visible;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.25s;
        min-height: 130px;
    }
    .kc:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.08); transform: translateY(-2px); border-color: #93C5FD; }
    .kc::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:14px 14px 0 0; }
    .kc.c-blue::after { background: linear-gradient(90deg, #3B82F6, transparent); }
    .kc.c-purple::after { background: linear-gradient(90deg, #8B5CF6, transparent); }
    .kc.c-pink::after { background: linear-gradient(90deg, #EC4899, transparent); }
    .kc.c-green::after { background: linear-gradient(90deg, #10B981, transparent); }
    .kc.c-red::after { background: linear-gradient(90deg, #EF4444, transparent); }
    .kc .kc-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
    .kc .kc-label { font-size:0.68rem; font-weight:600; color:#64748B; text-transform:uppercase; letter-spacing:1.2px; }
    .kc .kc-badge { font-size:0.65rem; font-weight:700; padding:3px 10px; border-radius:100px; }
    .kc .kc-badge.up { background:#D1FAE5; color:#065F46; }
    .kc .kc-badge.down { background:#FEE2E2; color:#991B1B; }
    .kc .kc-corner { font-size:0.7rem; font-weight:600; color:#475569; background:#F1F5F9; padding:3px 8px; border-radius:6px; }
    .kc .kc-val { font-size:1.9rem; font-weight:800; color:#0F172A; letter-spacing:-1px; }
    .kc .kc-sub { font-size:0.75rem; color:#94A3B8; margin-top:3px; }
    .kc .kc-bar { width:100%; height:5px; background:#F1F5F9; border-radius:100px; overflow:hidden; margin-top:10px; }
    .kc .kc-bar-fill { height:100%; border-radius:100px; }

    /* ── Score Row ── */
    .score-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }
    .sc {
        background: white; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 24px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.25s;
    }
    .sc:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.08); transform: translateY(-2px); border-color: #93C5FD; }
    .sc h3 { font-size:0.72rem; font-weight:600; color:#64748B; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:18px; }
    .ring-wrap { position:relative; width:140px; height:140px; margin:0 auto 16px; }
    .ring-wrap svg { width:100%; height:100%; }
    .ring-center { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:1.6rem; font-weight:800; color:#0F172A; letter-spacing:-1px; }
    .status-pill { display:inline-flex; align-items:center; gap:6px; padding:5px 14px; border-radius:100px; font-size:0.75rem; font-weight:600; }
    .status-pill.good { background:#D1FAE5; color:#065F46; }
    .status-pill.warn { background:#FEF3C7; color:#92400E; }
    .status-pill.bad { background:#FEE2E2; color:#991B1B; }

    /* ── Charts ── */
    .chart-box {
        background: white; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .chart-box h3 { font-size:0.9rem; font-weight:700; color:#0F172A; margin-bottom:16px; }
    .dom-row { display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid #F8FAFC; }
    .dom-row:last-child { border-bottom:none; }
    .dom-icon { width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; color:white; flex-shrink:0; }
    .dom-info { flex:1; }
    .dom-name { font-size:0.82rem; font-weight:600; color:#0F172A; margin-bottom:5px; }
    .dom-bar-bg { width:100%; height:5px; background:#F1F5F9; border-radius:100px; overflow:hidden; }
    .dom-bar-fill { height:100%; border-radius:100px; }
    .dom-pct { font-size:0.82rem; font-weight:700; min-width:50px; text-align:right; }

    /* ── Bottom Row ── */
    .bottom-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
    .bot-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.25s; min-height: 220px;
    }
    .bot-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.08); transform: translateY(-2px); border-color: #93C5FD; }
    .bot-card h3 { font-size:0.88rem; font-weight:700; color:#0F172A; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid #F1F5F9; }
    .err-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #F8FAFC; font-size:0.82rem; }
    .err-row:last-child { border-bottom:none; }
    .err-left { display:flex; align-items:center; gap:8px; color:#475569; }
    .err-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
    .cost-big { font-size:2.2rem; font-weight:800; letter-spacing:-1.5px; margin-bottom:2px; }
    .cost-label { font-size:0.78rem; color:#64748B; margin-bottom:14px; }
    .cost-row { display:flex; justify-content:space-between; font-size:0.82rem; padding:5px 0; }
    .act-item {
        display:flex; gap:10px; align-items:flex-start;
        padding:10px 12px; border-left:3px solid; border-radius:0 8px 8px 0;
        margin-bottom:6px; font-size:0.8rem; color:#475569; line-height:1.4;
    }
    .act-badge { font-size:0.6rem; font-weight:700; padding:2px 6px; border-radius:4px; white-space:nowrap; text-transform:uppercase; letter-spacing:0.5px; }

</style>
""", unsafe_allow_html=True)

page_header("Taleemabad MCP Observatory", "Governed data layer — adoption, quality, cost at a glance")
filters = render_filters()
inject_auto_refresh(get_refresh_seconds())
clear_cache_if_needed(get_refresh_seconds())
df = get_activity_log(**filters)
fb = get_feedback(days=filters["days"])

if df.empty:
    st.info("No activity data found. Use the MCP tools in Claude Code to generate data.")
    st.stop()

# ── Metrics ──
real = df[df["error_type"] != "dry_run"]
errs = real[real["error_type"].notna()]
cost_df = df[df["cost_usd"].notna() & (df["cost_usd"] > 0)]
total_q = len(real)
n_users = df["user_name"].nunique()
total_cost = cost_df["cost_usd"].sum() if not cost_df.empty else 0
err_count = len(errs)
err_rate = err_count / total_q * 100 if total_q > 0 else 0
success_rate = len(real[real["error_type"].isna()]) / total_q * 100 if total_q > 0 else 0
up = int((fb["rating"] == "up").sum()) if not fb.empty else 0
down = int((fb["rating"] == "down").sum()) if not fb.empty else 0
fb_total = len(fb) if not fb.empty else 0
sat = up / fb_total * 100 if fb_total > 0 else 0
confidence = success_rate * 0.7 + sat * 0.3 if fb_total > 0 else success_rate

_projects = load_projects()
_active = [p for p in _projects if p.get("status") == "active"]
_gov_map = get_governance_coverage()
_gov_per_ds: dict[str, int] = {}
for (_ds, _), _ in _gov_map.items():
    _gov_per_ds[_ds] = _gov_per_ds.get(_ds, 0) + 1
governed = sum(_gov_per_ds.values())
_ds_to_q = [p["dataset"] for p in _projects if p.get("dataset") and p.get("status") in ("active", "system")]
_ds_stats = get_dataset_stats(_ds_to_q) if _ds_to_q else {}
total_tables_all = sum(s["table_count"] for s in _ds_stats.values())

try:
    fresh_df = get_table_freshness()
    if not fresh_df.empty:
        from datetime import UTC, datetime
        _now = datetime.now(UTC)
        fresh_df["h"] = fresh_df["last_modified"].apply(
            lambda ts: (_now - ts.replace(tzinfo=UTC)).total_seconds() / 3600 if pd.notna(ts) else None)
        n_fresh = int((fresh_df["h"] < 24).sum())
        n_stale = int((fresh_df["h"] >= 72).sum())
        n_tables = len(fresh_df)
    else:
        n_fresh, n_stale, n_tables = 0, 0, 0
except Exception:
    n_fresh, n_stale, n_tables = 0, 0, 0
    fresh_df = pd.DataFrame()
health_pct = round((n_fresh * 100 + (n_tables - n_fresh - n_stale) * 50) / n_tables) if n_tables > 0 else 0
gov_pct = round(governed / total_tables_all * 100, 1) if total_tables_all > 0 else 0
proj_governed = sum(1 for p in _active if _gov_per_ds.get(p.get("dataset", ""), 0) > 0)
proj_pct = round(proj_governed / len(_active) * 100, 1) if _active else 0

# ======================================================================
# ROW 1 — 5 KPI cards
# ======================================================================
err_badge = (
    f'<span class="kc-badge down">+{err_rate:.1f}%</span>' if err_rate > 5
    else f'<span class="kc-badge up">{err_rate:.1f}%</span>'
)

st.markdown(
    f'<div class="kpi-row">'

    f'<div class="kc c-blue">'
    f'<div class="kc-head"><span class="kc-label">Active Users</span></div>'
    f'<div class="kc-val">{n_users}</div>'
    f'<div class="kc-sub">across {len(_active)} projects</div></div>'

    f'<div class="kc c-purple">'
    f'<div class="kc-head"><span class="kc-label">Total Queries</span></div>'
    f'<div class="kc-val">{total_q:,}</div>'
    f'<div class="kc-sub">{total_q / max(n_users,1):.1f} avg per user</div></div>'

    f'<div class="kc c-pink">'
    f'<div class="kc-head"><span class="kc-label">Governed Projects</span>'
    f'<span class="kc-corner">{proj_governed} / {len(_active)}</span></div>'
    f'<div class="kc-val">{proj_pct}%</div>'
    f'<div class="kc-bar"><div class="kc-bar-fill" style="width:{proj_pct}%;background:#EC4899;"></div></div>'
    f'<div class="kc-sub">{proj_governed} governed of {len(_active)} total</div></div>'

    f'<div class="kc c-green">'
    f'<div class="kc-head"><span class="kc-label">Governed Tables</span>'
    f'<span class="kc-corner">{governed} / {total_tables_all}</span></div>'
    f'<div class="kc-val">{gov_pct}%</div>'
    f'<div class="kc-bar"><div class="kc-bar-fill" style="width:{gov_pct}%;background:#10B981;"></div></div>'
    f'<div class="kc-sub">{governed} governed of {total_tables_all} total</div></div>'

    f'<div class="kc c-red">'
    f'<div class="kc-head"><span class="kc-label">Error Rate</span>{err_badge}</div>'
    f'<div class="kc-val">{err_rate:.1f}%</div>'
    f'<div class="kc-sub">{err_count} errors / {total_q} queries</div></div>'

    f'</div>',
    unsafe_allow_html=True,
)

# ======================================================================
# ROW 2 — 3 SVG ring charts (pure HTML grid)
# ======================================================================
def _ring(pct: float, c1: str, c2: str, rid: str) -> str:
    r, circ = 50, 2 * math.pi * 50
    off = circ * (1 - pct / 100)
    return (
        f'<svg viewBox="0 0 120 120">'
        f'<circle cx="60" cy="60" r="{r}" fill="none" stroke="#F1F5F9" stroke-width="10"/>'
        f'<circle cx="60" cy="60" r="{r}" fill="none" stroke="url(#{rid})" stroke-width="10" '
        f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}" stroke-linecap="round" '
        f'transform="rotate(-90 60 60)"/>'
        f'<defs><linearGradient id="{rid}" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>'
        f'</linearGradient></defs></svg>'
    )

def _pill(pct: float, hi: float = 70, lo: float = 50) -> tuple[str, str]:
    if pct >= hi: return "Good", "good"
    if pct >= lo: return "Needs Attention", "warn"
    return "Critical", "bad"

cl1, cc1 = _pill(confidence)
cl2, cc2 = _pill(health_pct, 70, 40)
cl3, cc3 = _pill(sat, 70, 50) if fb_total > 0 else ("No Data", "warn")

st.markdown(
    f'<div class="score-row">'

    f'<div class="sc">'
    f'<h3>SYSTEM CONFIDENCE</h3>'
    f'<div class="ring-wrap">{_ring(confidence, "#6366F1", "#10B981", "g1")}'
    f'<div class="ring-center">{confidence:.1f}%</div></div>'
    f'<span class="status-pill {cc1}">&#9679; {cl1}</span></div>'

    f'<div class="sc">'
    f'<h3>PIPELINE HEALTH</h3>'
    f'<div class="ring-wrap">{_ring(health_pct, "#14B8A6", "#F59E0B", "g2")}'
    f'<div class="ring-center">{health_pct}%</div></div>'
    f'<span class="status-pill {cc2}">&#9679; {cl2}</span></div>'

    f'<div class="sc">'
    f'<h3>USER SATISFACTION</h3>'
    f'<div class="ring-wrap">{_ring(sat if fb_total else 0, "#F97316", "#EC4899", "g3")}'
    f'<div class="ring-center">{sat:.1f}%</div></div>'
    f'<span class="status-pill {cc3}">&#9679; {cl3}</span></div>'

    f'</div>',
    unsafe_allow_html=True,
)

# ======================================================================
# ROW 3 — Activity Trend (plotly) + Domain bars (HTML) — use st.columns for plotly
# ======================================================================
df["date"] = pd.to_datetime(df["timestamp"]).dt.date
daily = df.groupby("date").agg(queries=("event_id", "count"), users=("user_name", "nunique")).reset_index()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=daily["date"], y=daily["queries"], name="Queries", mode="lines+markers",
    line=dict(color=COLORS["primary"], width=2, shape="spline"), marker=dict(size=4),
    fill="tozeroy", fillcolor="rgba(59,130,246,0.05)",
))
fig.add_trace(go.Bar(
    x=daily["date"], y=daily["users"], name="Users", yaxis="y2",
    marker_color=COLORS["purple"], opacity=0.3, marker_cornerradius=3,
))
fig.update_layout(
    template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), height=240,
    legend=dict(orientation="h", yanchor="top", y=1.1, x=0, font_size=11),
    yaxis=dict(title=None, gridcolor="#F1F5F9"),
    yaxis2=dict(title=None, overlaying="y", side="right", showgrid=False),
    xaxis=dict(title=None), hovermode="x unified",
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", size=11),
)

dom = df.groupby("domain").size().reset_index(name="n").sort_values("n", ascending=False)
dom["pct"] = (dom["n"] / dom["n"].sum() * 100).round(1)
_DOM_ICONS = {
    "observations": ("#F97316", "Ob"), "teachers": ("#3B82F6", "Te"),
    "lesson_plans": ("#10B981", "LP"), "training": ("#8B5CF6", "Tr"),
    "coaching": ("#EC4899", "Co"), "students": ("#14B8A6", "St"),
    "events": ("#6366F1", "Ev"), "platform": ("#F59E0B", "Pl"), "other": ("#94A3B8", "Ot"),
}
domain_html = ""
for _, r in dom.iterrows():
    d = r["domain"]
    color, abbr = _DOM_ICONS.get(d, ("#94A3B8", d[:2].title()))
    domain_html += (
        f'<div class="dom-row">'
        f'<div class="dom-icon" style="background:{color};">{abbr}</div>'
        f'<div class="dom-info"><div class="dom-name">{d.replace("_"," ").title()}</div>'
        f'<div class="dom-bar-bg"><div class="dom-bar-fill" style="width:{max(4,r["pct"])}%;background:{color};"></div></div></div>'
        f'<div class="dom-pct" style="color:{color};">{r["pct"]}%</div></div>'
    )

# Use 2 st.columns with matching proportions
ch_l, ch_r = st.columns([1.6, 1], gap="medium")
with ch_l:
    section_header("Activity Trend")
    st.plotly_chart(fig, use_container_width=True)
with ch_r:
    st.markdown(
        f'<div style="background:white;border:1px solid #E2E8F0;border-radius:14px;padding:22px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-top:0;">'
        f'<h3 style="font-size:0.9rem;font-weight:700;color:#0F172A;margin:0 0 12px;">Queries by Domain</h3>'
        f'{domain_html}</div>',
        unsafe_allow_html=True,
    )

# ======================================================================
# ROW 4 — Bottom: Errors | Cost | Actions (pure HTML grid)
# ======================================================================
st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

err_types_df = errs.groupby("error_type").size().reset_index(name="count").sort_values("count", ascending=False) if not errs.empty else pd.DataFrame()
err_colors_list = ["#EF4444", "#F59E0B", "#F97316", "#EC4899", "#94A3B8"]
err_html = ""
for i, (_, r) in enumerate(err_types_df.head(5).iterrows()):
    c = err_colors_list[i % len(err_colors_list)]
    err_html += f'<div class="err-row"><div class="err-left"><div class="err-dot" style="background:{c};"></div>{r["error_type"]}</div><span style="font-weight:600;color:#0F172A;">{r["count"]}</span></div>'
if not err_html:
    err_html = '<div style="color:#10B981;font-size:0.84rem;padding:8px 0;">No errors this period</div>'

avg_cost = total_cost / total_q if total_q > 0 else 0
avg_cost_user = total_cost / n_users if n_users > 0 else 0
total_bytes = cost_df["cost_bytes"].sum() if not cost_df.empty else 0
cost_color = "#10B981" if total_cost < 1 else ("#F59E0B" if total_cost < 10 else "#EF4444")

acts = []
if err_count > 0:
    top_e = errs["error_type"].value_counts().index[0]
    acts.append(("high", "#EF4444", "#FEE2E2", "#991B1B", f"Pipeline: {err_count} failed — top: {top_e}"))
if n_stale > 0:
    ns = fresh_df[fresh_df["h"] >= 72]["table_name"].tolist()[:2]
    acts.append(("med", "#F59E0B", "#FEF3C7", "#92400E", f"{n_stale} stale tables: {', '.join(ns)}"))
bad = [u for u in df["user_name"].unique() if "${" in str(u) or u == "unknown"]
if bad:
    acts.append(("med", "#F59E0B", "#FEF3C7", "#92400E", f"{len(bad)} misconfigured user(s)"))
if fb_total == 0 and total_q > 10:
    acts.append(("low", "#3B82F6", "#DBEAFE", "#1E40AF", "No feedback yet — encourage ratings"))
if n_users < 3 and total_q > 0:
    acts.append(("low", "#8B5CF6", "#EDE9FE", "#5B21B6", f"Low adoption — only {n_users} users"))
for p in _active:
    ds = p.get("dataset")
    if ds and _gov_per_ds.get(ds, 0) == 0:
        acts.append(("med", "#F59E0B", "#FEF3C7", "#92400E", f"No rules: {p.get('name', ds)}"))

actions_html = ""
for prio, color, bg, tc, text in acts:
    actions_html += (
        f'<div class="act-item" style="border-left-color:{color};background:{bg};">'
        f'<span class="act-badge" style="background:{bg};color:{tc};">{prio}</span>{text}</div>'
    )
if not actions_html:
    actions_html = '<div style="color:#10B981;font-size:0.84rem;">All clear — no actions needed</div>'

st.markdown(
    f'<div class="bottom-row">'

    f'<div class="bot-card">'
    f'<h3>Error Breakdown</h3>{err_html}'
    f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #F1F5F9;display:flex;justify-content:space-between;font-size:0.8rem;">'
    f'<span style="color:#64748B;">Total errors</span><span style="font-weight:700;">{err_count} / {total_q}</span></div></div>'

    f'<div class="bot-card">'
    f'<h3>Cost Tracker</h3>'
    f'<div class="cost-big" style="color:{cost_color};">${total_cost:.2f}</div>'
    f'<div class="cost-label">Total spend this period</div>'
    f'<div class="cost-row"><span style="color:#64748B;">Avg per query</span><span style="font-weight:600;">${avg_cost:.5f}</span></div>'
    f'<div class="cost-row"><span style="color:#64748B;">Avg per user</span><span style="font-weight:600;">${avg_cost_user:.4f}</span></div>'
    f'<div class="cost-row"><span style="color:#64748B;">Data scanned</span><span style="font-weight:600;">{total_bytes / (1024**3):.2f} GB</span></div></div>'

    f'<div class="bot-card"><h3>Actions Needed</h3>{actions_html}</div>'

    f'</div>',
    unsafe_allow_html=True,
)

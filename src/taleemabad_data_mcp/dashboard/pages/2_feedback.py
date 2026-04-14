"""Feedback — expectation vs reality deep dive."""

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
from taleemabad_data_mcp.dashboard.components.charts import DOMAIN_COLORS
from taleemabad_data_mcp.dashboard.components.filters import get_refresh_seconds, render_filters
from taleemabad_data_mcp.dashboard.components.styles import (
    CHART_H,
    CHART_H_SM,
    COLORS,
    inject_page_css,
    page_header,
    section_header,
)
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log, get_feedback

inject_page_css()

page_header("Expectation vs Reality", "Are MCP answers meeting user expectations? Feedback is voluntary.")

filters = render_filters()
inject_auto_refresh(get_refresh_seconds())
clear_cache_if_needed(get_refresh_seconds())
fb = get_feedback(days=filters["days"])
activity = get_activity_log(**filters)

if fb.empty:
    st.info(
        "No feedback data yet. Feedback is collected when users "
        "voluntarily give a thumbs up or down after receiving an answer."
    )
    st.stop()

# -- Derived --
up_count = int((fb["rating"] == "up").sum())
down_count = int((fb["rating"] == "down").sum())
total_fb = len(fb)
total_queries = len(activity) if not activity.empty else 0
sat_pct = up_count / total_fb * 100 if total_fb > 0 else 0
adoption = total_fb / total_queries * 100 if total_queries > 0 else 0

# -- KPI row --
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Satisfaction", f"{sat_pct:.0f}%")
c2.metric("Thumbs Up", up_count)
c3.metric("Thumbs Down", down_count)
c4.metric("Total Feedback", total_fb)
c5.metric("Feedback Adoption", f"{adoption:.0f}%")

st.markdown("")

# -- Row 1: Feedback trend + Satisfaction gauge --
col1, col2 = st.columns([3, 2])

with col1:
    section_header("Feedback Over Time", "green")
    fb["date"] = pd.to_datetime(fb["timestamp"]).dt.date
    fb_daily = fb.groupby(["date", "rating"]).size().reset_index(name="Count")
    fig = go.Figure()
    for rating, color in [("up", "#10B981"), ("down", "#EF4444")]:
        subset = fb_daily[fb_daily["rating"] == rating]
        if not subset.empty:
            fig.add_trace(go.Bar(
                x=subset["date"], y=subset["Count"],
                name=f"Thumbs {rating.title()}", marker_color=color,
                marker_cornerradius=3,
            ))
    fig.update_layout(
        template="plotly_white", barmode="group",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
        legend=dict(orientation="h", yanchor="top", y=1.1, x=0),
        xaxis=dict(title=None), yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("Satisfaction Score", "orange")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sat_pct,
        number=dict(suffix="%", font=dict(size=36, color=COLORS["text"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(size=10)),
            bar=dict(color="#3B82F6"),
            steps=[
                dict(range=[0, 50], color="#FEE2E2"),
                dict(range=[50, 75], color="#FEF3C7"),
                dict(range=[75, 100], color="#D1FAE5"),
            ],
            threshold=dict(
                line=dict(color="#EF4444", width=2),
                thickness=0.75, value=70,
            ),
        ),
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=10), height=CHART_H,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Row 2: Satisfaction by domain + by user --
col3, col4 = st.columns(2)

with col3:
    section_header("Satisfaction by Domain", "purple")
    if "domain" in fb.columns:
        domain_fb = fb.groupby("domain").agg(
            up=("rating", lambda x: (x == "up").sum()),
            total=("rating", "count"),
        ).reset_index()
        domain_fb["sat_pct"] = domain_fb["up"] / domain_fb["total"] * 100
        domain_fb = domain_fb.sort_values("sat_pct", ascending=True)
        d_colors = [
            DOMAIN_COLORS.get(d, "#94A3B8") for d in domain_fb["domain"]
        ]
        fig = go.Figure(go.Bar(
            x=domain_fb["sat_pct"], y=domain_fb["domain"],
            orientation="h", marker_color=d_colors,
            marker_cornerradius=3,
            text=[
                f"{v:.0f}% ({t})" for v, t
                in zip(domain_fb["sat_pct"], domain_fb["total"], strict=True)
            ],
            textposition="auto",
        ))
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
            xaxis=dict(title=None, range=[0, 100]),
            yaxis=dict(title=None),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)

with col4:
    section_header("Satisfaction by User")
    user_fb = fb.groupby("user_name").agg(
        up=("rating", lambda x: (x == "up").sum()),
        total=("rating", "count"),
    ).reset_index()
    user_fb["sat_pct"] = user_fb["up"] / user_fb["total"] * 100
    user_fb = user_fb.sort_values("sat_pct", ascending=True)
    fig = go.Figure(go.Bar(
        x=user_fb["sat_pct"], y=user_fb["user_name"],
        orientation="h", marker_color=COLORS["primary"],
        marker_cornerradius=3,
        text=[
            f"{v:.0f}% ({t})" for v, t
            in zip(user_fb["sat_pct"], user_fb["total"], strict=True)
        ],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H_SM,
        xaxis=dict(title=None, range=[0, 100]),
        yaxis=dict(title=None),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Comments --
section_header("User Comments", "teal")
comments = fb[fb["comment"].notna() & (fb["comment"] != "")]
if not comments.empty:
    for _, row in comments.head(20).iterrows():
        accent = "#10B981" if row["rating"] == "up" else "#EF4444"
        icon = (
            '<span style="color:#10B981;">&#9650;</span>'
            if row["rating"] == "up"
            else '<span style="color:#EF4444;">&#9660;</span>'
        )
        ts = pd.to_datetime(row["timestamp"]).strftime("%b %d, %H:%M")
        q = str(row.get("query_text", ""))[:60]
        st.markdown(
            f"<div style='padding:8px 12px;margin-bottom:6px;"
            f"background:#FAFAFA;border:1px solid #E2E8F0;"
            f"border-left:3px solid {accent};"
            f"border-radius:10px;font-size:0.88rem;'>"
            f"{icon} <strong>{row['user_name']}</strong>"
            f" <span style='color:#94A3B8;'>{ts}</span><br/>"
            f"<span style='color:#64748B;'>{q}</span><br/>"
            f"<em>{row['comment']}</em></div>",
            unsafe_allow_html=True,
        )
else:
    st.info("No comments yet — users can optionally leave text feedback.")

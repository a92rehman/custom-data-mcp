"""Feedback — expectation vs reality deep dive."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from taleemabad_data_mcp.dashboard.components.auto_refresh import (
    clear_cache_if_needed,
    inject_auto_refresh,
)
from taleemabad_data_mcp.dashboard.components.charts import DOMAIN_COLORS
from taleemabad_data_mcp.dashboard.components.filters import render_filters
from taleemabad_data_mcp.dashboard.components.styles import (
    CHART_H,
    CHART_H_SM,
    COLORS,
    inject_page_css,
)
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log, get_feedback

inject_page_css()

st.header("Expectation vs Reality")
st.caption(
    "Are MCP answers meeting user expectations? "
    "Feedback is voluntary — users rate only when they choose to."
)

filters = render_filters()
inject_auto_refresh(filters["refresh_seconds"])
clear_cache_if_needed(filters["refresh_seconds"])
st.markdown("---")
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
    st.markdown(
        '<div class="section-header">Feedback Over Time</div>',
        unsafe_allow_html=True,
    )
    fb["date"] = pd.to_datetime(fb["timestamp"]).dt.date
    fb_daily = fb.groupby(["date", "rating"]).size().reset_index(name="Count")
    fig = go.Figure()
    for rating, color in [("up", COLORS["success"]), ("down", COLORS["danger"])]:
        subset = fb_daily[fb_daily["rating"] == rating]
        if not subset.empty:
            fig.add_trace(go.Bar(
                x=subset["date"], y=subset["Count"],
                name=f"Thumbs {rating.title()}", marker_color=color,
            ))
    fig.update_layout(
        template="plotly_white", barmode="group",
        margin=dict(l=10, r=10, t=10, b=10), height=CHART_H,
        legend=dict(orientation="h", yanchor="top", y=1.1, x=0),
        xaxis=dict(title=None), yaxis=dict(title=None),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown(
        '<div class="section-header">Satisfaction Score</div>',
        unsafe_allow_html=True,
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sat_pct,
        number=dict(suffix="%", font=dict(size=36, color=COLORS["text"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(size=10)),
            bar=dict(color=COLORS["primary"]),
            steps=[
                dict(range=[0, 50], color="#FEE2E2"),
                dict(range=[50, 75], color="#FEF3C7"),
                dict(range=[75, 100], color="#DCFCE7"),
            ],
            threshold=dict(
                line=dict(color=COLORS["danger"], width=2),
                thickness=0.75, value=70,
            ),
        ),
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=10), height=CHART_H,
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Row 2: Satisfaction by domain + by user --
col3, col4 = st.columns(2)

with col3:
    st.markdown(
        '<div class="section-header">Satisfaction by Domain</div>',
        unsafe_allow_html=True,
    )
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
        )
        st.plotly_chart(fig, use_container_width=True)

with col4:
    st.markdown(
        '<div class="section-header">Satisfaction by User</div>',
        unsafe_allow_html=True,
    )
    user_fb = fb.groupby("user_name").agg(
        up=("rating", lambda x: (x == "up").sum()),
        total=("rating", "count"),
    ).reset_index()
    user_fb["sat_pct"] = user_fb["up"] / user_fb["total"] * 100
    user_fb = user_fb.sort_values("sat_pct", ascending=True)
    fig = go.Figure(go.Bar(
        x=user_fb["sat_pct"], y=user_fb["user_name"],
        orientation="h", marker_color=COLORS["primary"],
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
    )
    st.plotly_chart(fig, use_container_width=True)

# -- Comments --
st.markdown(
    '<div class="section-header">User Comments</div>',
    unsafe_allow_html=True,
)
comments = fb[fb["comment"].notna() & (fb["comment"] != "")]
if not comments.empty:
    for _, row in comments.head(20).iterrows():
        icon = (
            '<span style="color:#22C55E;">&#9650;</span>'
            if row["rating"] == "up"
            else '<span style="color:#EF4444;">&#9660;</span>'
        )
        ts = pd.to_datetime(row["timestamp"]).strftime("%b %d, %H:%M")
        q = str(row.get("query_text", ""))[:60]
        st.markdown(
            f"<div style='padding:8px 12px;margin-bottom:6px;"
            f"background:white;border:1px solid #E2E8F0;"
            f"border-radius:8px;font-size:0.88rem;'>"
            f"{icon} <strong>{row['user_name']}</strong>"
            f" <span style='color:#94A3B8;'>{ts}</span><br/>"
            f"<span style='color:#64748B;'>{q}</span><br/>"
            f"<em>{row['comment']}</em></div>",
            unsafe_allow_html=True,
        )
else:
    st.info("No comments yet — users can optionally leave text feedback.")

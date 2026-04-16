"""Teacher ACR & Promotion Policy — FICO-mapped KPI scores and student outcomes."""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from taleemabad_data_mcp.dashboard.components.auto_refresh import (
    clear_cache_if_needed,
    inject_auto_refresh,
)
from taleemabad_data_mcp.dashboard.components.filters import get_refresh_seconds
from taleemabad_data_mcp.dashboard.components.styles import (
    CHART_H,
    COLORS,
    inject_page_css,
    page_header,
    section_header,
)
from taleemabad_data_mcp.dashboard.data.client import get_bq_client, get_config

inject_page_css()

page_header(
    "Teacher ACR & Promotion Policy",
    "FICO observation indicators mapped to ACR KPIs — teacher performance analysis",
)
inject_auto_refresh(get_refresh_seconds())
clear_cache_if_needed(get_refresh_seconds())

# ── KPI column definitions ──
KPI_COLS = [
    ("Planning_and_Preparation", "Planning & Prep"),
    ("Subject_Knowledge", "Subject Knowledge"),
    ("Classroom_Management", "Classroom Mgmt"),
    ("Communication_Skills", "Communication"),
    ("Professional_Development", "Professional Dev"),
    ("Use_of_Technology", "Use of Technology"),
]

KPI_COLORS = {
    "Planning & Prep": COLORS["primary"],
    "Subject Knowledge": COLORS["success"],
    "Classroom Mgmt": COLORS["accent"],
    "Communication": COLORS["purple"],
    "Professional Dev": COLORS["pink"],
    "Use of Technology": COLORS["teal"],
}


# ── Data loading ──
@st.cache_data(ttl=600)
def load_fico_kpis() -> pd.DataFrame:
    """Load fico_kpis table from BigQuery."""
    client = get_bq_client()
    cfg = get_config()
    sql = f"""
        SELECT *
        FROM `{cfg['project']}.tbproddb.fico_kpis`
    """
    return client.query(sql).to_dataframe()


@st.cache_data(ttl=600)
def load_student_results() -> pd.DataFrame:
    """Load student_results_data from BigQuery."""
    client = get_bq_client()
    cfg = get_config()
    sql = f"""
        SELECT *
        FROM `{cfg['project']}.tbproddb.student_results_data`
    """
    return client.query(sql).to_dataframe()


# ── Load data ──
try:
    df = load_fico_kpis()
except Exception as e:
    st.error(f"Error loading fico_kpis: {e}")
    st.stop()

if df.empty:
    st.info("No ACR KPI data found in tbproddb.fico_kpis.")
    st.stop()

# ── Filters ──
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    sectors = sorted(df["Sector"].dropna().unique())
    sel_sector = st.multiselect("Sector", sectors)
with col2:
    designations = sorted(df["service_designation"].dropna().unique())
    sel_desig = st.multiselect("Designation", designations)
with col3:
    genders = sorted(df["gender"].dropna().unique())
    sel_gender = st.multiselect("Gender", genders)

filtered = df.copy()
if sel_sector:
    filtered = filtered[filtered["Sector"].isin(sel_sector)]
if sel_desig:
    filtered = filtered[filtered["service_designation"].isin(sel_desig)]
if sel_gender:
    filtered = filtered[filtered["gender"].isin(sel_gender)]

# ── Top KPI Cards ──
section_header("Overall Performance")

n_obs = len(filtered)
n_teachers = filtered["user_id"].nunique()
n_schools = filtered["EMIS"].nunique()
avg_pct = filtered["overall_percentage"].mean() if not filtered.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Observations", f"{n_obs:,}")
c2.metric("Teachers", f"{n_teachers:,}")
c3.metric("Schools", f"{n_schools:,}")
c4.metric("Avg ACR Score", f"{avg_pct:.1f}%")

# ── KPI Averages Radar Chart ──
section_header("ACR KPI Breakdown", "purple")

kpi_avgs = []
kpi_labels = []
for col_name, label in KPI_COLS:
    if col_name in filtered.columns:
        kpi_avgs.append(filtered[col_name].mean() if not filtered.empty else 0)
        kpi_labels.append(label)

col_left, col_right = st.columns(2)

with col_left:
    # Radar chart
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=kpi_avgs + [kpi_avgs[0]],  # close the polygon
        theta=kpi_labels + [kpi_labels[0]],
        fill="toself",
        fillcolor="rgba(59,130,246,0.15)",
        line=dict(color=COLORS["primary"], width=2),
        name="Average",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=10)),
        ),
        showlegend=False,
        height=CHART_H + 40,
        margin=dict(l=60, r=60, t=30, b=30),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_right:
    # Bar chart
    kpi_df = pd.DataFrame({"KPI": kpi_labels, "Average Score": kpi_avgs})
    kpi_df["Color"] = kpi_df["KPI"].map(KPI_COLORS)
    fig_bar = px.bar(
        kpi_df, x="KPI", y="Average Score",
        color="KPI", color_discrete_map=KPI_COLORS,
        text_auto=".1f",
    )
    fig_bar.update_layout(
        yaxis=dict(range=[0, 10], title="Score (out of 10)"),
        xaxis=dict(title=""),
        showlegend=False,
        height=CHART_H + 40,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter"),
    )
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Score Distribution ──
section_header("Overall Score Distribution", "green")

col_hist, col_box = st.columns(2)

with col_hist:
    fig_hist = px.histogram(
        filtered, x="overall_percentage",
        nbins=20,
        labels={"overall_percentage": "Overall Percentage"},
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig_hist.update_layout(
        yaxis_title="Count",
        height=CHART_H,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with col_box:
    fig_box = px.box(
        filtered, y="overall_percentage",
        color_discrete_sequence=[COLORS["success"]],
        labels={"overall_percentage": "Overall %"},
        points="outliers",
    )
    fig_box.update_layout(
        height=CHART_H,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ── By Sector ──
if filtered["Sector"].nunique() > 1:
    section_header("Performance by Sector", "orange")
    sector_avg = (
        filtered.groupby("Sector")["overall_percentage"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "Avg %", "count": "Observations"})
        .sort_values("Avg %", ascending=False)
    )
    fig_sector = px.bar(
        sector_avg, x="Sector", y="Avg %",
        text_auto=".1f",
        color_discrete_sequence=[COLORS["accent"]],
    )
    fig_sector.update_layout(
        yaxis=dict(range=[0, 100], title="Average ACR %"),
        height=CHART_H,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter"),
    )
    fig_sector.update_traces(textposition="outside")
    st.plotly_chart(fig_sector, use_container_width=True)

# ── By Designation ──
if filtered["service_designation"].nunique() > 1:
    section_header("Performance by Designation", "teal")
    desig_avg = (
        filtered.groupby("service_designation")["overall_percentage"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "Avg %", "count": "Observations"})
        .sort_values("Avg %", ascending=False)
    )
    fig_desig = px.bar(
        desig_avg, x="service_designation", y="Avg %",
        text_auto=".1f",
        color_discrete_sequence=[COLORS["teal"]],
    )
    fig_desig.update_layout(
        yaxis=dict(range=[0, 100], title="Average ACR %"),
        xaxis_title="Designation",
        height=CHART_H,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter"),
    )
    fig_desig.update_traces(textposition="outside")
    st.plotly_chart(fig_desig, use_container_width=True)

# ── By Gender ──
if filtered["gender"].nunique() > 1:
    section_header("Performance by Gender", "pink")
    gender_avg = (
        filtered.groupby("gender")["overall_percentage"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "Avg %", "count": "Observations"})
    )
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_gpie = px.pie(
            gender_avg, names="gender", values="Observations",
            color_discrete_sequence=[COLORS["pink"], COLORS["primary"], COLORS["muted"]],
        )
        fig_gpie.update_layout(
            height=CHART_H,
            margin=dict(l=20, r=20, t=20, b=20),
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig_gpie, use_container_width=True)
    with col_g2:
        st.dataframe(
            gender_avg.style.format({"Avg %": "{:.1f}"}),
            use_container_width=True,
            hide_index=True,
        )

# ── Student Results (Early Stage) ──
section_header("Student Results (Early Stage)", "amber")

try:
    sr = load_student_results()
    if sr.empty:
        st.info("No student results data yet.")
    else:
        sr_c1, sr_c2, sr_c3 = st.columns(3)
        sr_c1.metric("Student Records", f"{len(sr):,}")
        sr_c2.metric("Unique Students", f"{sr['student_id'].nunique():,}")
        sr_c3.metric("Avg Student %", f"{sr['percentage'].mean():.1f}%")

        # Student results by subject
        if sr["subject"].nunique() > 1:
            subj_avg = (
                sr.groupby("subject")["percentage"]
                .agg(["mean", "count"])
                .reset_index()
                .rename(columns={"mean": "Avg %", "count": "Records"})
                .sort_values("Avg %", ascending=False)
            )
            fig_subj = px.bar(
                subj_avg, x="subject", y="Avg %",
                text_auto=".1f",
                color_discrete_sequence=[COLORS["warning"]],
            )
            fig_subj.update_layout(
                yaxis=dict(range=[0, 100], title="Avg Student %"),
                xaxis_title="Subject",
                height=CHART_H,
                margin=dict(l=20, r=20, t=20, b=20),
                font=dict(family="Inter"),
            )
            fig_subj.update_traces(textposition="outside")
            st.plotly_chart(fig_subj, use_container_width=True)

        st.caption(
            "This data is under development (539 records). "
            "Additional student data will be integrated in future updates."
        )
except Exception as e:
    st.warning(f"Could not load student results: {e}")

# ── Raw Data ──
with st.expander("View Raw ACR Data"):
    display_cols = [
        "teacher_name", "School", "Sector", "service_designation", "gender",
        "Observation_date", "grade", "subject",
    ] + [c for c, _ in KPI_COLS] + ["total_score_out_of_60", "overall_percentage"]
    available = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[available].sort_values("overall_percentage", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

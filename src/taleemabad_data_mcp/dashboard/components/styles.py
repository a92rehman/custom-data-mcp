"""Shared CSS and design tokens for all dashboard pages."""

import streamlit as st

COLORS = {
    "primary": "#3B82F6",
    "secondary": "#60A5FA",
    "accent": "#F97316",
    "success": "#22C55E",
    "warning": "#EAB308",
    "danger": "#EF4444",
    "text": "#1E293B",
    "muted": "#64748B",
}

DOMAIN_COLORS = {
    "teachers": "#3B82F6",
    "lesson_plans": "#22C55E",
    "observations": "#F97316",
    "training": "#8B5CF6",
    "other": "#94A3B8",
}

CHART_H = 300
CHART_H_SM = 260


def inject_page_css() -> None:
    """Inject shared CSS for deep-dive pages."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Fira Sans', system-ui, sans-serif; }
    .block-container { padding-top: 1.2rem; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #E2E8F0;
        border-radius: 12px; padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetric"] label {
        font-weight: 500; color: #64748B; font-size: 0.85rem;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.5rem; font-weight: 700; color: #1E293B;
    }
    .section-header {
        font-size: 0.95rem; font-weight: 600; color: #1E293B;
        margin: 0.6rem 0 0.3rem 0; padding-bottom: 0.25rem;
        border-bottom: 2px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

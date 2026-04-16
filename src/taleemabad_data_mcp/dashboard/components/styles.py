"""Shared CSS and design tokens for all dashboard pages."""

import streamlit as st

# ── Expanded color palette ──────────────────────────────────────────────
COLORS = {
    "primary": "#3B82F6",
    "primary_light": "#DBEAFE",
    "secondary": "#60A5FA",
    "accent": "#F97316",
    "accent_light": "#FFF7ED",
    "success": "#10B981",
    "success_light": "#D1FAE5",
    "warning": "#F59E0B",
    "warning_light": "#FEF3C7",
    "danger": "#EF4444",
    "danger_light": "#FEE2E2",
    "purple": "#8B5CF6",
    "purple_light": "#EDE9FE",
    "pink": "#EC4899",
    "pink_light": "#FCE7F3",
    "teal": "#14B8A6",
    "teal_light": "#CCFBF1",
    "indigo": "#6366F1",
    "indigo_light": "#E0E7FF",
    "text": "#0F172A",
    "text_secondary": "#475569",
    "muted": "#94A3B8",
    "border": "#E2E8F0",
    "bg": "#F8FAFC",
    "card": "#FFFFFF",
}

# Each domain gets a distinct, vibrant color for easy visual scanning
DOMAIN_COLORS = {
    "teachers": "#3B82F6",      # blue
    "lesson_plans": "#10B981",  # emerald
    "observations": "#F97316",  # orange
    "training": "#8B5CF6",      # violet
    "coaching": "#EC4899",      # pink
    "students": "#14B8A6",      # teal
    "events": "#6366F1",        # indigo
    "platform": "#F59E0B",      # amber
    "teacher_acr": "#059669",   # emerald-700
    "attendance": "#0891B2",    # cyan-600
    "schools": "#7C3AED",      # violet-600
    "other": "#94A3B8",         # slate
}

# Gradient pairs for section headers (from → to)
GRADIENTS = {
    "primary": "linear-gradient(135deg, #3B82F6, #6366F1)",
    "success": "linear-gradient(135deg, #10B981, #14B8A6)",
    "danger": "linear-gradient(135deg, #EF4444, #EC4899)",
    "warning": "linear-gradient(135deg, #F59E0B, #F97316)",
    "purple": "linear-gradient(135deg, #8B5CF6, #6366F1)",
    "teal": "linear-gradient(135deg, #14B8A6, #10B981)",
}

CHART_H = 300
CHART_H_SM = 260


def inject_page_css() -> None:
    """Inject shared CSS for deep-dive pages."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        background: #F8FAFC;
    }
    .block-container { padding-top: 1.2rem; }

    /* ── Page header ── */
    .page-header {
        background: linear-gradient(135deg, #3B82F6 0%, #6366F1 50%, #8B5CF6 100%);
        color: white; border-radius: 16px; padding: 24px 28px;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px rgba(59,130,246,0.2);
    }
    .page-header h2 {
        margin: 0; font-weight: 700; font-size: 1.5rem;
        letter-spacing: -0.02em;
    }
    .page-header p {
        margin: 4px 0 0; opacity: 0.85; font-size: 0.88rem;
        font-weight: 400;
    }

    /* ── KPI metric cards (Streamlit native) ── */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.02);
        transition: box-shadow 0.2s, transform 0.2s;
        border-top: 3px solid #3B82F6;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 4px 16px rgba(59,130,246,0.12);
        transform: translateY(-1px);
    }
    div[data-testid="stMetric"] label {
        font-weight: 600; color: #64748B; font-size: 0.82rem;
        text-transform: uppercase; letter-spacing: 0.04em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.6rem; font-weight: 800; color: #0F172A;
    }

    /* ── Section headers with colored left accent ── */
    .section-header {
        font-size: 0.95rem; font-weight: 700; color: #0F172A;
        margin: 0.8rem 0 0.4rem 0; padding: 8px 14px;
        border-left: 4px solid #3B82F6;
        background: linear-gradient(90deg, #EFF6FF 0%, transparent 100%);
        border-radius: 0 8px 8px 0;
        letter-spacing: -0.01em;
    }

    /* Colored variants */
    .section-header--green {
        border-left-color: #10B981;
        background: linear-gradient(90deg, #D1FAE5 0%, transparent 100%);
    }
    .section-header--orange {
        border-left-color: #F97316;
        background: linear-gradient(90deg, #FFF7ED 0%, transparent 100%);
    }
    .section-header--purple {
        border-left-color: #8B5CF6;
        background: linear-gradient(90deg, #EDE9FE 0%, transparent 100%);
    }
    .section-header--red {
        border-left-color: #EF4444;
        background: linear-gradient(90deg, #FEE2E2 0%, transparent 100%);
    }
    .section-header--teal {
        border-left-color: #14B8A6;
        background: linear-gradient(90deg, #CCFBF1 0%, transparent 100%);
    }
    .section-header--pink {
        border-left-color: #EC4899;
        background: linear-gradient(90deg, #FCE7F3 0%, transparent 100%);
    }
    .section-header--amber {
        border-left-color: #F59E0B;
        background: linear-gradient(90deg, #FEF3C7 0%, transparent 100%);
    }

    /* ── Containers with colored top border ── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    }

    /* ── Tables ── */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Dividers ── */
    hr { border: none; border-top: 1px solid #E2E8F0; margin: 0.8rem 0; }

    /* ── Sidebar polish ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
</style>
""", unsafe_allow_html=True)


def page_header(title: str, subtitle: str) -> None:
    """Render a gradient page header banner."""
    st.markdown(
        f'<div class="page-header">'
        f'<h2>{title}</h2>'
        f'<p>{subtitle}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(text: str, color: str = "") -> None:
    """Render a section header with optional color variant.

    Args:
        text: Header text
        color: One of: green, orange, purple, red, teal, pink, amber (or empty for blue default)
    """
    cls = f"section-header section-header--{color}" if color else "section-header"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

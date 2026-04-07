"""Shared sidebar filters for all dashboard pages."""

import streamlit as st

from taleemabad_data_mcp.dashboard.data.queries import get_distinct_domains, get_distinct_users


def render_sidebar_filters() -> dict:
    """Render sidebar filters and return selected values.

    Returns:
        dict with keys: days, users, domains
    """
    st.sidebar.header("Filters")

    days = st.sidebar.selectbox(
        "Time range",
        options=[7, 14, 30, 60, 90],
        index=2,
        format_func=lambda x: f"Last {x} days",
    )

    available_users = get_distinct_users(days=90)
    users = st.sidebar.multiselect("Users", options=available_users)

    available_domains = get_distinct_domains(days=90)
    if not available_domains:
        available_domains = ["teachers", "lesson_plans", "observations", "training", "other"]
    domains = st.sidebar.multiselect("Domains", options=available_domains)

    return {
        "days": days,
        "users": users or None,
        "domains": domains or None,
    }

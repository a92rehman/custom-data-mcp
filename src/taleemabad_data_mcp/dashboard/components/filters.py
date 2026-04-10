"""Horizontal top-bar filters for all dashboard pages."""

import streamlit as st

from taleemabad_data_mcp.dashboard.data.queries import (
    get_distinct_domains,
    get_distinct_users,
)

# Fixed 10-minute auto-refresh. Hard browser refresh also works.
REFRESH_SECONDS = 600


def render_filters() -> dict:
    """Render horizontal filter bar at the top of the page.

    Returns:
        dict with keys: days, users, domains
    """
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        days = st.selectbox(
            "Time Range",
            options=[7, 14, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Last {x} days",
        )

    with col2:
        available_users = get_distinct_users(days=90)
        users = st.multiselect("Users", options=available_users)

    with col3:
        available_domains = get_distinct_domains(days=90)
        if not available_domains:
            available_domains = [
                "teachers", "lesson_plans", "observations", "training", "other",
            ]
        domains = st.multiselect("Domains", options=available_domains)

    return {
        "days": days,
        "users": users or None,
        "domains": domains or None,
    }


def get_refresh_seconds() -> int:
    """Get the fixed auto-refresh interval (10 minutes)."""
    return REFRESH_SECONDS

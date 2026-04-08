"""Taleemabad Data MCP — Observatory Dashboard.

Uses st.navigation API for full control over sidebar page labels.
"""

import os
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Taleemabad MCP Observatory",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -- Auth --
def check_password() -> bool:
    """Simple password gate."""
    password = os.environ.get("DASHBOARD_PASSWORD")
    if not password:
        return True
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("Taleemabad MCP Observatory")
    entered = st.text_input("Password", type="password")
    if st.button("Login"):
        if entered == password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False


if not check_password():
    st.stop()

# -- Page navigation with explicit labels --
pages_dir = Path(__file__).parent / "pages"

pg = st.navigation([
    st.Page(pages_dir / "0_Overview.py", title="Overview", default=True),
    st.Page(pages_dir / "1_Query_Analytics.py", title="Query Analytics"),
    st.Page(pages_dir / "2_feedback.py", title="Feedback"),
    st.Page(pages_dir / "3_cost.py", title="Cost"),
    st.Page(pages_dir / "4_errors.py", title="Errors"),
    st.Page(pages_dir / "5_freshness.py", title="Freshness"),
])

pg.run()

"""Taleemabad Data MCP — Observability Dashboard."""

import os

import streamlit as st

st.set_page_config(
    page_title="Taleemabad MCP Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def check_password() -> bool:
    """Simple password gate. Returns True if authenticated."""
    password = os.environ.get("DASHBOARD_PASSWORD")
    if not password:
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("Taleemabad MCP Dashboard")
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

st.title("Taleemabad MCP — Observability Dashboard")
st.markdown(
    "Track adoption, quality, cost, and data freshness of the governed data layer."
)

st.markdown("### Navigate using the sidebar pages:")
st.markdown("""
- **Overview** — Active users, query volume, feedback summary
- **Feedback** — Expectation vs Reality deep dive
- **Cost** — BigQuery cost tracking
- **Errors** — Error rates, governance gaps
- **Freshness** — Data freshness status
""")

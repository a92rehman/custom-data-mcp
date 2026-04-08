"""Auto-refresh support for dashboard pages."""

import streamlit as st


def inject_auto_refresh(seconds: int) -> None:
    """Inject HTML meta refresh tag to auto-reload the page.

    Args:
        seconds: Refresh interval in seconds. 0 disables auto-refresh.
    """
    if seconds > 0:
        st.markdown(
            f'<meta http-equiv="refresh" content="{seconds}">',
            unsafe_allow_html=True,
        )


def clear_cache_if_needed(seconds: int) -> None:
    """Clear Streamlit cache when refresh interval is shorter than default TTL.

    This ensures data refreshes at the rate the user expects,
    not at the hardcoded 300s TTL.
    """
    if seconds > 0 and seconds < 300:
        st.cache_data.clear()

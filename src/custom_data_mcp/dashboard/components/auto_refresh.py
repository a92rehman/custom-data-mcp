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
    """Clear Streamlit cache if needed. Currently a no-op since refresh
    interval (10 min) exceeds the cache TTL (5 min).
    """
    pass

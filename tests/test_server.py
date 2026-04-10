"""Tests for MCP server graceful degradation and new tools."""

from unittest.mock import MagicMock


def test_app_context_missing_credentials():
    """Server should create AppContext with bq_client=None when credentials missing."""
    from taleemabad_data_mcp.server import AppContext

    ctx = AppContext(
        config=MagicMock(),
        bq_client=None,
        audit_logger=MagicMock(),
        cost_estimator=MagicMock(),
        feedback_logger=MagicMock(),
    )
    assert ctx.bq_client is None


def test_credentials_error_message_constant():
    """The error message should mention the credentials file."""
    from taleemabad_data_mcp.server import CREDENTIALS_MISSING_MSG

    assert "niete-bq-prod-48ae5260d1ea.json" in CREDENTIALS_MISSING_MSG


def test_require_bq_returns_error_when_none():
    """_require_bq should return error message when bq_client is None."""
    from taleemabad_data_mcp.server import CREDENTIALS_MISSING_MSG, _require_bq, AppContext

    app = AppContext(
        config=MagicMock(),
        bq_client=None,
        audit_logger=None,
        cost_estimator=None,
        feedback_logger=None,
    )
    assert _require_bq(app) == CREDENTIALS_MISSING_MSG


def test_require_bq_returns_none_when_connected():
    """_require_bq should return None when bq_client exists."""
    from taleemabad_data_mcp.server import _require_bq, AppContext

    app = AppContext(
        config=MagicMock(),
        bq_client=MagicMock(),
        audit_logger=MagicMock(),
        cost_estimator=MagicMock(),
        feedback_logger=MagicMock(),
    )
    assert _require_bq(app) is None

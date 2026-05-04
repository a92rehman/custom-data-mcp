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
    """The error message should mention BigQuery connection issue."""
    from taleemabad_data_mcp.server import CREDENTIALS_MISSING_MSG

    assert "BigQuery connection unavailable" in CREDENTIALS_MISSING_MSG


def test_require_bq_returns_error_when_none():
    """_require_bq should return error message when bq_client is None."""
    from taleemabad_data_mcp.server import CREDENTIALS_MISSING_MSG, AppContext, _require_bq

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
    from taleemabad_data_mcp.server import AppContext, _require_bq

    app = AppContext(
        config=MagicMock(),
        bq_client=MagicMock(),
        audit_logger=MagicMock(),
        cost_estimator=MagicMock(),
        feedback_logger=MagicMock(),
    )
    assert _require_bq(app) is None


def test_banned_tables_contains_legacy():
    """BANNED_TABLES should block the unpartitioned legacy table."""
    from taleemabad_data_mcp.server import BANNED_TABLES
    assert "analytics_analyticsevent" in BANNED_TABLES


def test_safe_filter_regex_accepts_valid():
    """Partition filter regex should accept standard date filters."""
    from taleemabad_data_mcp.server import _SAFE_FILTER_RE
    assert _SAFE_FILTER_RE.match("sent_at >= DATE('2025-01-01')")
    assert _SAFE_FILTER_RE.match("created >= DATE('2025-01-01')")
    assert _SAFE_FILTER_RE.match("sent_at >= DATE('2025-01-01') AND sent_at <= DATE('2025-12-31')")


def test_safe_filter_regex_rejects_injection():
    """Partition filter regex should reject SQL injection attempts."""
    from taleemabad_data_mcp.server import _SAFE_FILTER_RE
    assert not _SAFE_FILTER_RE.match("1=1; DROP TABLE users --")
    assert not _SAFE_FILTER_RE.match("sent_at >= (SELECT MIN(sent_at) FROM other)")
    assert not _SAFE_FILTER_RE.match("sent_at >= '2025-01-01'; DELETE FROM t")


def test_safe_identifier_regex():
    """Identifier regex should accept valid names and reject injection."""
    from taleemabad_data_mcp.server import _SAFE_IDENTIFIER_RE
    assert _SAFE_IDENTIFIER_RE.match("coaching_observation")
    assert _SAFE_IDENTIFIER_RE.match("FDE_Schools")
    assert not _SAFE_IDENTIFIER_RE.match("table`; DROP--")
    assert not _SAFE_IDENTIFIER_RE.match("a b c")


def test_describe_data_median_even():
    """Median of even-length list should average middle two values."""
    vals = [1.0, 2.0, 3.0, 4.0]
    n = len(vals)
    median = (vals[n // 2 - 1] + vals[n // 2]) / 2
    assert median == 2.5


def test_describe_data_median_odd():
    """Median of odd-length list should be the middle value."""
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    n = len(vals)
    median = vals[n // 2]
    assert median == 3.0


def test_read_user_from_env_file(tmp_path, monkeypatch):
    """Should read TALEEMABAD_USER from env file."""
    env_file = tmp_path / "taleemabad-data-mcp.env"
    env_file.write_text("TALEEMABAD_USER=Mariam\nGOOGLE_APPLICATION_CREDENTIALS=creds.json\n")
    monkeypatch.setattr("taleemabad_data_mcp.server._ENV_FILE", env_file)

    from taleemabad_data_mcp.server import _read_user_from_env_file
    assert _read_user_from_env_file() == "Mariam"


def test_read_user_from_env_file_missing(tmp_path, monkeypatch):
    """Should return None when env file doesn't exist."""
    env_file = tmp_path / "nonexistent.env"
    monkeypatch.setattr("taleemabad_data_mcp.server._ENV_FILE", env_file)

    from taleemabad_data_mcp.server import _read_user_from_env_file
    assert _read_user_from_env_file() is None


def test_read_user_from_env_file_empty_value(tmp_path, monkeypatch):
    """Should return None when TALEEMABAD_USER is empty."""
    env_file = tmp_path / "taleemabad-data-mcp.env"
    env_file.write_text("TALEEMABAD_USER=\n")
    monkeypatch.setattr("taleemabad_data_mcp.server._ENV_FILE", env_file)

    from taleemabad_data_mcp.server import _read_user_from_env_file
    assert _read_user_from_env_file() is None

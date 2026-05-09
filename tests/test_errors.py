"""Tests for BigQuery error classification and structured responses."""

from custom_data_mcp.engine.errors import (
    BIGQUERY_UNAVAILABLE,
    COST_EXCEEDED,
    MISSING_PARTITION,
    OTHER,
    PERMISSION_DENIED,
    SCHEMA_DRIFT,
    SYNTAX_ERROR,
    TIMEOUT,
    classify_bigquery_error,
    format_error_response,
    format_success_response,
    sql_hash,
)


def _make_exc(name: str, msg: str) -> Exception:
    """Create an exception with a specific class name for testing."""
    exc_class = type(name, (Exception,), {})
    return exc_class(msg)


class TestClassifyBigqueryError:
    def test_not_found_table(self):
        exc = _make_exc("NotFound", "Not found: Table niete-bq-prod.tbproddb.missing_table")
        error_class, hints = classify_bigquery_error(exc, "SELECT * FROM tbproddb.missing_table")
        assert error_class == SCHEMA_DRIFT
        assert "table_referenced" in hints

    def test_not_found_generic(self):
        exc = _make_exc("NotFound", "Not found: some resource")
        error_class, hints = classify_bigquery_error(exc, "SELECT 1")
        assert error_class == SCHEMA_DRIFT
        assert "hint" in hints

    def test_bad_request_column_not_found(self):
        exc = _make_exc("BadRequest", "400 Unrecognized name: old_column_name at [1:8]")
        error_class, hints = classify_bigquery_error(exc, "SELECT old_column_name FROM t")
        assert error_class == SCHEMA_DRIFT
        assert hints.get("column_referenced") == "old_column_name"

    def test_bad_request_missing_partition(self):
        exc = _make_exc(
            "BadRequest",
            "Cannot query over table 'analytics_events' without a filter over column(s) 'sent_at'",
        )
        error_class, hints = classify_bigquery_error(exc, "SELECT * FROM analytics_events")
        assert error_class == MISSING_PARTITION

    def test_bad_request_cost_exceeded(self):
        exc = _make_exc(
            "BadRequest",
            "query will process 68,000,000,000 bytes, exceeding limit",
        )
        error_class, hints = classify_bigquery_error(exc, "SELECT * FROM big_table")
        assert error_class == COST_EXCEEDED

    def test_bad_request_syntax_error(self):
        exc = _make_exc("BadRequest", "400 Syntax error: Unexpected 'SELECCT' at [1:1]")
        error_class, hints = classify_bigquery_error(exc, "SELECCT 1")
        assert error_class == SYNTAX_ERROR

    def test_forbidden(self):
        exc = _make_exc("Forbidden", "403 Access denied: Table tbproddb.secret")
        error_class, _ = classify_bigquery_error(exc, "SELECT * FROM secret")
        assert error_class == PERMISSION_DENIED

    def test_timeout(self):
        exc = _make_exc("DeadlineExceeded", "Deadline exceeded")
        error_class, _ = classify_bigquery_error(exc, "SELECT * FROM big")
        assert error_class == TIMEOUT

    def test_service_unavailable(self):
        exc = _make_exc("ServiceUnavailable", "503 Service unavailable")
        error_class, _ = classify_bigquery_error(exc, "SELECT 1")
        assert error_class == BIGQUERY_UNAVAILABLE

    def test_internal_server_error(self):
        exc = _make_exc("InternalServerError", "500 Internal error")
        error_class, _ = classify_bigquery_error(exc, "SELECT 1")
        assert error_class == BIGQUERY_UNAVAILABLE

    def test_unknown_error(self):
        exc = _make_exc("WeirdError", "something unexpected")
        error_class, hints = classify_bigquery_error(exc, "SELECT 1")
        assert error_class == OTHER
        assert "hint" in hints


class TestFormatErrorResponse:
    def test_structure(self):
        exc = Exception("test error")
        resp = format_error_response(
            SYNTAX_ERROR, exc, "evt-123", table_referenced="foo"
        )
        assert resp["status"] == "error"
        assert resp["error_class"] == SYNTAX_ERROR
        assert resp["error_type"] == "Exception"
        assert resp["event_id"] == "evt-123"
        assert resp["table_referenced"] == "foo"
        assert resp["retryable"] is False

    def test_retryable_for_timeout(self):
        exc = Exception("timeout")
        resp = format_error_response(TIMEOUT, exc, "evt-456")
        assert resp["retryable"] is True

    def test_retryable_for_unavailable(self):
        exc = Exception("503")
        resp = format_error_response(BIGQUERY_UNAVAILABLE, exc, "evt-789")
        assert resp["retryable"] is True

    def test_message_truncation(self):
        exc = Exception("x" * 1000)
        resp = format_error_response(OTHER, exc, "evt-trunc")
        assert len(resp["message"]) <= 500


class TestFormatSuccessResponse:
    def test_structure(self):
        rows = [{"id": 1, "name": "test"}]
        resp = format_success_response(
            rows, "evt-ok", 0.001, ["table_a"]
        )
        assert resp["status"] == "ok"
        assert resp["rows"] == rows
        assert resp["rows_returned"] == 1
        assert resp["cost_usd"] == 0.001
        assert resp["tables_accessed"] == ["table_a"]
        assert resp["event_id"] == "evt-ok"

    def test_empty_rows(self):
        resp = format_success_response([], "evt-empty", 0.0, [])
        assert resp["rows_returned"] == 0


class TestSqlHash:
    def test_deterministic(self):
        assert sql_hash("SELECT 1") == sql_hash("SELECT 1")

    def test_different_sql_different_hash(self):
        assert sql_hash("SELECT 1") != sql_hash("SELECT 2")

    def test_length(self):
        assert len(sql_hash("SELECT 1")) == 16

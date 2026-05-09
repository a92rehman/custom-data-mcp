"""Tests for query-fixer integration — error classification drives fix decisions.

The query-fixer agent is a markdown file, so we test the Python infrastructure
it relies on: error classification, error→category mapping, and the give-up
logic boundaries.
"""

import json

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
)


# The error_class → ticket category mapping from data-analyst Phase 4
ERROR_CLASS_TO_CATEGORY = {
    SCHEMA_DRIFT: "schema",
    MISSING_PARTITION: "partition",
    SYNTAX_ERROR: "syntax",
    COST_EXCEEDED: "cost",
    BIGQUERY_UNAVAILABLE: "connection",
    TIMEOUT: "connection",
    PERMISSION_DENIED: "connection",
    OTHER: "other",
}

# System-level errors that should NOT go to query-fixer
SYSTEM_ERRORS = {BIGQUERY_UNAVAILABLE, TIMEOUT, PERMISSION_DENIED}


def _make_exc(name: str, msg: str) -> Exception:
    exc_class = type(name, (Exception,), {})
    return exc_class(msg)


class TestSchemaFriftFix:
    """SCHEMA_DRIFT errors should map to 'schema' category and be fixable."""

    def test_column_renamed_classified(self):
        exc = _make_exc("BadRequest", "400 Unrecognized name: old_col at [1:8]")
        error_class, hints = classify_bigquery_error(exc, "SELECT old_col FROM t")
        assert error_class == SCHEMA_DRIFT
        assert ERROR_CLASS_TO_CATEGORY[error_class] == "schema"
        assert error_class not in SYSTEM_ERRORS  # should go to query-fixer

    def test_table_not_found_classified(self):
        exc = _make_exc("NotFound", "Not found: Table niete-bq-prod.tbproddb.old_table")
        error_class, hints = classify_bigquery_error(exc, "SELECT * FROM old_table")
        assert error_class == SCHEMA_DRIFT
        assert hints.get("table_referenced") is not None

    def test_error_response_includes_column(self):
        exc = _make_exc("BadRequest", "400 Unrecognized name: missing_col at [1:8]")
        error_class, hints = classify_bigquery_error(exc, "SELECT missing_col FROM t")
        resp = format_error_response(error_class, exc, "evt-1", **hints)
        assert resp["error_class"] == SCHEMA_DRIFT
        assert resp["column_referenced"] == "missing_col"


class TestMissingPartitionFix:
    """MISSING_PARTITION errors should map to 'partition' and be fixable."""

    def test_partition_required(self):
        exc = _make_exc(
            "BadRequest",
            "Cannot query over table 'analytics_events' without a filter over column(s) 'sent_at'",
        )
        error_class, _ = classify_bigquery_error(exc, "SELECT * FROM analytics_events")
        assert error_class == MISSING_PARTITION
        assert ERROR_CLASS_TO_CATEGORY[error_class] == "partition"
        assert error_class not in SYSTEM_ERRORS

    def test_partition_error_response_retryable(self):
        exc = _make_exc(
            "BadRequest",
            "Cannot query over table 't' without a filter over column(s) 'dt'",
        )
        error_class, hints = classify_bigquery_error(exc, "SELECT * FROM t")
        resp = format_error_response(error_class, exc, "evt-2", **hints)
        assert resp["retryable"] is False  # partition errors are fixable, not auto-retryable


class TestSyntaxErrorFix:
    """SYNTAX_ERROR errors should map to 'syntax' and be fixable."""

    def test_typo(self):
        exc = _make_exc("BadRequest", "400 Syntax error: Unexpected 'SELECCT'")
        error_class, _ = classify_bigquery_error(exc, "SELECCT 1")
        assert error_class == SYNTAX_ERROR
        assert ERROR_CLASS_TO_CATEGORY[error_class] == "syntax"


class TestCostExceededFix:
    """COST_EXCEEDED errors should map to 'cost' and be fixable."""

    def test_bytes_exceeded(self):
        exc = _make_exc(
            "BadRequest",
            "query will process 68,000,000,000 bytes, exceeding limit",
        )
        error_class, hints = classify_bigquery_error(exc, "SELECT * FROM big_table")
        assert error_class == COST_EXCEEDED
        assert ERROR_CLASS_TO_CATEGORY[error_class] == "cost"
        assert error_class not in SYSTEM_ERRORS


class TestSystemErrorsRouteToDoctor:
    """System-level errors should NOT go to query-fixer."""

    def test_unavailable_is_system(self):
        exc = _make_exc("ServiceUnavailable", "503")
        error_class, _ = classify_bigquery_error(exc, "SELECT 1")
        assert error_class == BIGQUERY_UNAVAILABLE
        assert error_class in SYSTEM_ERRORS

    def test_timeout_is_system(self):
        exc = _make_exc("DeadlineExceeded", "timeout")
        error_class, _ = classify_bigquery_error(exc, "SELECT 1")
        assert error_class == TIMEOUT
        assert error_class in SYSTEM_ERRORS

    def test_permission_is_system(self):
        exc = _make_exc("Forbidden", "403 Access denied")
        error_class, _ = classify_bigquery_error(exc, "SELECT 1")
        assert error_class == PERMISSION_DENIED
        assert error_class in SYSTEM_ERRORS


class TestGiveUpBoundary:
    """The fixer must give up after attempt 3 — verified by checking the
    error response format includes all info needed for the give-up decision."""

    def test_error_response_has_event_id(self):
        """Parent needs event_id to track across attempts."""
        exc = Exception("test")
        resp = format_error_response(SYNTAX_ERROR, exc, "evt-track")
        assert resp["event_id"] == "evt-track"

    def test_all_error_classes_mapped(self):
        """Every classified error class has a ticket category."""
        all_classes = {
            SCHEMA_DRIFT, MISSING_PARTITION, SYNTAX_ERROR, COST_EXCEEDED,
            BIGQUERY_UNAVAILABLE, TIMEOUT, PERMISSION_DENIED, OTHER,
        }
        assert all_classes == set(ERROR_CLASS_TO_CATEGORY.keys())

    def test_error_response_serializable(self):
        """Error responses must be JSON-serializable for agent communication."""
        exc = _make_exc("BadRequest", "test error with special chars: <>&\"'")
        resp = format_error_response(SYNTAX_ERROR, exc, "evt-json")
        serialized = json.dumps(resp, default=str)
        parsed = json.loads(serialized)
        assert parsed["error_class"] == SYNTAX_ERROR

"""BigQuery error classification and structured response formatting."""

from __future__ import annotations

import hashlib
import re
from typing import Any


# Error class constants
SCHEMA_DRIFT = "SCHEMA_DRIFT"
MISSING_PARTITION = "MISSING_PARTITION"
SYNTAX_ERROR = "SYNTAX_ERROR"
COST_EXCEEDED = "COST_EXCEEDED"
PERMISSION_DENIED = "PERMISSION_DENIED"
TIMEOUT = "TIMEOUT"
BIGQUERY_UNAVAILABLE = "BIGQUERY_UNAVAILABLE"
RULE_NOT_FOUND = "RULE_NOT_FOUND"
OTHER = "OTHER"

# Patterns for column-not-found errors
_COLUMN_NOT_FOUND_RE = re.compile(
    r"Unrecognized name: (\S+)",
    re.IGNORECASE,
)
_TABLE_NOT_FOUND_RE = re.compile(
    r"Not found: Table (\S+)",
    re.IGNORECASE,
)
_BYTES_EXCEEDED_RE = re.compile(
    r"query will process (\d[\d,]*) bytes",
    re.IGNORECASE,
)


def classify_bigquery_error(
    exc: Exception,
    sql: str,
) -> tuple[str, dict[str, Any]]:
    """Classify a BigQuery exception into an error class with hints.

    Args:
        exc: The exception raised by the BigQuery client.
        sql: The SQL that caused the error.

    Returns:
        A tuple of (error_class, hints) where hints is a dict with
        context-specific information for the fixer agent.
    """
    exc_name = type(exc).__name__
    msg = str(exc)

    # google.api_core.exceptions.NotFound
    if exc_name == "NotFound" or "NotFound" in exc_name:
        # Distinguish table not found vs column not found
        table_match = _TABLE_NOT_FOUND_RE.search(msg)
        if table_match:
            return SCHEMA_DRIFT, {
                "table_referenced": table_match.group(1),
                "hint": "Table does not exist or was renamed.",
            }
        return SCHEMA_DRIFT, {"hint": "Resource not found."}

    # google.api_core.exceptions.BadRequest
    if exc_name == "BadRequest" or "BadRequest" in exc_name:
        col_match = _COLUMN_NOT_FOUND_RE.search(msg)
        if col_match:
            return SCHEMA_DRIFT, {
                "column_referenced": col_match.group(1),
                "hint": f"Column '{col_match.group(1)}' not found. Check schema.",
            }

        if "Cannot query over table" in msg and "without a filter" in msg:
            return MISSING_PARTITION, {
                "hint": "Query requires a partition filter.",
            }

        bytes_match = _BYTES_EXCEEDED_RE.search(msg)
        if bytes_match:
            return COST_EXCEEDED, {
                "bytes_estimated": bytes_match.group(1),
                "hint": "Query exceeds maximum_bytes_billed. Narrow the date range.",
            }

        return SYNTAX_ERROR, {"hint": "SQL syntax or semantic error."}

    # google.api_core.exceptions.Forbidden
    if exc_name == "Forbidden" or "Forbidden" in exc_name:
        return PERMISSION_DENIED, {
            "hint": "Insufficient permissions for this query or table.",
        }

    # Timeout / DeadlineExceeded
    if "Timeout" in exc_name or "DeadlineExceeded" in exc_name:
        return TIMEOUT, {"hint": "Query timed out. Try a smaller date range."}

    # ServiceUnavailable / InternalServerError / 503
    if any(
        kw in exc_name
        for kw in ("ServiceUnavailable", "InternalServerError", "ServerError")
    ):
        return BIGQUERY_UNAVAILABLE, {
            "hint": "BigQuery is temporarily unavailable. Retry later.",
        }

    # Fallback
    return OTHER, {"hint": msg[:200]}


def format_error_response(
    error_class: str,
    exc: Exception,
    event_id: str,
    **hints: Any,
) -> dict[str, Any]:
    """Format a structured error response dict.

    Args:
        error_class: One of the error class constants.
        exc: The original exception.
        event_id: The audit log event_id for traceability.
        **hints: Additional context (table_referenced, column_referenced, etc.)

    Returns:
        A structured dict suitable for JSON serialization.
    """
    retryable = error_class in (TIMEOUT, BIGQUERY_UNAVAILABLE)

    return {
        "status": "error",
        "error_class": error_class,
        "error_type": type(exc).__name__,
        "message": str(exc)[:500],
        "table_referenced": hints.get("table_referenced"),
        "column_referenced": hints.get("column_referenced"),
        "retryable": retryable,
        "event_id": event_id,
    }


def format_success_response(
    rows: list[dict[str, Any]],
    event_id: str,
    cost_usd: float,
    tables_accessed: list[str],
) -> dict[str, Any]:
    """Format a structured success response dict.

    Args:
        rows: Query result rows (already truncated to max 100).
        event_id: The audit log event_id.
        cost_usd: Estimated cost in USD.
        tables_accessed: List of table IDs accessed.

    Returns:
        A structured dict suitable for JSON serialization.
    """
    return {
        "status": "ok",
        "rows": rows,
        "event_id": event_id,
        "rows_returned": len(rows),
        "cost_usd": round(cost_usd, 6),
        "tables_accessed": tables_accessed,
    }


def sql_hash(sql: str) -> str:
    """Return SHA-256 hash of SQL for privacy-safe logging."""
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16]

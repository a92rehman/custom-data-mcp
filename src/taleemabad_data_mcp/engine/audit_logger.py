"""Immutable audit log for all MCP interactions."""

import structlog

from taleemabad_data_mcp.models.audit import AuditLogEntry

logger = structlog.get_logger()


class AuditLogger:
    """Creates and stores immutable audit log entries."""

    def __init__(self) -> None:
        self._entries: list[AuditLogEntry] = []

    def log(
        self,
        query_text: str,
        session_id: str | None = None,
        user_id: str | None = None,
        matched_metric: str | None = None,
        generated_sql: str | None = None,
        tables_accessed: list[str] | None = None,
        rows_returned: int | None = None,
        execution_ms: int | None = None,
        result_cached: bool = False,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> AuditLogEntry:
        """Create an immutable audit log entry."""
        entry = AuditLogEntry(
            query_text=query_text,
            session_id=session_id,
            user_id=user_id,
            matched_metric=matched_metric,
            generated_sql=generated_sql,
            tables_accessed=tables_accessed or [],
            rows_returned=rows_returned,
            execution_ms=execution_ms,
            result_cached=result_cached,
            error_type=error_type,
            error_message=error_message,
        )
        self._entries.append(entry)
        logger.info(
            "audit_log_entry",
            event_id=entry.event_id,
            query_text=entry.query_text,
            matched_metric=entry.matched_metric,
            error_type=entry.error_type,
        )
        return entry

    @property
    def entries(self) -> list[AuditLogEntry]:
        return list(self._entries)

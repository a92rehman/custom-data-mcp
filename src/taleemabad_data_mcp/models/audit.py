"""Audit log entry model."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_name: str = "unknown"
    hostname: str = ""
    session_id: str | None = None
    query_text: str
    matched_metric: str | None = None
    generated_sql: str | None = None
    tables_accessed: list[str] = []
    rows_returned: int | None = None
    execution_ms: int | None = None
    cost_bytes: int | None = None
    cost_usd: float | None = None
    result_cached: bool = False
    error_type: str | None = None
    error_message: str | None = None

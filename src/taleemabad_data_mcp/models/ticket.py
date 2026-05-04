"""Ticket model for self-healing loop tracking."""

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def _make_ticket_id() -> str:
    """Generate a ticket ID in the format TKT-YYYYMMDD-<6 hex>."""
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    hex_part = uuid.uuid4().hex[:6]
    return f"TKT-{date_part}-{hex_part}"


class Ticket(BaseModel):
    ticket_id: str = Field(default_factory=_make_ticket_id)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_email: str | None = None
    hostname: str = ""
    loop: Literal["query", "system"]
    category: Literal[
        "connection",
        "identity",
        "rules",
        "plugin",
        "schema",
        "syntax",
        "partition",
        "cost",
        "other",
    ]
    symptom: str
    severity: Literal["info", "warning", "error", "critical"] = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)
    diagnosis: str | None = None
    actions_attempted: list[dict[str, Any]] = Field(default_factory=list)
    status: Literal[
        "open",
        "diagnosing",
        "auto_fixed",
        "user_action_required",
        "escalated",
        "abandoned",
    ] = "open"
    related_event_id: str | None = None
    escalated_to: str | None = None
    resolution_notes: str | None = None

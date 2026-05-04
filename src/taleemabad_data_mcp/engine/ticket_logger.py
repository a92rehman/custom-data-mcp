"""Ticket logger — writes to local JSONL with best-effort BigQuery sync.

Mirrors the audit_logger.py pattern: local file is always written,
BigQuery write is best-effort and never blocks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from taleemabad_data_mcp.models.ticket import Ticket

if TYPE_CHECKING:
    from google.cloud import bigquery

logger = structlog.get_logger()

_LOCAL_LOG_DIR = Path.home() / ".claude" / "taleemabad-logs"
_LOCAL_TICKET_FILE = _LOCAL_LOG_DIR / "tickets.jsonl"


class TicketLogger:
    """Manages ticket lifecycle with JSONL persistence and optional BigQuery sync."""

    def __init__(
        self,
        bq_client: "bigquery.Client | None" = None,
        project: str = "",
        audit_dataset: str = "mcp_audit",
        ticket_table: str = "system_tickets",
        user_email: str | None = None,
        hostname: str = "",
    ) -> None:
        self._bq_client = bq_client
        self._table_id = f"{project}.{audit_dataset}.{ticket_table}" if project else ""
        self._user_email = user_email
        self._hostname = hostname
        self._table_exists: bool | None = None

    def open_ticket(
        self,
        loop: str,
        category: str,
        symptom: str,
        severity: str = "warning",
        evidence: dict[str, Any] | None = None,
        diagnosis: str | None = None,
        related_event_id: str | None = None,
    ) -> Ticket:
        """Create and persist a new ticket."""
        ticket = Ticket(
            user_email=self._user_email,
            hostname=self._hostname,
            loop=loop,
            category=category,
            symptom=symptom,
            severity=severity,
            evidence=evidence or {},
            diagnosis=diagnosis,
            related_event_id=related_event_id,
        )
        self._write_local(ticket)
        self._write_bigquery(ticket)
        logger.info(
            "ticket_opened",
            ticket_id=ticket.ticket_id,
            loop=loop,
            category=category,
            symptom=symptom,
        )
        return ticket

    def update_ticket(
        self,
        ticket_id: str,
        action: dict[str, Any] | None = None,
        diagnosis: str | None = None,
        status: str | None = None,
    ) -> Ticket | None:
        """Update an existing ticket. Returns the updated ticket or None."""
        ticket = self._find_ticket(ticket_id)
        if ticket is None:
            logger.warning("ticket_not_found", ticket_id=ticket_id)
            return None

        if action:
            ticket.actions_attempted.append(action)
        if diagnosis:
            ticket.diagnosis = diagnosis
        if status:
            ticket.status = status  # type: ignore[assignment]
        ticket.updated_at = datetime.now(UTC)

        self._rewrite_local(ticket)
        self._write_bigquery(ticket)
        logger.info("ticket_updated", ticket_id=ticket_id, status=ticket.status)
        return ticket

    def close_ticket(
        self,
        ticket_id: str,
        status: str,
        resolution_notes: str | None = None,
        escalated_to: str | None = None,
    ) -> Ticket | None:
        """Close a ticket with a final status."""
        ticket = self._find_ticket(ticket_id)
        if ticket is None:
            logger.warning("ticket_not_found", ticket_id=ticket_id)
            return None

        ticket.status = status  # type: ignore[assignment]
        ticket.resolution_notes = resolution_notes
        ticket.escalated_to = escalated_to
        ticket.updated_at = datetime.now(UTC)

        self._rewrite_local(ticket)
        self._write_bigquery(ticket)
        logger.info("ticket_closed", ticket_id=ticket_id, status=status)
        return ticket

    def read_local_tickets(
        self,
        status: str | None = None,
        category: str | None = None,
        since: datetime | None = None,
    ) -> list[Ticket]:
        """Read tickets from local JSONL file with optional filters."""
        if not _LOCAL_TICKET_FILE.exists():
            return []

        tickets: list[Ticket] = []
        seen_ids: set[str] = set()

        # Read all lines, keeping last version of each ticket_id
        all_tickets: dict[str, Ticket] = {}
        for line in _LOCAL_TICKET_FILE.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            try:
                t = Ticket.model_validate_json(line)
                all_tickets[t.ticket_id] = t
            except Exception:
                continue

        for t in all_tickets.values():
            if status and t.status != status:
                continue
            if category and t.category != category:
                continue
            if since and t.created_at < since.replace(tzinfo=UTC):
                continue
            if t.ticket_id not in seen_ids:
                tickets.append(t)
                seen_ids.add(t.ticket_id)

        return tickets

    def _find_ticket(self, ticket_id: str) -> Ticket | None:
        """Find the latest version of a ticket by ID from local storage."""
        if not _LOCAL_TICKET_FILE.exists():
            return None

        latest: Ticket | None = None
        for line in _LOCAL_TICKET_FILE.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            try:
                t = Ticket.model_validate_json(line)
                if t.ticket_id == ticket_id:
                    latest = t
            except Exception:
                continue
        return latest

    def _write_local(self, ticket: Ticket) -> None:
        """Append ticket to local JSONL file."""
        try:
            _LOCAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
            with _LOCAL_TICKET_FILE.open("a", encoding="utf-8") as f:
                f.write(ticket.model_dump_json() + "\n")
        except Exception as e:
            logger.warning("ticket_local_write_failed", error=str(e))

    def _rewrite_local(self, ticket: Ticket) -> None:
        """Append updated ticket version to JSONL (append-only log)."""
        self._write_local(ticket)

    def _write_bigquery(self, ticket: Ticket) -> None:
        """Insert/update ticket in BigQuery (best-effort, never blocks)."""
        if not self._bq_client or not self._table_id:
            return
        try:
            if self._table_exists is None:
                self._ensure_ticket_table()

            row = ticket.model_dump()
            row["created_at"] = row["created_at"].isoformat()
            row["updated_at"] = row["updated_at"].isoformat()
            # Serialize nested dicts/lists as JSON strings for BQ
            import json
            row["evidence"] = json.dumps(row["evidence"], default=str)
            row["actions_attempted"] = json.dumps(row["actions_attempted"], default=str)

            errors = self._bq_client.insert_rows_json(self._table_id, [row])
            if errors:
                logger.warning("ticket_bq_write_failed", errors=errors)
        except Exception as e:
            logger.warning("ticket_bq_write_failed", error=str(e))

    def _ensure_ticket_table(self) -> None:
        """Create ticket dataset and table if they don't exist."""
        from google.cloud import bigquery

        try:
            parts = self._table_id.split(".")
            project, dataset_id = parts[0], parts[1]

            dataset_ref = bigquery.DatasetReference(project, dataset_id)
            try:
                self._bq_client.get_dataset(dataset_ref)
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                self._bq_client.create_dataset(dataset, exists_ok=True)

            schema = [
                bigquery.SchemaField("ticket_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP"),
                bigquery.SchemaField("user_email", "STRING"),
                bigquery.SchemaField("hostname", "STRING"),
                bigquery.SchemaField("loop", "STRING"),
                bigquery.SchemaField("category", "STRING"),
                bigquery.SchemaField("symptom", "STRING"),
                bigquery.SchemaField("severity", "STRING"),
                bigquery.SchemaField("evidence", "STRING"),  # JSON string
                bigquery.SchemaField("diagnosis", "STRING"),
                bigquery.SchemaField("actions_attempted", "STRING"),  # JSON string
                bigquery.SchemaField("status", "STRING"),
                bigquery.SchemaField("related_event_id", "STRING"),
                bigquery.SchemaField("escalated_to", "STRING"),
                bigquery.SchemaField("resolution_notes", "STRING"),
            ]
            table = bigquery.Table(self._table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="created_at",
            )
            self._bq_client.create_table(table, exists_ok=True)

            self._table_exists = True
            logger.info("ticket_table_ready", table=self._table_id)
        except Exception as e:
            self._table_exists = False
            logger.warning("ticket_table_setup_failed", error=str(e))

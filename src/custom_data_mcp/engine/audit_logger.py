"""Audit logger — writes to BigQuery with local JSON Lines fallback."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from custom_data_mcp.models.audit import AuditLogEntry

if TYPE_CHECKING:
    from google.cloud import bigquery

logger = structlog.get_logger()

_LOCAL_LOG_DIR = Path.home() / ".claude" / "custom-data-logs"
_LOCAL_LOG_FILE = _LOCAL_LOG_DIR / "activity.jsonl"


class AuditLogger:
    """Creates audit log entries and persists them to BigQuery + local file."""

    def __init__(
        self,
        bq_client: bigquery.Client | None = None,
        project: str = "",
        audit_dataset: str = "mcp_audit",
        audit_table: str = "activity_log",
        user_name: str = "unknown",
        hostname: str = "",
        remote_mode: bool = False,
    ) -> None:
        self._bq_client = bq_client
        self._table_id = f"{project}.{audit_dataset}.{audit_table}" if project else ""
        self._user_name = user_name
        self._hostname = hostname
        self._table_exists: bool | None = None
        self._remote_mode = remote_mode

    def log(
        self,
        query_text: str,
        session_id: str | None = None,
        matched_metric: str | None = None,
        generated_sql: str | None = None,
        tables_accessed: list[str] | None = None,
        rows_returned: int | None = None,
        execution_ms: int | None = None,
        cost_bytes: int | None = None,
        cost_usd: float | None = None,
        result_cached: bool = False,
        error_type: str | None = None,
        error_message: str | None = None,
        domain: str = "other",
        user_email: str | None = None,
    ) -> AuditLogEntry:
        """Create an audit log entry and persist it.

        Args:
            user_email: Per-request email from HTTP header (remote mode).
                        Overrides the default user_name when provided.
        """
        # Derive user fields from email if provided (remote mode)
        if user_email:
            user_name = user_email.split("@")[0]
            user_domain = user_email.split("@")[1] if "@" in user_email else None
        else:
            user_name = self._user_name
            user_domain = None

        entry = AuditLogEntry(
            query_text=query_text,
            user_name=user_name,
            user_email=user_email,
            user_domain=user_domain,
            hostname=self._hostname,
            session_id=session_id,
            matched_metric=matched_metric,
            generated_sql=generated_sql,
            tables_accessed=tables_accessed or [],
            rows_returned=rows_returned,
            execution_ms=execution_ms,
            cost_bytes=cost_bytes,
            cost_usd=cost_usd,
            result_cached=result_cached,
            error_type=error_type,
            error_message=error_message,
            domain=domain,
        )

        # Write to local file only in local mode (Railway filesystem is ephemeral)
        if not self._remote_mode:
            self._write_local(entry)

        # Try BigQuery write (best-effort, never block)
        if self._bq_client and self._table_id:
            self._write_bigquery(entry)

        logger.info(
            "audit_log_entry",
            event_id=entry.event_id,
            user_name=entry.user_name,
            user_email=entry.user_email,
            query_text=entry.query_text[:100],
            error_type=entry.error_type,
        )
        return entry

    def _write_local(self, entry: AuditLogEntry) -> None:
        """Append entry to local JSON Lines file."""
        try:
            _LOCAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
            with _LOCAL_LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.warning("audit_local_write_failed", error=str(e))

    def _write_bigquery(self, entry: AuditLogEntry) -> None:
        """Insert entry into BigQuery audit table."""
        try:
            if self._table_exists is None:
                self._ensure_audit_table()

            row = entry.model_dump()
            row["timestamp"] = row["timestamp"].isoformat()
            errors = self._bq_client.insert_rows_json(self._table_id, [row])
            if errors:
                logger.warning("audit_bq_write_failed", errors=errors)
        except Exception as e:
            logger.warning("audit_bq_write_failed", error=str(e))

    def _ensure_audit_table(self) -> None:
        """Create audit dataset and table if they don't exist."""
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
                logger.info("audit_dataset_created", dataset=dataset_id)

            schema = [
                bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("user_name", "STRING"),
                bigquery.SchemaField("user_email", "STRING"),
                bigquery.SchemaField("user_domain", "STRING"),
                bigquery.SchemaField("hostname", "STRING"),
                bigquery.SchemaField("session_id", "STRING"),
                bigquery.SchemaField("query_text", "STRING"),
                bigquery.SchemaField("matched_metric", "STRING"),
                bigquery.SchemaField("generated_sql", "STRING"),
                bigquery.SchemaField("tables_accessed", "STRING", mode="REPEATED"),
                bigquery.SchemaField("rows_returned", "INTEGER"),
                bigquery.SchemaField("execution_ms", "INTEGER"),
                bigquery.SchemaField("cost_bytes", "INTEGER"),
                bigquery.SchemaField("cost_usd", "FLOAT"),
                bigquery.SchemaField("result_cached", "BOOLEAN"),
                bigquery.SchemaField("error_type", "STRING"),
                bigquery.SchemaField("error_message", "STRING"),
                bigquery.SchemaField("domain", "STRING"),
            ]
            table = bigquery.Table(self._table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp",
            )
            self._bq_client.create_table(table, exists_ok=True)

            # Migrate existing tables: add missing columns
            try:
                table_ref = self._bq_client.get_table(self._table_id)
                existing_fields = {f.name for f in table_ref.schema}
                new_fields = []
                for col_name in ("domain", "user_email", "user_domain"):
                    if col_name not in existing_fields:
                        new_fields.append(bigquery.SchemaField(col_name, "STRING"))
                if new_fields:
                    table_ref.schema = list(table_ref.schema) + new_fields
                    self._bq_client.update_table(table_ref, ["schema"])
                    logger.info(
                        "audit_table_migrated",
                        added_columns=[f.name for f in new_fields],
                    )
            except Exception as e:
                logger.warning("audit_table_migration_skipped", error=str(e))

            self._table_exists = True
            logger.info("audit_table_ready", table=self._table_id)
        except Exception as e:
            self._table_exists = False
            logger.warning("audit_table_setup_failed", error=str(e))

    def get_local_entries(self, since: datetime | None = None) -> list[AuditLogEntry]:
        """Read entries from local log file, optionally filtered by date."""
        if not _LOCAL_LOG_FILE.exists():
            return []
        entries = []
        for line in _LOCAL_LOG_FILE.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            entry = AuditLogEntry.model_validate_json(line)
            if since and entry.timestamp < since.replace(tzinfo=UTC):
                continue
            entries.append(entry)
        return entries

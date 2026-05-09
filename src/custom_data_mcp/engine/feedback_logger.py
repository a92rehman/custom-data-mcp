"""Feedback logger — writes to BigQuery with local JSON Lines fallback."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from custom_data_mcp.models.feedback import FeedbackEntry

if TYPE_CHECKING:
    from google.cloud import bigquery

logger = structlog.get_logger()

_LOCAL_LOG_DIR = Path.home() / ".claude" / "custom-data-logs"
_LOCAL_LOG_FILE = _LOCAL_LOG_DIR / "feedback.jsonl"


class FeedbackLogger:
    """Creates feedback entries and persists them to BigQuery + local file."""

    def __init__(
        self,
        bq_client: bigquery.Client | None = None,
        project: str = "",
        audit_dataset: str = "mcp_audit",
        feedback_table: str = "query_feedback",
        user_name: str = "unknown",
    ) -> None:
        self._bq_client = bq_client
        self._table_id = f"{project}.{audit_dataset}.{feedback_table}" if project else ""
        self._user_name = user_name
        self._table_exists: bool | None = None

    def log(
        self,
        event_id: str,
        rating: str,
        comment: str | None = None,
    ) -> FeedbackEntry:
        """Create a feedback entry and persist it."""
        entry = FeedbackEntry(
            event_id=event_id,
            user_name=self._user_name,
            rating=rating,
            comment=comment,
        )

        self._write_local(entry)

        if self._bq_client and self._table_id:
            self._write_bigquery(entry)

        logger.info(
            "feedback_logged",
            feedback_id=entry.feedback_id,
            event_id=entry.event_id,
            rating=entry.rating,
        )
        return entry

    def _write_local(self, entry: FeedbackEntry) -> None:
        """Append entry to local JSON Lines file."""
        try:
            _LOCAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
            with _LOCAL_LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.warning("feedback_local_write_failed", error=str(e))

    def _write_bigquery(self, entry: FeedbackEntry) -> None:
        """Insert entry into BigQuery feedback table."""
        try:
            if self._table_exists is None:
                self._ensure_feedback_table()

            row = entry.model_dump()
            row["timestamp"] = row["timestamp"].isoformat()
            errors = self._bq_client.insert_rows_json(self._table_id, [row])
            if errors:
                logger.warning("feedback_bq_write_failed", errors=errors)
        except Exception as e:
            logger.warning("feedback_bq_write_failed", error=str(e))

    def _ensure_feedback_table(self) -> None:
        """Create feedback dataset and table if they don't exist."""
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
                bigquery.SchemaField("feedback_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_name", "STRING"),
                bigquery.SchemaField("rating", "STRING"),
                bigquery.SchemaField("comment", "STRING"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            ]
            table = bigquery.Table(self._table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp",
            )
            self._bq_client.create_table(table, exists_ok=True)
            self._table_exists = True
            logger.info("feedback_table_ready", table=self._table_id)
        except Exception as e:
            self._table_exists = False
            logger.warning("feedback_table_setup_failed", error=str(e))

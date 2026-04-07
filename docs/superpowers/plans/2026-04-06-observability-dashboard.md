# Observability Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a feedback system, domain tagging, and Streamlit dashboard to track MCP adoption, quality, and cost.

**Architecture:** New `submit_feedback` MCP tool writes to `mcp_audit.query_feedback`. Domain classifier tags each audit entry. Streamlit dashboard reads both audit tables and renders 5 pages (Overview, Feedback, Cost, Errors, Freshness). Deployed on Railway.

**Tech Stack:** Python 3.11+, Streamlit, Plotly, Pandas, Google BigQuery, Pydantic

**Spec:** `docs/superpowers/specs/2026-04-06-observability-dashboard-design.md`

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `src/taleemabad_data_mcp/models/feedback.py` | `FeedbackEntry` Pydantic model |
| `src/taleemabad_data_mcp/engine/feedback_logger.py` | BigQuery + local JSONL writer for feedback |
| `src/taleemabad_data_mcp/engine/domain_classifier.py` | `classify_domain()` — maps tables/SQL to domain |
| `tests/test_feedback_model.py` | FeedbackEntry validation tests |
| `tests/test_feedback_logger.py` | FeedbackLogger write tests |
| `tests/test_domain_classifier.py` | Domain classification tests |
| `src/taleemabad_data_mcp/dashboard/__init__.py` | Package marker |
| `src/taleemabad_data_mcp/dashboard/app.py` | Streamlit entry point + auth gate |
| `src/taleemabad_data_mcp/dashboard/data/__init__.py` | Package marker |
| `src/taleemabad_data_mcp/dashboard/data/client.py` | BigQuery client for dashboard |
| `src/taleemabad_data_mcp/dashboard/data/queries.py` | All dashboard SQL queries |
| `src/taleemabad_data_mcp/dashboard/components/__init__.py` | Package marker |
| `src/taleemabad_data_mcp/dashboard/components/filters.py` | Shared sidebar filters |
| `src/taleemabad_data_mcp/dashboard/components/charts.py` | Reusable chart helpers |
| `src/taleemabad_data_mcp/dashboard/pages/1_overview.py` | Overview page |
| `src/taleemabad_data_mcp/dashboard/pages/2_feedback.py` | Expectation vs Reality page |
| `src/taleemabad_data_mcp/dashboard/pages/3_cost.py` | Cost tracking page |
| `src/taleemabad_data_mcp/dashboard/pages/4_errors.py` | Errors & governance gaps page |
| `src/taleemabad_data_mcp/dashboard/pages/5_freshness.py` | Data freshness page |
| `src/taleemabad_data_mcp/dashboard/.streamlit/config.toml` | Streamlit theme config |
| `Procfile` | Railway deployment |

### Modified Files
| File | Change |
|------|--------|
| `src/taleemabad_data_mcp/models/__init__.py` | Export `FeedbackEntry` |
| `src/taleemabad_data_mcp/models/audit.py` | Add `domain` field |
| `src/taleemabad_data_mcp/engine/audit_logger.py` | Add `domain` column to BQ schema + ALTER TABLE migration |
| `src/taleemabad_data_mcp/server.py` | Add `FeedbackLogger` to `AppContext`, init in lifespan, add `submit_feedback` tool, call `classify_domain()` before audit writes |
| `src/taleemabad_data_mcp/cli.py` | Add `dashboard` subcommand |
| `pyproject.toml` | Add `[dashboard]` optional deps |

---

## Task 1: FeedbackEntry Model

**Files:**
- Create: `src/taleemabad_data_mcp/models/feedback.py`
- Create: `tests/test_feedback_model.py`
- Modify: `src/taleemabad_data_mcp/models/__init__.py`

- [ ] **Step 1: Write failing tests for FeedbackEntry**

```python
# tests/test_feedback_model.py
"""Tests for FeedbackEntry model."""

from taleemabad_data_mcp.models.feedback import FeedbackEntry


def test_feedback_entry_defaults():
    entry = FeedbackEntry(event_id="abc-123", rating="up")
    assert entry.feedback_id is not None
    assert entry.timestamp is not None
    assert entry.event_id == "abc-123"
    assert entry.rating == "up"
    assert entry.comment is None
    assert entry.user_name == "unknown"


def test_feedback_entry_with_comment():
    entry = FeedbackEntry(
        event_id="abc-123",
        rating="down",
        comment="Wrong number, expected 150",
        user_name="Abdur-Rehman",
    )
    assert entry.rating == "down"
    assert entry.comment == "Wrong number, expected 150"
    assert entry.user_name == "Abdur-Rehman"


def test_feedback_entry_invalid_rating():
    import pytest
    with pytest.raises(Exception):
        FeedbackEntry(event_id="abc-123", rating="maybe")


def test_feedback_entry_serialization():
    entry = FeedbackEntry(event_id="abc-123", rating="up")
    data = entry.model_dump()
    assert "feedback_id" in data
    assert "timestamp" in data
    assert data["rating"] == "up"

    json_str = entry.model_dump_json()
    assert "abc-123" in json_str
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_feedback_model.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement FeedbackEntry model**

```python
# src/taleemabad_data_mcp/models/feedback.py
"""Feedback entry model."""

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackEntry(BaseModel):
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_name: str = "unknown"
    rating: Literal["up", "down"]
    comment: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

- [ ] **Step 4: Update models __init__.py**

Add to `src/taleemabad_data_mcp/models/__init__.py`:
```python
from taleemabad_data_mcp.models.feedback import FeedbackEntry

__all__ = [
    "AuditLogEntry",
    "FeedbackEntry",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_feedback_model.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/taleemabad_data_mcp/models/feedback.py src/taleemabad_data_mcp/models/__init__.py tests/test_feedback_model.py
git commit -m "feat: add FeedbackEntry model for user satisfaction tracking"
```

---

## Task 2: Domain Classifier

**Files:**
- Create: `src/taleemabad_data_mcp/engine/domain_classifier.py`
- Create: `tests/test_domain_classifier.py`

- [ ] **Step 1: Write failing tests for classify_domain**

```python
# tests/test_domain_classifier.py
"""Tests for domain classification."""

from taleemabad_data_mcp.engine.domain_classifier import classify_domain


def test_observations_domain():
    assert classify_domain(["coaching_observation", "coaching_teachervisit"]) == "observations"


def test_observations_single_table():
    assert classify_domain(["coaching_observationanswer"]) == "observations"


def test_lesson_plans_domain():
    assert classify_domain(["events_partitioned", "lp_info_all_types"]) == "lesson_plans"


def test_lesson_plans_timetable():
    assert classify_domain(["schoolclasstimetable", "schools_schoolclass"]) == "lesson_plans"


def test_training_domain():
    assert classify_domain(["teacher_training_level", "user_school_profiles"]) == "training"


def test_training_assessment():
    assert classify_domain(["teacher_training_assessment"]) == "training"


def test_teachers_domain():
    assert classify_domain(["users_teacherprofile", "schools_school"]) == "teachers"


def test_teachers_user_school_profiles_only():
    # user_school_profiles alone → teachers (not training, since no training tables)
    assert classify_domain(["user_school_profiles"]) == "teachers"


def test_other_domain():
    assert classify_domain(["some_random_table"]) == "other"


def test_empty_tables():
    assert classify_domain([]) == "other"


def test_sql_fallback_observations():
    assert classify_domain([], sql="SELECT * FROM coaching_observation WHERE ...") == "observations"


def test_sql_fallback_lesson_plans():
    assert classify_domain([], sql="SELECT * FROM lp_info_all_types") == "lesson_plans"


def test_sql_fallback_training():
    assert classify_domain([], sql="SELECT * FROM teacher_training_level") == "training"


def test_sql_fallback_teachers():
    assert classify_domain([], sql="SELECT * FROM users_teacherprofile") == "teachers"


def test_sql_fallback_empty():
    assert classify_domain([], sql="") == "other"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_domain_classifier.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement domain classifier**

```python
# src/taleemabad_data_mcp/engine/domain_classifier.py
"""Classify audit entries by data domain based on tables accessed or SQL text."""

_DOMAIN_KEYWORDS: list[tuple[str, list[str]]] = [
    ("observations", [
        "coaching_observation",
        "coaching_teachervisit",
        "coaching_observationanswer",
        "coaching_observationquestion",
        "coaching_questionoption",
        "coaching_observationquestiongroup",
        "coaching_observationsection",
        "coaching_observationtemplate",
    ]),
    ("training", [
        "teacher_training_level",
        "teacher_training_assessment",
    ]),
    ("lesson_plans", [
        "lp_info_all_types",
        "schoolclasstimetable",
        "schools_schoolclasssubject",
        "schools_schoolclass",
    ]),
    ("teachers", [
        "users_teacherprofile",
        "user_school_profiles",
        "teacher_profiles",
        "users_coachprofile",
        "users_principalprofile",
    ]),
]


def classify_domain(tables_accessed: list[str], sql: str = "") -> str:
    """Classify which data domain a query belongs to.

    Primary: matches table names from BigQuery job metadata.
    Fallback: keyword-matches against the SQL string when tables_accessed is empty.

    Args:
        tables_accessed: List of table IDs from BigQuery referenced_tables.
        sql: Raw SQL string, used as fallback when tables_accessed is empty.

    Returns:
        One of: "observations", "lesson_plans", "training", "teachers", "other".
    """
    search_text = " ".join(tables_accessed).lower()

    if not search_text and sql:
        search_text = sql.lower()

    if not search_text:
        return "other"

    for domain, keywords in _DOMAIN_KEYWORDS:
        if any(kw in search_text for kw in keywords):
            return domain

    return "other"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_domain_classifier.py -v`
Expected: All 15 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/engine/domain_classifier.py tests/test_domain_classifier.py
git commit -m "feat: add domain classifier for audit entry tagging"
```

---

## Task 3: Add Domain Field to AuditLogEntry + Schema Migration

**Files:**
- Modify: `src/taleemabad_data_mcp/models/audit.py`
- Modify: `src/taleemabad_data_mcp/engine/audit_logger.py`

- [ ] **Step 1: Add domain field to AuditLogEntry**

In `src/taleemabad_data_mcp/models/audit.py`, add after `error_message` field (line 25):
```python
    domain: str = "other"
```

- [ ] **Step 2: Add domain to AuditLogger.log() parameters**

In `src/taleemabad_data_mcp/engine/audit_logger.py`, add `domain: str = "other"` parameter to the `log()` method signature (after `error_message` param), and pass it to `AuditLogEntry(...)`:
```python
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
    ) -> AuditLogEntry:
```
And add `domain=domain` in the `AuditLogEntry(...)` constructor call.

- [ ] **Step 3: Add domain column to BigQuery schema**

In `_ensure_audit_table()` in `audit_logger.py`, add to the `schema` list (after `error_message` field):
```python
                bigquery.SchemaField("domain", "STRING"),
```

- [ ] **Step 4: Add ALTER TABLE migration for existing tables**

In `_ensure_audit_table()` in `audit_logger.py`, after the `create_table` call and before `self._table_exists = True`, add:
```python
            # Migrate existing tables: add domain column if missing
            try:
                table_ref = self._bq_client.get_table(self._table_id)
                existing_fields = {f.name for f in table_ref.schema}
                if "domain" not in existing_fields:
                    new_schema = list(table_ref.schema) + [
                        bigquery.SchemaField("domain", "STRING"),
                    ]
                    table_ref.schema = new_schema
                    self._bq_client.update_table(table_ref, ["schema"])
                    logger.info("audit_table_migrated", added_column="domain")
            except Exception as e:
                logger.warning("audit_table_migration_skipped", error=str(e))
```

- [ ] **Step 5: Add test for domain field**

Add to `tests/test_audit_logger.py`:
```python
def test_log_with_domain(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_FILE",
        tmp_path / "activity.jsonl",
    )
    logger = AuditLogger()
    entry = logger.log(query_text="observation query", domain="observations")
    assert entry.domain == "observations"


def test_log_domain_defaults_to_other(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_FILE",
        tmp_path / "activity.jsonl",
    )
    logger = AuditLogger()
    entry = logger.log(query_text="some query")
    assert entry.domain == "other"
```

- [ ] **Step 6: Run all audit tests**

Run: `uv run pytest tests/test_audit_logger.py -v`
Expected: All 6 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/taleemabad_data_mcp/models/audit.py src/taleemabad_data_mcp/engine/audit_logger.py
git commit -m "feat: add domain field to audit model + schema migration"
```

---

## Task 4: FeedbackLogger

**Files:**
- Create: `src/taleemabad_data_mcp/engine/feedback_logger.py`
- Create: `tests/test_feedback_logger.py`

- [ ] **Step 1: Write failing tests for FeedbackLogger**

```python
# tests/test_feedback_logger.py
"""Tests for feedback logging."""

from taleemabad_data_mcp.engine.feedback_logger import FeedbackLogger


def test_log_feedback_creates_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.feedback_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.feedback_logger._LOCAL_LOG_FILE",
        tmp_path / "feedback.jsonl",
    )
    fb_logger = FeedbackLogger(user_name="test-user")
    entry = fb_logger.log(event_id="evt-123", rating="up")
    assert entry.feedback_id is not None
    assert entry.event_id == "evt-123"
    assert entry.rating == "up"
    assert entry.user_name == "test-user"


def test_log_feedback_with_comment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.feedback_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.feedback_logger._LOCAL_LOG_FILE",
        tmp_path / "feedback.jsonl",
    )
    fb_logger = FeedbackLogger(user_name="test-user")
    entry = fb_logger.log(event_id="evt-456", rating="down", comment="Wrong number")
    assert entry.comment == "Wrong number"
    assert entry.rating == "down"


def test_log_feedback_writes_local_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.feedback_logger._LOCAL_LOG_DIR", tmp_path
    )
    log_file = tmp_path / "feedback.jsonl"
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.feedback_logger._LOCAL_LOG_FILE", log_file
    )
    fb_logger = FeedbackLogger()
    fb_logger.log(event_id="evt-1", rating="up")
    fb_logger.log(event_id="evt-2", rating="down", comment="bad data")
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_feedback_logger.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement FeedbackLogger**

```python
# src/taleemabad_data_mcp/engine/feedback_logger.py
"""Feedback logger — writes to BigQuery with local JSON Lines fallback."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from taleemabad_data_mcp.models.feedback import FeedbackEntry

if TYPE_CHECKING:
    from google.cloud import bigquery

logger = structlog.get_logger()

_LOCAL_LOG_DIR = Path.home() / ".claude" / "taleemabad-logs"
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_feedback_logger.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/engine/feedback_logger.py tests/test_feedback_logger.py
git commit -m "feat: add FeedbackLogger with BigQuery + local fallback"
```

---

## Task 5: Wire Feedback + Domain Into MCP Server

**Files:**
- Modify: `src/taleemabad_data_mcp/server.py`

- [ ] **Step 1: Add imports**

At the top of `server.py`, add:
```python
from taleemabad_data_mcp.engine.domain_classifier import classify_domain
from taleemabad_data_mcp.engine.feedback_logger import FeedbackLogger
```

- [ ] **Step 2: Add FeedbackLogger to AppContext**

In the `AppContext` dataclass, add:
```python
    feedback_logger: FeedbackLogger
```

- [ ] **Step 3: Initialize FeedbackLogger in app_lifespan**

After the `cost_estimator` initialization (line 51), add:
```python
    feedback_logger = FeedbackLogger(
        bq_client=bq_client,
        project=config.bigquery_project,
        audit_dataset=config.audit_dataset,
        feedback_table="query_feedback",
        user_name=config.taleemabad_user,
    )
```

And add `feedback_logger=feedback_logger` to the `yield AppContext(...)` call.

- [ ] **Step 4: Add domain tagging to execute_query**

In `execute_query`, after the successful query audit log (the `audit.log(...)` call around line 121), replace the `audit.log(...)` call to include domain:
```python
        tables = list({ref.table_id for ref in query_job.referenced_tables})
        domain = classify_domain(tables, sql)

        audit.log(
            query_text=question or sql,
            generated_sql=sql,
            tables_accessed=tables,
            rows_returned=len(rows),
            execution_ms=int(
                (query_job.ended - query_job.started).total_seconds() * 1000
            ) if query_job.ended and query_job.started else None,
            cost_bytes=bytes_billed,
            cost_usd=cost_usd,
            domain=domain,
        )
```

For the error path audit log (around line 139), add domain from SQL fallback:
```python
        audit.log(
            query_text=question or sql,
            generated_sql=sql,
            error_type=type(e).__name__,
            error_message=str(e),
            domain=classify_domain([], sql),
        )
```

For the dry_run audit log (around line 98), add domain from SQL fallback:
```python
        audit.log(
            query_text=question or sql,
            generated_sql=sql,
            result_cached=False,
            error_type="dry_run",
            domain=classify_domain([], sql),
        )
```

- [ ] **Step 5: Add submit_feedback tool**

Add after the `get_table_schema` tool at the end of `server.py`:
```python
@mcp.tool()
async def submit_feedback(
    event_id: str,
    rating: str,
    comment: str = "",
) -> str:
    """Submit optional feedback on a query result.

    Call this ONLY when the user voluntarily expresses satisfaction or
    dissatisfaction with a query result. Never prompt for feedback —
    it must be organic and non-intrusive.

    Args:
        event_id: The event_id from the audit log entry of the query being rated.
        rating: "up" if the result met expectations, "down" if it did not.
        comment: Optional free-text feedback from the user.
    """
    if rating not in ("up", "down"):
        return f"Invalid rating '{rating}'. Must be 'up' or 'down'."

    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    entry = app.feedback_logger.log(
        event_id=event_id,
        rating=rating,
        comment=comment or None,
    )

    return f"Feedback recorded (id: {entry.feedback_id}). Thank you."
```

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 7: Run linter**

Run: `uv run ruff check src/ tests/`
Expected: No errors (fix any that appear)

- [ ] **Step 8: Commit**

```bash
git add src/taleemabad_data_mcp/server.py
git commit -m "feat: wire feedback tool + domain tagging into MCP server"
```

---

## Task 6: Add Dashboard CLI Subcommand + pyproject.toml

**Files:**
- Modify: `src/taleemabad_data_mcp/cli.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add dashboard optional dependencies to pyproject.toml**

Add after the `dev` optional dependencies block:
```toml
dashboard = [
    "streamlit>=1.30",
    "plotly>=5.18",
    "pandas>=2.0",
]
```

- [ ] **Step 2: Add dashboard subcommand to cli.py**

Add after the `serve` command at the end of `cli.py`:
```python
@main.command()
def dashboard() -> None:
    """Launch the observability dashboard (Streamlit)."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        click.echo(
            "Streamlit is not installed. Install dashboard dependencies:\n"
            '  pip install "taleemabad-data-mcp[dashboard]"',
            err=True,
        )
        sys.exit(1)

    import subprocess as sp

    dashboard_app = Path(__file__).parent / "dashboard" / "app.py"
    if not dashboard_app.exists():
        click.echo(f"Dashboard app not found at {dashboard_app}", err=True)
        sys.exit(1)

    sp.run(["streamlit", "run", str(dashboard_app)], check=False)
```

- [ ] **Step 3: Run existing CLI tests**

Run: `uv run pytest tests/test_cli.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml src/taleemabad_data_mcp/cli.py
git commit -m "feat: add dashboard CLI subcommand + optional dependencies"
```

---

## Task 7: Dashboard Data Layer

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/__init__.py`
- Create: `src/taleemabad_data_mcp/dashboard/data/__init__.py`
- Create: `src/taleemabad_data_mcp/dashboard/data/client.py`
- Create: `src/taleemabad_data_mcp/dashboard/data/queries.py`

- [ ] **Step 1: Create package markers**

Create empty `src/taleemabad_data_mcp/dashboard/__init__.py` and `src/taleemabad_data_mcp/dashboard/data/__init__.py`.

- [ ] **Step 2: Implement BigQuery client for dashboard**

```python
# src/taleemabad_data_mcp/dashboard/data/client.py
"""BigQuery client for the dashboard."""

import base64
import json
import os
import tempfile

import streamlit as st
from google.cloud import bigquery


@st.cache_resource
def get_bq_client() -> bigquery.Client:
    """Create a BigQuery client, cached for the Streamlit session.

    Supports two credential modes:
    - GOOGLE_APPLICATION_CREDENTIALS_BASE64: base64-encoded JSON key (Railway)
    - GOOGLE_APPLICATION_CREDENTIALS: path to JSON key file (local dev)
    """
    project = os.environ.get("BIGQUERY_PROJECT", "niete-bq-prod")

    b64_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
    if b64_creds:
        creds_json = base64.b64decode(b64_creds).decode("utf-8")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(creds_json)
            temp_path = f.name
        return bigquery.Client.from_service_account_json(temp_path, project=project)

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        return bigquery.Client.from_service_account_json(creds_path, project=project)

    # Try loading from saved env file (local dev)
    env_file = os.path.expanduser("~/.claude/taleemabad-data-mcp.env")
    if os.path.exists(env_file):
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    env_vars[k] = v
        creds = env_vars.get("GOOGLE_APPLICATION_CREDENTIALS")
        if creds:
            return bigquery.Client.from_service_account_json(creds, project=project)

    return bigquery.Client(project=project)


def get_config() -> dict:
    """Get dashboard configuration from environment."""
    return {
        "project": os.environ.get("BIGQUERY_PROJECT", "niete-bq-prod"),
        "audit_dataset": os.environ.get("AUDIT_DATASET", "mcp_audit"),
        "audit_table": os.environ.get("AUDIT_TABLE", "activity_log"),
        "feedback_table": os.environ.get("FEEDBACK_TABLE", "query_feedback"),
    }
```

- [ ] **Step 3: Implement dashboard queries**

```python
# src/taleemabad_data_mcp/dashboard/data/queries.py
"""All BigQuery SQL queries used by the dashboard."""

import pandas as pd
import streamlit as st
from google.cloud import bigquery

from taleemabad_data_mcp.dashboard.data.client import get_bq_client, get_config


def _full_table(table_key: str) -> str:
    """Build fully qualified table name."""
    cfg = get_config()
    table_name = cfg[table_key] if table_key in cfg else table_key
    return f"`{cfg['project']}.{cfg['audit_dataset']}.{table_name}`"


@st.cache_data(ttl=300)
def get_activity_log(
    days: int = 30,
    users: list[str] | None = None,
    domains: list[str] | None = None,
) -> pd.DataFrame:
    """Fetch audit log entries for the given time window."""
    client = get_bq_client()
    table = _full_table("audit_table")

    where = [f"timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)"]
    if users:
        user_list = ", ".join(f"'{u}'" for u in users)
        where.append(f"user_name IN ({user_list})")
    if domains:
        domain_list = ", ".join(f"'{d}'" for d in domains)
        where.append(f"IFNULL(domain, 'other') IN ({domain_list})")

    sql = f"""
        SELECT
            event_id, timestamp, user_name, query_text, generated_sql,
            tables_accessed, rows_returned, execution_ms,
            cost_bytes, cost_usd, result_cached,
            error_type, error_message, IFNULL(domain, 'other') AS domain
        FROM {table}
        WHERE {' AND '.join(where)}
        ORDER BY timestamp DESC
    """
    return client.query(sql).to_dataframe()


@st.cache_data(ttl=300)
def get_feedback(days: int = 30) -> pd.DataFrame:
    """Fetch feedback entries for the given time window."""
    client = get_bq_client()
    table = _full_table("feedback_table")
    audit_table = _full_table("audit_table")

    sql = f"""
        SELECT
            f.feedback_id, f.event_id, f.user_name, f.rating, f.comment, f.timestamp,
            a.query_text, a.generated_sql, IFNULL(a.domain, 'other') AS domain
        FROM {table} f
        LEFT JOIN {audit_table} a ON f.event_id = a.event_id
        WHERE f.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY f.timestamp DESC
    """
    return client.query(sql).to_dataframe()


@st.cache_data(ttl=300)
def get_distinct_users(days: int = 90) -> list[str]:
    """Get distinct user names from recent activity."""
    client = get_bq_client()
    table = _full_table("audit_table")
    sql = f"""
        SELECT DISTINCT user_name
        FROM {table}
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY user_name
    """
    df = client.query(sql).to_dataframe()
    return df["user_name"].tolist() if not df.empty else []


@st.cache_data(ttl=300)
def get_distinct_domains(days: int = 90) -> list[str]:
    """Get distinct domains from recent activity."""
    client = get_bq_client()
    table = _full_table("audit_table")
    sql = f"""
        SELECT DISTINCT IFNULL(domain, 'other') AS domain
        FROM {table}
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY domain
    """
    df = client.query(sql).to_dataframe()
    return df["domain"].tolist() if not df.empty else []


@st.cache_data(ttl=300)
def get_table_freshness() -> pd.DataFrame:
    """Get freshness for key tables from INFORMATION_SCHEMA."""
    client = get_bq_client()
    cfg = get_config()

    key_tables = [
        "user_school_profiles", "events_partitioned", "coaching_observation",
        "teacher_training_level", "teacher_training_assessment",
        "lp_info_all_types", "FDE_Schools",
    ]
    table_list = ", ".join(f"'{t}'" for t in key_tables)

    sql = f"""
        SELECT
            table_name,
            MAX(last_modified_time) AS last_modified
        FROM `{cfg['project']}.tbproddb.INFORMATION_SCHEMA.PARTITIONS`
        WHERE table_name IN ({table_list})
          AND partition_id != '__NULL__'
        GROUP BY table_name
    """
    return client.query(sql).to_dataframe()
```

- [ ] **Step 4: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/__init__.py dashboard/data/__init__.py dashboard/data/client.py dashboard/data/queries.py
git commit -m "feat: add dashboard data layer (BigQuery client + queries)"
```

---

## Task 8: Dashboard Shared Components

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/components/__init__.py`
- Create: `src/taleemabad_data_mcp/dashboard/components/filters.py`
- Create: `src/taleemabad_data_mcp/dashboard/components/charts.py`

- [ ] **Step 1: Create package marker**

Create empty `src/taleemabad_data_mcp/dashboard/components/__init__.py`.

- [ ] **Step 2: Implement shared sidebar filters**

```python
# src/taleemabad_data_mcp/dashboard/components/filters.py
"""Shared sidebar filters for all dashboard pages."""

from datetime import datetime, timedelta

import streamlit as st

from taleemabad_data_mcp.dashboard.data.queries import get_distinct_domains, get_distinct_users


def render_sidebar_filters() -> dict:
    """Render sidebar filters and return selected values.

    Returns:
        dict with keys: days, users, domains
    """
    st.sidebar.header("Filters")

    days = st.sidebar.selectbox(
        "Time range",
        options=[7, 14, 30, 60, 90],
        index=2,
        format_func=lambda x: f"Last {x} days",
    )

    available_users = get_distinct_users(days=90)
    users = st.sidebar.multiselect("Users", options=available_users)

    available_domains = get_distinct_domains(days=90)
    if not available_domains:
        available_domains = ["teachers", "lesson_plans", "observations", "training", "other"]
    domains = st.sidebar.multiselect("Domains", options=available_domains)

    return {
        "days": days,
        "users": users or None,
        "domains": domains or None,
    }
```

- [ ] **Step 3: Implement reusable chart helpers**

```python
# src/taleemabad_data_mcp/dashboard/components/charts.py
"""Reusable chart helpers for dashboard pages."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def kpi_card(label: str, value: str | int | float, delta: str | None = None) -> None:
    """Render a KPI metric card using Streamlit's metric component."""
    import streamlit as st
    st.metric(label=label, value=value, delta=delta)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
) -> go.Figure:
    """Create a Plotly line chart."""
    fig = px.line(df, x=x, y=y, title=title, color=color)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
    barmode: str = "group",
) -> go.Figure:
    """Create a Plotly bar chart."""
    fig = px.bar(df, x=x, y=y, title=title, color=color, barmode=barmode)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def stacked_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
) -> go.Figure:
    """Create a Plotly stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title, barmode="stack")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def freshness_color(hours_ago: float) -> str:
    """Return color indicator based on staleness hours."""
    if hours_ago < 6:
        return "🟢"
    elif hours_ago < 24:
        return "🟡"
    return "🔴"
```

- [ ] **Step 4: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/components/__init__.py dashboard/components/filters.py dashboard/components/charts.py
git commit -m "feat: add dashboard shared components (filters + charts)"
```

---

## Task 9: Dashboard App Entry Point + Auth

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/app.py`
- Create: `src/taleemabad_data_mcp/dashboard/.streamlit/config.toml`

- [ ] **Step 1: Create Streamlit config**

```toml
# src/taleemabad_data_mcp/dashboard/.streamlit/config.toml
[theme]
primaryColor = "#1B73E8"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
headless = true
```

- [ ] **Step 2: Implement app entry point with auth gate**

```python
# src/taleemabad_data_mcp/dashboard/app.py
"""Taleemabad Data MCP — Observability Dashboard."""

import os

import streamlit as st

st.set_page_config(
    page_title="Taleemabad MCP Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def check_password() -> bool:
    """Simple password gate. Returns True if authenticated."""
    password = os.environ.get("DASHBOARD_PASSWORD")
    if not password:
        return True  # No password set — open access

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("Taleemabad MCP Dashboard")
    entered = st.text_input("Password", type="password")
    if st.button("Login"):
        if entered == password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False


if not check_password():
    st.stop()

# Main landing page
st.title("📊 Taleemabad MCP — Observability Dashboard")
st.markdown(
    "Track adoption, quality, cost, and data freshness of the governed data layer."
)

st.markdown("### Navigate using the sidebar pages:")
st.markdown("""
- **Overview** — Active users, query volume, feedback summary
- **Feedback** — Expectation vs Reality deep dive
- **Cost** — BigQuery cost tracking
- **Errors** — Error rates, governance gaps
- **Freshness** — Data freshness status
""")
```

- [ ] **Step 3: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/app.py dashboard/.streamlit/config.toml
git commit -m "feat: add dashboard entry point with password auth gate"
```

---

## Task 10: Dashboard Pages — Overview

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/pages/1_overview.py`

- [ ] **Step 1: Implement Overview page**

```python
# src/taleemabad_data_mcp/dashboard/pages/1_overview.py
"""Overview page — active users, query volume, feedback summary."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card, line_chart, stacked_bar_chart
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log, get_feedback

st.header("Overview")

filters = render_sidebar_filters()
df = get_activity_log(**filters)
fb = get_feedback(days=filters["days"])

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card("Total Queries", len(df))

with col2:
    active_users = df["user_name"].nunique()
    kpi_card("Active Users", active_users)

with col3:
    if not fb.empty:
        up_count = (fb["rating"] == "up").sum()
        total_fb = len(fb)
        sat_rate = f"{up_count / total_fb * 100:.0f}%" if total_fb > 0 else "N/A"
    else:
        sat_rate = "N/A"
    kpi_card("Satisfaction Rate", sat_rate)

with col4:
    avg_cost = df["cost_usd"].mean() if "cost_usd" in df.columns else 0
    kpi_card("Avg Cost/Query", f"${avg_cost:.4f}")

st.divider()

# Daily Active Users
df["date"] = pd.to_datetime(df["timestamp"]).dt.date
dau = df.groupby("date")["user_name"].nunique().reset_index()
dau.columns = ["Date", "Active Users"]
st.plotly_chart(line_chart(dau, "Date", "Active Users", "Daily Active Users"), use_container_width=True)

# Query Volume by Domain
vol = df.groupby(["date", "domain"]).size().reset_index(name="Queries")
st.plotly_chart(
    stacked_bar_chart(vol, "date", "Queries", "domain", "Query Volume by Domain"),
    use_container_width=True,
)

# Feedback Score Trend
if not fb.empty:
    fb["date"] = pd.to_datetime(fb["timestamp"]).dt.date
    fb_daily = fb.groupby(["date", "rating"]).size().reset_index(name="Count")
    st.plotly_chart(
        bar_chart(fb_daily, "date", "Count", "Feedback Trend", color="rating"),
        use_container_width=True,
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/pages/1_overview.py
git commit -m "feat: add Overview dashboard page"
```

---

## Task 11: Dashboard Pages — Feedback

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/pages/2_feedback.py`

- [ ] **Step 1: Implement Feedback page**

```python
# src/taleemabad_data_mcp/dashboard/pages/2_feedback.py
"""Expectation vs Reality — feedback deep dive."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card, line_chart
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log, get_feedback

st.header("Expectation vs Reality")

filters = render_sidebar_filters()
fb = get_feedback(days=filters["days"])
activity = get_activity_log(**filters)

if fb.empty:
    st.info("No feedback data found. Feedback is collected when users voluntarily rate query results.")
    st.stop()

# Top-level stats
col1, col2, col3 = st.columns(3)

up_count = (fb["rating"] == "up").sum()
down_count = (fb["rating"] == "down").sum()
total_fb = len(fb)

with col1:
    kpi_card("👍 Thumbs Up", int(up_count))
with col2:
    kpi_card("👎 Thumbs Down", int(down_count))
with col3:
    total_queries = len(activity) if not activity.empty else 0
    unrated_pct = f"{(1 - total_fb / total_queries) * 100:.0f}%" if total_queries > 0 else "N/A"
    kpi_card("Unrated Queries", unrated_pct)

st.divider()

# Feedback timeline
fb["date"] = pd.to_datetime(fb["timestamp"]).dt.date
timeline = fb.groupby(["date", "rating"]).size().reset_index(name="Count")
st.plotly_chart(
    bar_chart(timeline, "date", "Count", "Feedback Over Time", color="rating"),
    use_container_width=True,
)

# Satisfaction by domain
if "domain" in fb.columns:
    domain_sat = fb.groupby(["domain", "rating"]).size().reset_index(name="Count")
    st.plotly_chart(
        bar_chart(domain_sat, "domain", "Count", "Satisfaction by Domain", color="rating"),
        use_container_width=True,
    )

# Satisfaction by user
user_sat = fb.groupby(["user_name", "rating"]).size().unstack(fill_value=0).reset_index()
st.subheader("Satisfaction by User")
st.dataframe(user_sat, use_container_width=True)

# Recent comments
comments = fb[fb["comment"].notna() & (fb["comment"] != "")]
if not comments.empty:
    st.subheader("Recent Comments")
    st.dataframe(
        comments[["timestamp", "user_name", "rating", "comment", "query_text"]].head(50),
        use_container_width=True,
    )
else:
    st.info("No comments yet.")
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/pages/2_feedback.py
git commit -m "feat: add Feedback dashboard page"
```

---

## Task 12: Dashboard Pages — Cost

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/pages/3_cost.py`

- [ ] **Step 1: Implement Cost page**

```python
# src/taleemabad_data_mcp/dashboard/pages/3_cost.py
"""Cost tracking — BigQuery spend analysis."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card, line_chart
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log

st.header("Cost Tracking")

filters = render_sidebar_filters()
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

# Exclude dry runs and errors for cost analysis
cost_df = df[df["cost_usd"].notna() & (df["cost_usd"] > 0)].copy()

# KPI Cards
col1, col2, col3 = st.columns(3)

with col1:
    total_cost = cost_df["cost_usd"].sum() if not cost_df.empty else 0
    kpi_card("Total Spend", f"${total_cost:.2f}")

with col2:
    total_bytes = cost_df["cost_bytes"].sum() if not cost_df.empty else 0
    gb = total_bytes / (1024 ** 3)
    kpi_card("Total Data Scanned", f"{gb:.1f} GB")

with col3:
    avg_cost = cost_df["cost_usd"].mean() if not cost_df.empty else 0
    kpi_card("Avg Cost/Query", f"${avg_cost:.4f}")

st.divider()

if cost_df.empty:
    st.info("No queries with cost data in this period.")
    st.stop()

# Spend over time
cost_df["date"] = pd.to_datetime(cost_df["timestamp"]).dt.date
daily_cost = cost_df.groupby("date")["cost_usd"].sum().reset_index()
daily_cost.columns = ["Date", "Cost (USD)"]
st.plotly_chart(line_chart(daily_cost, "Date", "Cost (USD)", "Daily Spend"), use_container_width=True)

# Cost by user
user_cost = cost_df.groupby("user_name")["cost_usd"].sum().reset_index().sort_values("cost_usd", ascending=False)
user_cost.columns = ["User", "Cost (USD)"]
st.plotly_chart(bar_chart(user_cost.head(10), "User", "Cost (USD)", "Top Spenders"), use_container_width=True)

# Cost by domain
domain_cost = cost_df.groupby("domain")["cost_usd"].sum().reset_index().sort_values("cost_usd", ascending=False)
domain_cost.columns = ["Domain", "Cost (USD)"]
st.plotly_chart(bar_chart(domain_cost, "Domain", "Cost (USD)", "Cost by Domain"), use_container_width=True)

# Large queries
large = cost_df.nlargest(10, "cost_bytes")
if not large.empty:
    st.subheader("Largest Queries")
    st.dataframe(
        large[["timestamp", "user_name", "domain", "cost_usd", "cost_bytes", "query_text"]],
        use_container_width=True,
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/pages/3_cost.py
git commit -m "feat: add Cost Tracking dashboard page"
```

---

## Task 13: Dashboard Pages — Errors

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/pages/4_errors.py`

- [ ] **Step 1: Implement Errors page**

```python
# src/taleemabad_data_mcp/dashboard/pages/4_errors.py
"""Errors & governance gaps."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import bar_chart, kpi_card, line_chart
from taleemabad_data_mcp.dashboard.components.filters import render_sidebar_filters
from taleemabad_data_mcp.dashboard.data.queries import get_activity_log

st.header("Errors & Governance Gaps")

filters = render_sidebar_filters()
df = get_activity_log(**filters)

if df.empty:
    st.info("No activity data found for the selected filters.")
    st.stop()

# Separate errors (exclude dry_run as it's not a real error)
errors = df[(df["error_type"].notna()) & (df["error_type"] != "dry_run")].copy()
total = len(df[df["error_type"] != "dry_run"])

# KPI Cards
col1, col2, col3 = st.columns(3)

with col1:
    kpi_card("Total Errors", len(errors))

with col2:
    error_rate = f"{len(errors) / total * 100:.1f}%" if total > 0 else "0%"
    kpi_card("Error Rate", error_rate)

with col3:
    unique_types = errors["error_type"].nunique() if not errors.empty else 0
    kpi_card("Error Types", unique_types)

st.divider()

if errors.empty:
    st.success("No errors in this period!")
    st.stop()

# Error rate over time
errors["date"] = pd.to_datetime(errors["timestamp"]).dt.date
daily_errors = errors.groupby("date").size().reset_index(name="Errors")
st.plotly_chart(line_chart(daily_errors, "date", "Errors", "Errors Over Time"), use_container_width=True)

# Errors by type
type_counts = errors.groupby("error_type").size().reset_index(name="Count").sort_values("Count", ascending=False)
st.plotly_chart(bar_chart(type_counts, "error_type", "Count", "Errors by Type"), use_container_width=True)

# Governance gaps (queries that mention "no governed query" or "NoMatchingMetric")
st.subheader("Governance Gaps")
gaps = errors[
    (errors["error_type"] == "NoMatchingMetric")
    | (errors["error_message"].str.contains("no governed", case=False, na=False))
]
if not gaps.empty:
    st.dataframe(
        gaps[["timestamp", "user_name", "query_text", "error_message"]].head(50),
        use_container_width=True,
    )
else:
    st.info("No governance gaps detected — all queries matched governed rules.")

# All errors detail
st.subheader("Error Details")
st.dataframe(
    errors[["timestamp", "user_name", "error_type", "error_message", "query_text"]].head(50),
    use_container_width=True,
)
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/pages/4_errors.py
git commit -m "feat: add Errors & Governance Gaps dashboard page"
```

---

## Task 14: Dashboard Pages — Freshness

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/pages/5_freshness.py`

- [ ] **Step 1: Implement Freshness page**

```python
# src/taleemabad_data_mcp/dashboard/pages/5_freshness.py
"""Data freshness status for key tables."""

from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.components.charts import freshness_color
from taleemabad_data_mcp.dashboard.data.queries import get_table_freshness

st.header("Data Freshness")

st.markdown("Freshness of key BigQuery tables used by governed metrics.")

try:
    df = get_table_freshness()

    if df.empty:
        st.warning("Could not retrieve freshness data. Check BigQuery permissions.")
        st.stop()

    now = datetime.now(UTC)
    df["hours_ago"] = df["last_modified"].apply(
        lambda ts: (now - ts.replace(tzinfo=UTC)).total_seconds() / 3600
        if pd.notna(ts) else None
    )
    df["status"] = df["hours_ago"].apply(
        lambda h: freshness_color(h) if pd.notna(h) else "⚪"
    )
    df["last_modified_str"] = df["last_modified"].apply(
        lambda ts: ts.strftime("%Y-%m-%d %H:%M UTC") if pd.notna(ts) else "Unknown"
    )
    df["hours_ago_str"] = df["hours_ago"].apply(
        lambda h: f"{h:.1f}h" if pd.notna(h) else "Unknown"
    )

    display = df[["status", "table_name", "last_modified_str", "hours_ago_str"]].copy()
    display.columns = ["Status", "Table", "Last Modified", "Age"]

    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("""
    **Legend:** 🟢 Fresh (<6h) | 🟡 Aging (6-24h) | 🔴 Stale (>24h) | ⚪ Unknown
    """)

except Exception as e:
    st.error(f"Error fetching freshness data: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/pages/5_freshness.py
git commit -m "feat: add Data Freshness dashboard page"
```

---

## Task 15: Procfile + Final Wiring

**Files:**
- Create: `Procfile`

- [ ] **Step 1: Create Procfile for Railway**

```
web: python -m streamlit run src/taleemabad_data_mcp/dashboard/app.py --server.port=$PORT --server.address=0.0.0.0
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 3: Run linter on all code**

Run: `uv run ruff check src/ tests/`
Expected: No errors (fix any that appear)

- [ ] **Step 4: Commit everything**

```bash
git add Procfile
git commit -m "feat: add Procfile for Railway deployment"
```

---

## Task 16: Final Integration Test

- [ ] **Step 1: Install dashboard dependencies locally**

Run: `uv pip install streamlit plotly pandas`

- [ ] **Step 2: Verify Streamlit starts**

Run: `streamlit run src/taleemabad_data_mcp/dashboard/app.py`
Expected: Browser opens, password gate shows (or landing page if no password set)

- [ ] **Step 3: Verify all pages load without errors**

Click through each page in the sidebar: Overview, Feedback, Cost, Errors, Freshness. Each should either show data or an informational message if no data exists yet.

- [ ] **Step 4: Verify MCP server still works**

Run: `uv run python -m taleemabad_data_mcp serve`
Expected: Server starts without errors

- [ ] **Step 5: Final commit with version bump**

Update `pyproject.toml` version from `"0.2.0"` to `"0.3.0"`.

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.3.0 for dashboard release"
```

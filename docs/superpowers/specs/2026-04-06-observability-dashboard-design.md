# Observability Dashboard — Design Spec

**Date:** 2026-04-06
**Status:** Approved
**Approach:** Monorepo (Streamlit dashboard inside taleemabad-data-mcp)

---

## 1. Problem

The MCP server executes governed queries and logs audit trails, but there is no way to:
- Know if answers meet user expectations
- Track who is using the system and how often
- Monitor query costs, errors, and governance gaps
- See data freshness at a glance

Leadership, data leads, and the MCP maintainer need a visual dashboard to track adoption, quality, and cost of the governed data layer.

## 2. Solution Overview

Three deliverables:

1. **Feedback system** — new MCP tool for optional thumbs up/down + comment, stored in BigQuery
2. **Domain tagging** — classify each audit entry by data domain at write time
3. **Streamlit dashboard** — 5-page web app reading from audit tables, deployed on Railway

## 3. Feedback System

### New MCP Tool

```
submit_feedback(
    event_id: str,        # links to the audit log entry
    rating: str,          # "up" or "down"
    comment: str = None   # optional open-ended text
)
```

**Behavior:**
- Called by Claude Code only when the user voluntarily gives feedback
- Never prompted, never mandatory — zero friction
- If the user says nothing and moves on, no feedback is recorded
- Returns a simple confirmation message
- `event_id` validation is best-effort — BigQuery has no FK constraints, and we do not query to verify the event exists before writing feedback. Invalid `event_id` values are accepted but will not join to any audit entry in the dashboard (orphaned feedback is harmless).

### Storage

**BigQuery table:** `mcp_audit.query_feedback` (partitioned daily on `timestamp`)

| Column | Type | Description |
|--------|------|-------------|
| `feedback_id` | STRING (UUID) | Primary key |
| `event_id` | STRING (UUID) | FK to `activity_log.event_id` |
| `user_name` | STRING | Who gave feedback |
| `rating` | STRING | `"up"` or `"down"` |
| `comment` | STRING (nullable) | Optional open-ended text |
| `timestamp` | TIMESTAMP | When feedback was submitted |

**Local fallback:** `~/.claude/taleemabad-logs/feedback.jsonl` — same pattern as audit logger. Best-effort, non-blocking writes.

### Feedback Logger

New class `FeedbackLogger` in `engine/feedback_logger.py`, following the same pattern as `AuditLogger`:
- Writes to BigQuery `mcp_audit.query_feedback`
- Falls back to local JSON Lines if BigQuery write fails
- Auto-creates table if missing
- Never blocks on write failure

### Feedback Model

New Pydantic model `FeedbackEntry` in `models/feedback.py`:
- `feedback_id: str` (UUID, auto-generated)
- `event_id: str` (required)
- `user_name: str`
- `rating: Literal["up", "down"]`
- `comment: Optional[str]`
- `timestamp: datetime` (UTC, auto-generated)

## 4. Domain Tagging

### Change to AuditLogEntry

Add `domain: str` field to `AuditLogEntry` model. Populated at write time by the MCP server before logging.

### Classification Rules

Domain is inferred from `tables_accessed` in the audit entry:

| Tables accessed contain | Domain |
|---|---|
| `coaching_observation`, `coaching_teachervisit`, `coaching_observationanswer` | `observations` |
| `events_partitioned` + LP events, `lp_info_all_types`, `schoolclasstimetable` | `lesson_plans` |
| `teacher_training_level`, `teacher_training_assessment` | `training` |
| `users_teacherprofile`, `user_school_profiles`, `teacher_profiles` | `teachers` |
| None of the above | `other` |

### Implementation

Utility function `classify_domain(tables_accessed: list[str], sql: str = "") -> str` in `engine/domain_classifier.py`. Called in `server.py` before writing the audit log entry.

**Primary:** Uses `tables_accessed` from BigQuery job metadata (available on successful queries).
**Fallback:** For dry runs and failed queries where `tables_accessed` is empty, uses simple keyword matching on the SQL string (e.g., `coaching_observation` in SQL → `observations`). This ensures domain tagging works for the majority of entries, not just successful executions.

### BigQuery Schema Change

Add `domain STRING` column to `mcp_audit.activity_log` table.

**Migration:** The `_ensure_audit_table` method in `audit_logger.py` uses `create_table(..., exists_ok=True)` which does not alter existing schemas. We must add an `ALTER TABLE` migration:

```sql
ALTER TABLE `mcp_audit.activity_log` ADD COLUMN IF NOT EXISTS domain STRING;
```

This runs once at startup in `_ensure_audit_table` after the `exists_ok` create. Existing rows will have `NULL` domain — dashboard treats `NULL` as `"other"`.

## 5. Dashboard Architecture

### Project Structure

```
src/taleemabad_data_mcp/dashboard/
  __init__.py
  app.py                  # Streamlit entry point
  pages/
    1_overview.py         # Active users, query volume, feedback summary
    2_feedback.py         # Expectation vs Reality deep dive
    3_cost.py             # BigQuery cost tracking
    4_errors.py           # Error rates, governance gaps
    5_freshness.py        # Data freshness status
  data/
    __init__.py
    queries.py            # All BigQuery SQL for dashboard metrics
    client.py             # BigQuery client setup
  components/
    __init__.py
    filters.py            # Shared sidebar filters (date range, user, domain)
    charts.py             # Reusable chart helpers
```

**Why inside the package:** The dashboard lives inside `src/taleemabad_data_mcp/` so it is included in the wheel and importable from installed packages. The CLI `dashboard` command and Railway Procfile both reference this path.

### Dependencies

Added as optional extras in `pyproject.toml`:

```toml
[project.optional-dependencies]
dashboard = ["streamlit>=1.30", "plotly>=5.18", "pandas>=2.0"]
```

Install: `pip install taleemabad-data-mcp[dashboard]`

### Data Source

Reads directly from:
- `mcp_audit.activity_log` — query audit entries
- `mcp_audit.query_feedback` — user feedback

No intermediate ETL. The audit tables are the dashboard's data source.

### Caching

Streamlit's `@st.cache_data(ttl=300)` — 5-minute TTL on all dashboard queries. No custom caching layer.

### BigQuery Client

`dashboard/data/client.py` creates a BigQuery client using:
- **Local:** reads from `~/.claude/taleemabad-data-mcp.env` (same as MCP server)
- **Railway:** reads `GOOGLE_APPLICATION_CREDENTIALS_BASE64` env var, decodes to temp file

## 6. Dashboard Pages

### Shared Sidebar Filters (all pages)

- **Date range picker** — default: last 30 days
- **User filter** — multi-select dropdown, populated from distinct `user_name` values
- **Domain filter** — multi-select: teachers, lesson_plans, observations, training, other

### Page 1: Overview

Top-line KPI cards:
- Total queries (period)
- Active users (unique `user_name` count)
- Satisfaction rate (thumbs up / total feedback %)
- Avg cost per query (USD)

Charts:
- **Daily active users** — line chart over time
- **Query volume by domain** — stacked bar chart over time
- **Feedback score trend** — thumbs up/down ratio over time

### Page 2: Expectation vs Reality

- **Feedback timeline** — thumbs up/down counts over time
- **Satisfaction by domain** — bar chart comparing up/down ratios per domain
- **Satisfaction by user** — table with per-user feedback stats
- **Recent comments** — table of open-ended feedback with columns: timestamp, user, rating, comment, original question
- **Unrated queries %** — gauge showing what fraction of queries received feedback (tracks feedback adoption)

### Page 3: Cost Tracking

- **Total spend** — line chart (daily/weekly/monthly toggle)
- **Cost by user** — bar chart of top spenders
- **Cost by domain** — pie/bar chart
- **Large query alerts** — table of queries exceeding confirmation threshold
- **Bytes processed trend** — line chart showing efficiency over time

### Page 4: Errors & Governance Gaps

- **Error rate** — line chart of failed queries over time
- **Errors by type** — bar chart (BadRequest, Forbidden, NotFound, InternalServerError)
- **Dead letter queue** — table of questions with no matching governance rule
- **Common error patterns** — grouped recurring failures
- ~~**Resolution rate**~~ — deferred to future phase (no `resolved` field in audit model yet)

### Page 5: Data Freshness

- **Table freshness status** — queries BigQuery `INFORMATION_SCHEMA.PARTITIONS` live for each key table, shows last modified time, color-coded: green (<6h), yellow (6-24h), red (>24h)
- ~~**Freshness trend**~~ — deferred to future phase (requires historical freshness snapshots not yet collected)
- ~~**Stale data warnings served**~~ — deferred to future phase (requires audit logging in `check_table_freshness` tool)

## 7. Deployment

### Railway

- **Service type:** Web (Streamlit)
- **Procfile:** `web: streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0`
- **Environment variables:**
  - `GOOGLE_APPLICATION_CREDENTIALS_BASE64` — base64-encoded service account JSON
  - `BIGQUERY_PROJECT` — `niete-bq-prod`
  - `AUDIT_DATASET` — `mcp_audit`
  - `AUDIT_TABLE` — `activity_log`
  - `DASHBOARD_PASSWORD` — simple password for access control

### Access Control

Simple password gate using `st.text_input(type="password")` check on app load. Password stored in `DASHBOARD_PASSWORD` env var. No role-based access — anyone with the password sees all data.

**Note:** This is not production-grade auth. The password is checked on every Streamlit rerun (Streamlit's execution model). Acceptable for an internal tool; upgrade to OAuth/SSO if the audience grows.

### Local Development

```bash
# From project root
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

CLI shortcut:
```bash
python -m taleemabad_data_mcp dashboard
```

Reads credentials from `~/.claude/taleemabad-data-mcp.env` automatically.

## 8. Changes to Existing Code

| File | Change |
|------|--------|
| `models/audit.py` | Add `domain: str = "other"` field to `AuditLogEntry` |
| `models/feedback.py` | New file — `FeedbackEntry` model |
| `engine/feedback_logger.py` | New file — BigQuery + local fallback for feedback |
| `engine/domain_classifier.py` | New file — `classify_domain()` function |
| `server.py` | Add `submit_feedback` tool, call `classify_domain()` before audit write, add `FeedbackLogger` to `AppContext` and initialize in `app_lifespan` |
| `engine/audit_logger.py` | Handle new `domain` column in BigQuery schema |
| `cli.py` | Add `dashboard` subcommand (with `ImportError` guard if streamlit not installed) |
| `pyproject.toml` | Add `[dashboard]` optional dependencies |

## 9. What This Does NOT Include

- No changes to existing MCP tools (`execute_query`, `list_datasets`, `get_table_schema`, `check_table_freshness`)
- No changes to governance rules in `.claude/rules/`
- No role-based access control
- No real-time streaming — dashboard refreshes on page load with 5-min cache
- No alerting/notifications (future phase)
- No mobile-optimized layout (desktop-first)

## 10. Success Criteria

- Dashboard loads in <5 seconds on Railway
- All 5 pages render correctly with real audit data
- Feedback tool works in Claude Code without disrupting user workflow
- Domain classification correctly tags >90% of successful queries (dry runs and errors use SQL fallback)
- Password protection prevents unauthorized access

## 11. Testing Strategy

- `classify_domain()` — unit tests with known table lists and SQL strings
- `FeedbackEntry` — model validation tests (valid/invalid ratings, missing fields)
- `FeedbackLogger` — unit tests with mocked BigQuery client (same pattern as `test_audit_logger.py`)
- `submit_feedback` tool — integration test verifying feedback is logged
- Dashboard query functions — tested with sample BigQuery responses (mocked client)

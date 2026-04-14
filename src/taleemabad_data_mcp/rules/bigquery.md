# BigQuery

- Every query MUST include a partition filter — reject without one, ask user to narrow scope
- Run dry run before every execution — show estimated bytes, require confirmation above `BIGQUERY_MAX_BYTES`
- Set `maximum_bytes_billed` on every query job — no exceptions
- Use parameterized queries (`bigquery.ScalarQueryParameter`) — never string-interpolate SQL
- Use BigQuery client from lifespan context — never create clients in tool functions
- Handle errors by type: `BadRequest` (syntax), `Forbidden` (permissions), `NotFound` (table), `InternalServerError` (circuit breaker)
- Unpartitioned tables → log as partition debt, don't run full scan

## Event Tables — Hierarchy

| Table | Status | Partition | Size | Notes |
|-------|--------|-----------|------|-------|
| `tbproddb.analytics_events` | **USE THIS** | DAY on `sent_at` | 70M+ rows | CANONICAL. Partitioned, most complete. Prefer this for all event queries. |
| `tbproddb.events_partitioned` | **FALLBACK** | DAY on `created` | 7.5 GB | Older partitioned copy. Use only if `analytics_events` is missing needed data. |
| `tbproddb.analytics_analyticsevent` | **NEVER USE** | None (unpartitioned) | 68.6 GB | Full table scan. Legacy, do not query directly. |

- Always include `WHERE sent_at >= DATE('...')` when querying `analytics_events`
- Always include `WHERE created >= DATE('...')` when querying `events_partitioned` (fallback only)
- The description on `analytics_events` mentions "Prefer `taleemabad_analytics.activity_events`" — this is a cross-dataset alias; use the `tbproddb.analytics_events` path

## PostgreSQL Databases — Hierarchy (Moawin / Akhuwat / Rawalpindi)

| Database | Role | Type | Schema | Notes |
|----------|------|------|--------|-------|
| `neondb` (Schoolpilot) | **USE THIS** for user/teacher data | PostgreSQL | `public.users`, `public.teachers`, `public.student_scores`, `public.assessments` | CANONICAL. User roster, institutional attributes, student assessments. |
| `zavia1` (Zavia) | **USE THIS** for AI coaching/LP/assessments | PostgreSQL | `public.lesson_plans`, `public.coaching_sessions`, `public.reading_assessments`, etc. | CANONICAL. AI-generated content, coaching pipeline, quality metrics. |

**Rules:**
- Every PostgreSQL query must specify database and schema explicitly: `neondb.public.users`, `zavia1.public.lesson_plans`
- When querying small unpartitioned tables (Schoolpilot/Zavia): full scans acceptable if table < 10,000 rows
- For large queries: check with data team on partition strategy
- No hardcoded credentials in queries — use environment variable substitution

- Design rationale: docs/VISION.md Section 10

---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# BigQuery

- Every query MUST include a partition filter — reject without one, ask user to narrow scope
- Run dry run before every execution — show estimated bytes, require confirmation above `BIGQUERY_MAX_BYTES`
- Set `maximum_bytes_billed` on every query job — no exceptions
- Use parameterized queries (`bigquery.ScalarQueryParameter`) — never string-interpolate SQL
- Use BigQuery client from lifespan context — never create clients in tool functions
- Handle errors by type: `BadRequest` (syntax), `Forbidden` (permissions), `NotFound` (table), `InternalServerError` (circuit breaker)
- Unpartitioned tables → log as partition debt, don't run full scan

## Event Tables — Always Use Partitioned Version
- `tbproddb.events_partitioned` — **USE THIS** for event queries. Partitioned daily on `created`, filter required. 7.5 GB.
- `tbproddb.analytics_analyticsevent` — **NEVER query directly**. Unpartitioned, 68.6 GB, full table scan. Only use if `events_partitioned` is confirmed missing the needed data.
- Always include `WHERE created >= DATE('...')` when querying `events_partitioned`

- Design rationale: docs/VISION.md Section 10

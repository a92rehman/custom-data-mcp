# Rules Index

This file is auto-loaded every session. It tells you where to find domain-specific rules and query definitions. Read the relevant subfolder ONLY when working on that domain.

## How This Works
- **Governance logic lives here** in `.claude/rules/` — not in Python code
- **MCP server is a thin execution layer** — use `execute_query`, `list_datasets`, `get_table_schema` tools
- When a user asks a data question: read the relevant domain rules below, find the correct query, clarify if needed, then use MCP tools to execute

## General Rules (always active)
- `data-governance.md` — metric access, audit, classification
- `bigquery.md` — partition-first policy, cost control, parameterized queries
- `caching.md` — freshness, invalidation, loop prevention
- `failure-handling.md` — retries, circuit breaker, dead letter queue
- `observability.md` — 3-layer telemetry, audit log, structured logging

## Domain Rules (load when working on that domain)

### dimensions/teachers/
When: user asks about teachers, user profiles, school assignments
- `teacher-query-rules.md` — mandatory questions: teacher level (PRIMARY/MIDDLE/SECONDARY) and region (org_id)
- `teacher-data.md` — query definitions for teacher_profiles and user_school_profiles

### theory_of_change/
When: user asks about LP adoption, coaching, FICO scores, student outcomes
- TBD — will be added as queries are provided

## BigQuery Context
- Project: `niete-bq-prod`
- 3 datasets: `RUMI_DB` (70 tables), `TaleemHub_DB` (60 tables), `tbproddb` (466 tables)
- organization_id = region (1 = ICT/Islamabad)
- levels = teacher level (PRIMARY, MIDDLE, SECONDARY) — JSON array

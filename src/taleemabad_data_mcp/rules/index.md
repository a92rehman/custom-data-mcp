# Rules Index

This file is auto-loaded every session. Read the relevant section based on the user's question.

## How This Works
- **Governance logic lives here** in `.claude/rules/` — not in Python code
- **MCP server is a thin execution layer** — use `execute_query`, `list_datasets`, `get_table_schema` tools
- **Rules are organized by region** — always determine the region first, then read that region's rules

## Step 1: Determine Region
Always clarify which region before reading domain rules:
- `organization_id = 1` → **ICT/Islamabad** → read `ict-islamabad/`
- Punjab/RWP → read `punjab-rwp/` (not yet available)
- Moawin → read `moawin/` (not yet available)

If the region's rules don't exist yet, tell the user: "Rules for [region] haven't been added yet."

## General Rules (all regions, always active)
- `data-governance.md` — metric access, audit, classification
- `bigquery.md` — partition-first policy, cost control, event table rules
- `caching.md` — freshness, invalidation, loop prevention
- `failure-handling.md` — retries, circuit breaker, dead letter queue
- `observability.md` — 3-layer telemetry, audit log, structured logging

## Region: ICT/Islamabad (`ict-islamabad/`)
Dataset: `tbproddb` | organization_id: 1 | School reference: `FDE_Schools`

### ict-islamabad/dimensions/teachers/
When: teacher profiles, user counts, school assignments
- `teacher-query-rules.md` — level (PRIMARY/MIDDLE/SECONDARY), required filters, key tables

### ict-islamabad/lesson_plans/
When: LP usage, completion rates, On-Schedule/Off-Schedule, Core vs User Generated
- `lp-query-rules.md` — LP types, status categories, counting rules, aggregation

### ict-islamabad/coaching_observations/
When: FICO scores, Section B/C/D, observer activity, feedback
- `observation-query-rules.md` — sections, score mapping, observer types, aggregation

### ict-islamabad/training/
When: teacher training levels, pass rates, completion status
- `training-query-rules.md` — pass threshold (>=80), two data sources, level ordering

## Region: Punjab/RWP (`punjab-rwp/`)
Not yet available. Will follow same domain structure when added.

## Region: Moawin (`moawin/`)
Not yet available. Will follow same domain structure when added.

## BigQuery Context
- Project: `niete-bq-prod`
- ICT/Islamabad dataset: `tbproddb` (466 tables)
- Other datasets: `RUMI_DB` (70 tables), `TaleemHub_DB` (60 tables)
- More datasets will be added after migration from other sources

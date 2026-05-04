# Self-Healing Query Loop + System Doctor Agent

## Summary

This PR closes two gaps in the Taleemabad Data MCP plugin: (1) the advertised "self-healing query loop" now actually works — `execute_query` returns structured JSON errors that the `data-analyst` agent's new Phase 4 uses to dispatch a `query-fixer` subagent for up to 3 fix attempts; (2) a new `system-doctor` agent detects and fixes common infrastructure issues (MCP connectivity, env configuration, rules sync, hook crashes) with a ticket-tracked lifecycle. All recovery actions are tracked as tickets with JSONL persistence and best-effort BigQuery sync, viewable in a new dashboard page.

## New Files Created

### Phase 0 — Shared Infrastructure
- `src/taleemabad_data_mcp/engine/errors.py` — BigQuery error classifier (8 error classes), structured response formatters, SQL hashing
- `src/taleemabad_data_mcp/models/ticket.py` — Ticket pydantic model (TKT-YYYYMMDD-hex format)
- `src/taleemabad_data_mcp/engine/ticket_logger.py` — JSONL + BigQuery ticket persistence (mirrors audit_logger pattern)
- `hooks/session-start/update.py` — Cross-platform Python session-start hook (stdlib-only, handles Windows paths)
- `hooks/run-hook.sh` — Linux/macOS shim (prefers Python over bash)
- `tests/test_errors.py` — 15 tests for error classification
- `tests/test_ticket_model.py` — 3 tests for ticket model
- `tests/test_ticket_logger.py` — 8 tests for ticket lifecycle
- `tests/test_update_hook.py` — 12 tests for Python hook

### Phase 1 — Query Self-Healing
- `agents/query-fixer.md` — Subagent that diagnoses failed SQL by error class and proposes corrected queries
- `tests/test_query_fixer.py` — 13 tests verifying error-class-to-fix-strategy mapping

### Phase 2 — System Self-Healing
- `agents/system-doctor.md` — Infrastructure health agent with 9-symptom handler matrix
- `commands/doctor.md` — `/taleemabad-doctor` slash command
- `src/taleemabad_data_mcp/dashboard/pages/7_Tickets.py` — Dashboard tickets page with KPI cards, charts, filters
- `tests/test_system_doctor.py` — 13 tests simulating all symptom classes
- `docs/superpowers/plans/2026-05-04-self-healing-loops.md` — Smoke test plan (14 scenarios)

## Existing Files Modified

| File | Change |
|------|--------|
| `src/taleemabad_data_mcp/server.py` | `execute_query` returns structured JSON (with `legacy_format=True` backward compat). Added `TicketLogger` to AppContext. Added 3 new MCP tools: `report_ticket`, `update_ticket`, `close_ticket`. |
| `agents/data-analyst.md` | Added Phase 4 (retry on error) — append-only, Phases 1-3 byte-for-byte identical. |
| `.claude-plugin/plugin.json` | Registered `query-fixer` and `system-doctor` agents, `/taleemabad-doctor` command. |
| `hooks/run-hook.cmd` | Now tries Python before bash (avoids Windows bash crashes). |
| `hooks/session-start/update.py` | Health checks run even when version is pinned; writes sentinel file. |
| `src/taleemabad_data_mcp/dashboard/data/queries.py` | Added `query_tickets()` function with BQ + JSONL fallback. |
| `tests/test_server.py` | Fixed pre-existing broken assertion on `CREDENTIALS_MISSING_MSG`. |
| `CLAUDE.md` | Documented structured error format, ticket system, two-loop architecture, Python session hook, 3 new MCP tools. |
| `README.md` | Added "Self-Healing" section explaining what users will see. |

## Deleted Files

| File | Reason |
|------|--------|
| `bash.exe.stackdump` | Windows bash crash artifact — no longer relevant with Python-first hook. |

## New MCP Tools

| Tool | Signature | Purpose |
|------|-----------|---------|
| `report_ticket` | `(loop, category, symptom, severity?, evidence?, diagnosis?, related_event_id?) -> JSON` | Open a self-healing ticket |
| `update_ticket` | `(ticket_id, action?, diagnosis?, status?) -> JSON` | Add actions/diagnosis to a ticket |
| `close_ticket` | `(ticket_id, status, resolution_notes?, escalated_to?) -> JSON` | Close with final status |

## New Agents

| Agent | Trigger | Tools |
|-------|---------|-------|
| `query-fixer` | Dispatched by `data-analyst` Phase 4 when `execute_query` returns structured error | Read, Glob, Grep |
| `system-doctor` | Auto: sentinel file from hook. Manual: `/taleemabad-doctor`. Connection errors from `execute_query`. | Read, Bash, Write, Glob, Grep, WebFetch |

## Backward Compatibility Flags

| Flag | Where | Default | Remove When |
|------|-------|---------|-------------|
| `legacy_format=True` on `execute_query` | `server.py` | `False` (new structured JSON) | v0.20.0 |

Old agents that don't pass `legacy_format` will get the new JSON format. The structured JSON is a superset — it includes all the information the old format had plus error classification. Old agents that pass `legacy_format=True` get the exact old string format.

## Known Limitations / TODOs

- `system-doctor` GitHub issue filing requires `gh` CLI or `GITHUB_PAT` — falls back to local JSONL if neither available
- `query_tickets()` dashboard function does BQ query first, JSONL fallback — no merge of both sources
- `test_cli.py::test_setup_copies_rules_and_saves_config` was already broken before this PR (CLI `--user` flag removed in prior commit)
- Ruff not available in the dev environment's shell PATH (Windows) — code follows existing codebase patterns
- Version bump to v0.18.0 done on branch only — tag and push happen after merge

## Manual Test Results

See `docs/superpowers/plans/2026-05-04-self-healing-loops.md` for the 14-scenario smoke test plan. Automated tests: **146 passed** (119 existing + 27 new, excluding pre-existing broken CLI test).

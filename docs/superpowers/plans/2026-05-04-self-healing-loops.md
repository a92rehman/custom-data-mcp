# Smoke Test Plan: Self-Healing Loops

## Query Loop Tests

### Test 1: SCHEMA_DRIFT — column renamed
- Trigger: Execute a query referencing a column that was renamed (e.g., `old_column_name`)
- Expected: `execute_query` returns structured JSON with `error_class: "SCHEMA_DRIFT"`, `column_referenced: "old_column_name"`
- Expected: data-analyst Phase 4 opens a ticket, dispatches query-fixer
- Expected: query-fixer reads schema, proposes SQL with correct column name
- Verify: ticket status transitions open → diagnosing → auto_fixed

### Test 2: MISSING_PARTITION — no date filter
- Trigger: Execute `SELECT * FROM tbproddb.analytics_events` without `sent_at` filter
- Expected: `error_class: "MISSING_PARTITION"`
- Expected: query-fixer adds partition filter based on rule file
- Verify: corrected SQL includes `WHERE sent_at >= DATE(...)`

### Test 3: SYNTAX_ERROR — typo
- Trigger: Execute `SELECCT * FROM tbproddb.users_user`
- Expected: `error_class: "SYNTAX_ERROR"`
- Expected: query-fixer corrects `SELECCT` → `SELECT`

### Test 4: COST_EXCEEDED — too wide date range
- Trigger: Execute a query scanning >10GB
- Expected: `error_class: "COST_EXCEEDED"`
- Expected: query-fixer tightens date range or switches to curated table

### Test 5: Give-up after 3 attempts
- Trigger: Execute a query with a fundamentally broken join (no valid fix)
- Expected: query-fixer returns `give_up` after attempt 3
- Expected: ticket closed as `escalated`, user sees human-readable summary with ticket ID

### Test 6: System-level error routes to doctor
- Trigger: `execute_query` returns `BIGQUERY_UNAVAILABLE`
- Expected: data-analyst Phase 4 does NOT dispatch query-fixer
- Expected: ticket closed as `escalated` with note "routed to system-doctor"

## System Loop Tests

### Test 7: connection_failed
- Trigger: `/taleemabad-doctor` when MCP server is unreachable (disconnect internet or mock)
- Expected: ticket opened for `connection_failed`, retry after 10s
- If still down: ticket status → user_action_required

### Test 8: user_env_missing
- Trigger: Delete `~/.claude/taleemabad-data-mcp.env`, run `/taleemabad-doctor`
- Expected: doctor detects missing env, attempts recovery from audit log
- If no audit history: asks user for email

### Test 9: rules_path_missing
- Trigger: Delete `~/.claude/taleemabad-rules-path`, run `/taleemabad-doctor`
- Expected: doctor re-runs Python hook, verifies rules path restored

### Test 10: hook_crashed
- Trigger: Place a `bash.exe.stackdump` in repo, run `/taleemabad-doctor`
- Expected: doctor detects stackdump, verifies Python hook is preferred, deletes stackdump

### Test 11: GitHub escalation dry-run
- Trigger: Force 2 failures on `rules_path_missing`
- Expected: ticket escalated, issue body written to `~/.claude/taleemabad-tickets-pending-github.jsonl`
- Verify: issue body contains ticket_id, sanitized evidence, no raw emails

## Backward Compatibility Tests

### Test 12: legacy_format=True
- Trigger: `execute_query(sql="SELECT 1", legacy_format=True)`
- Expected: returns plain text string (not JSON), byte-for-byte identical to old format
- Verify: deprecation warning in structlog

### Test 13: Existing agents unaffected
- Trigger: Ask a data question using the old cached `data-analyst` (Phases 1-3 only)
- Expected: works exactly as before — Phase 4 is additive, old agents don't read it

## Dashboard Tests

### Test 14: Empty tickets table
- Trigger: Open dashboard Tickets page when `mcp_audit.system_tickets` has 0 rows
- Expected: page shows "No tickets found" info message, no crash

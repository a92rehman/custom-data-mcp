# Distribution & Observability Design

**Date:** 2026-04-06
**Status:** Approved

## Problem

The MCP server works locally but has no distribution story. Teams can't install it without cloning the repo. The governance rules only work inside this project directory. There's no activity tracking.

## Design

### 1. CLI Setup Command

A `setup` subcommand that installs everything to user-level Claude Code config:

```bash
uvx taleemabad-data-mcp setup --user "Name" --credentials /path/to/key.json
```

**What it does:**
1. Copies `.claude/rules/` → `~/.claude/rules/taleemabad/`
2. Merges MCP server config into `~/.claude/settings.json`
3. Stores user name + credentials path in `~/.claude/taleemabad-data-mcp.env`

**Also provides:**
- `uvx taleemabad-data-mcp uninstall` — removes rules + config
- `uvx taleemabad-data-mcp setup` re-run — updates rules to latest version

### 2. Activity Tracking (BigQuery Audit Table)

Every query execution writes to `mcp_audit.activity_log` in BigQuery:

| Column | Type | Source |
|--------|------|--------|
| event_id | STRING | UUID |
| timestamp | TIMESTAMP | UTC now |
| user_name | STRING | From setup --user |
| hostname | STRING | Auto-detected |
| query_text | STRING | The SQL executed |
| tables_accessed | ARRAY<STRING> | From BQ job metadata |
| rows_returned | INT64 | Result count |
| execution_ms | INT64 | From BQ job metadata |
| cost_bytes | INT64 | Bytes billed |
| cost_usd | FLOAT64 | Calculated |
| error_type | STRING | If failed |
| error_message | STRING | If failed |

The audit logger writes to BigQuery instead of in-memory list. Falls back to local JSON Lines file if BQ write fails.

### 3. Freshness Tool

New MCP tool `check_table_freshness` that queries `INFORMATION_SCHEMA.PARTITIONS` / `__TABLES__` to return last modified timestamp. Claude uses this per the caching rules.

### 4. Package Structure Changes

```
src/taleemabad_data_mcp/
  __main__.py         # Route: "setup", "uninstall", or default MCP server
  cli.py              # Setup/uninstall logic
  rules/              # Governance rules (copied from .claude/rules/)
    index.md
    data-governance.md
    bigquery.md
    ...
  server.py           # MCP server (unchanged + new freshness tool)
  engine/
    audit_logger.py   # Rewritten: writes to BigQuery + local fallback
```

**Single source for rules:** Rules live in `src/taleemabad_data_mcp/rules/`. During development, `.claude/rules/` is a symlink or copy. The `setup` command copies from the package's bundled rules.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/taleemabad_data_mcp/cli.py` | **Create** — setup/uninstall commands |
| `src/taleemabad_data_mcp/__main__.py` | **Modify** — route to CLI or MCP server |
| `src/taleemabad_data_mcp/rules/` | **Create** — move rules here as single source |
| `src/taleemabad_data_mcp/server.py` | **Modify** — add check_table_freshness tool |
| `src/taleemabad_data_mcp/engine/audit_logger.py` | **Modify** — BigQuery writes + local fallback |
| `src/taleemabad_data_mcp/models/audit.py` | **Modify** — add cost fields |
| `src/taleemabad_data_mcp/config.py` | **Modify** — add user_name, audit dataset config |
| `tests/test_cli.py` | **Create** — test setup/uninstall |
| `tests/test_freshness.py` | **Create** — test freshness tool |
| `pyproject.toml` | **Modify** — add CLI entry point |

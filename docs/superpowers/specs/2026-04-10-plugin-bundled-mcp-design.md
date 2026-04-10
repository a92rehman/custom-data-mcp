# Plugin-Bundled MCP Architecture — Design Spec

**Date:** 2026-04-10
**Status:** Draft
**Author:** Claude + AR

## Problem

The current plugin architecture separates the MCP server from the plugin. Users must:
1. Install the plugin (gets agents, commands, rules)
2. Run `/taleemabad-setup` (creates a venv, copies rules, generates `.mcp.json`)
3. Copy credentials to each project
4. Run `/taleemabad-init` in every new project (generates another `.mcp.json`)
5. Restart Claude Code

This multi-step process has caused cascading errors across v0.7–v0.11:
- uv startup timeouts from `git+https://` fetches on every MCP start
- Absolute vs relative credential path mismatches
- Missing credentials files in new projects
- Bash wrapper failures on Windows due to env var inheritance
- Venv path issues across machines

Other plugins (claude-mem, everything-claude-code) solve this by bundling MCP config in a `.mcp.json` at the plugin root — one install, zero manual wiring.

## Decision

**Bundle the MCP server config inside the plugin** using `.mcp.json` at plugin root with `uv run --directory ${CLAUDE_PLUGIN_ROOT}`. Drop `bigquery-analytics` MCP server entirely (redundant — our `execute_query` does everything it does, plus governance).

## Architecture

### Before (Current)

```
Plugin install → agents + commands + rules (NO MCP)
     ↓
/taleemabad-setup → creates venv + copies rules + writes .mcp.json
     ↓
Per project: /taleemabad-init → writes another .mcp.json
     ↓
Restart → MCP server starts from user-managed venv
```

### After (New)

```
Plugin install → agents + commands + rules + MCP server config
     ↓
Copy credentials file to project directory
     ↓
/taleemabad-setup → asks name (one time, recommended for audit identity)
     ↓
Restart → MCP server auto-starts via uv run --directory
```

## Plugin `.mcp.json`

New file at plugin root. **Must be un-ignored in `.gitignore`** — the current `.gitignore` has `.mcp.json` on the ignore list and a blanket `*.json` rule. Add `!.mcp.json` exception (after the `.mcp.json` ignore line) so the plugin's `.mcp.json` is committed to the repo and reaches users via plugin install.

The existing development `.mcp.json` (pointing to local venv with absolute paths) will be **replaced** by this plugin-level config.

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "uv",
      "args": [
        "run", "--directory", "${CLAUDE_PLUGIN_ROOT}",
        "python", "-m", "taleemabad_data_mcp", "serve"
      ],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "./niete-bq-prod-48ae5260d1ea.json",
        "TALEEMABAD_USER": "${TALEEMABAD_USER}"
      }
    }
  }
}
```

**Why `uv run --directory`:**
- The old timeout issue was `uv run --with git+https://...` which did a git fetch on every startup
- `--directory` uses local source from plugin cache — no network calls after first dependency install
- First startup: ~15s (installs dependencies). Subsequent: instant (uv caches the venv).
- uv ships with Claude Code at `~/.claude/uv`

**Why drop `bigquery-analytics`:**
- It only has one tool: `query` (raw SQL executor)
- Our `execute_query` does the same thing plus audit logging, cost guardrails, and domain classification
- Having an ungoverned SQL executor alongside a governed one undermines the whole governance model

## Credentials Missing — Graceful Degradation

Since the plugin MCP server is declared globally, it will attempt to start in **every** Claude Code session, including projects without the credentials file. The server MUST handle this gracefully:

- If `GOOGLE_APPLICATION_CREDENTIALS` points to a missing file, the server should **start successfully** but return clear errors when tools are called: "BigQuery credentials not found. Copy `niete-bq-prod-48ae5260d1ea.json` to this project directory."
- This means `server.py` lifespan must catch the missing-credentials error and set a flag rather than crashing
- Tools check this flag and return the helpful error message instead of an opaque stack trace
- The MCP server process stays alive so Claude Code doesn't show a connection failure

This is a change to `server.py` — moved from UNCHANGED to MODIFY in File Changes below.

## User Experience

### First-time setup (any machine)

1. `claude plugin install taleemabad-data@Orenda-Project`
2. Copy `niete-bq-prod-48ae5260d1ea.json` to project directory (data team provides)
3. `/taleemabad-setup` — asks name, saves to `~/.claude/taleemabad-data-mcp.env`
4. Restart Claude Code
5. Done

### New project (same machine)

1. Copy credentials file to project directory
2. Done

### New machine

1. Install plugin + copy credentials + `/taleemabad-setup` + restart
2. Done

## File Changes

### CREATE

| File | Purpose |
|------|---------|
| `.mcp.json` (plugin root) | MCP server config with `uv run --directory`. Must un-ignore in `.gitignore`. |

### MODIFY

| File | Change |
|------|--------|
| `.gitignore` | Add `!.mcp.json` exception so plugin `.mcp.json` is committed. Remove the `.mcp.json` ignore line (or override with `!`). |
| `.claude-plugin/plugin.json` | Remove `init.md` from commands array |
| `commands/setup.md` | Simplify: ask name, save config, sync rules. No venv creation, no `.mcp.json` generation. Remove Git prerequisite. Remove `bigquery-analytics` from verification output. |
| `src/taleemabad_data_mcp/cli.py` | Remove `init` command, `upgrade` command, `_write_mcp_json()`, `_mcp_json_content()`, `_bigquery_analytics_config()`, `_to_bash_path()`, `_find_uv_command()`, `_mcp_server_config()`. Simplify `setup` to only save user config and sync rules. Simplify `uninstall` to remove rules dir + env file only (no venv, no settings.json). |
| `agents/data-analyst.md` | Remove references to `bigquery-analytics` MCP tools (lines 107-109, 134). Note: visualization/charting capability is removed until Phase 2/3 tools are added. Agent should acknowledge this limitation when users ask for charts. |
| `hooks/session-start/update.sh` | Remove venv update logic (lines 69-79 that do `pip install --force-reinstall git+https://...`). Add logic to read `~/.claude/taleemabad-data-mcp.env` and export `TALEEMABAD_USER` into the shell environment. Keep rule syncing and tag checking. |
| `src/taleemabad_data_mcp/server.py` | Add graceful degradation for missing credentials (see "Credentials Missing" section). Add Phase 1 tools: `preview_table`, `save_query_results`, `describe_data`. |

### DELETE

| File | Reason |
|------|--------|
| `commands/init.md` | No longer needed — no per-project `.mcp.json` generation |

### UNCHANGED

| Files | Reason |
|-------|--------|
| `agents/data-admin.md` | No changes needed |
| `rules/*` | Governance rules unchanged |
| `src/taleemabad_data_mcp/engine/*` | Audit, cost, domain unchanged |
| `src/taleemabad_data_mcp/config.py` | Config unchanged |
| `tests/*` | Updated separately |

## `TALEEMABAD_USER` Handling

The MCP server env references `${TALEEMABAD_USER}`. Claude Code expands `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` as special plugin variables, but arbitrary env vars like `${TALEEMABAD_USER}` are expanded from the **shell environment** at process start time.

**Strategy:**

1. `/taleemabad-setup` asks for name → saves to `~/.claude/taleemabad-data-mcp.env`
2. Session-start hook (`hooks/session-start/update.sh`) reads the env file and **exports `TALEEMABAD_USER`** into the shell environment so Claude Code's MCP process inherits it
3. If the env var is not set (hook didn't run, or setup never ran), the MCP server's `config.py` falls back to `"unknown"` — queries still work, audit logs lack user name

**Fallback chain:** Shell env var (set by hook) → `config.py` default `"unknown"`

**Important:** The session-start hook must be MODIFIED to add the env var export logic. See File Changes below.

## New MCP Tools (Phased)

### Phase 1 (this release)

| Tool | Purpose | Governance |
|------|---------|------------|
| `preview_table` | Quick peek at table data (10 rows) | Checks allowed datasets, respects partition filters, blocks banned tables, audit logged |
| `save_query_results` | Export governed query results to CSV/JSON | Only saves governed query results, adds metadata header, checks data classification, audit logged |
| `describe_data` | Descriptive statistics on governed query results | Runs governed query first, education-aware stats (score distributions, coverage %), flags data quality issues, audit logged |

### Phase 2 (next release)

| Tool | Purpose | Governance |
|------|---------|------------|
| `analyze_trends` | Time series analysis | Saturday-Friday weeks, Asia/Karachi timezone, domain-aware (LP status shifts, FICO section trends) |
| `detect_anomalies` | Outlier detection | Context-aware thresholds from rules (FICO 0-1, LP ratio capped, training pass >= 80), distinguishes data bugs from real anomalies |
| `generate_insights` | Auto-generate cross-domain insights | Maps to Theory of Change, runs multiple governed queries, labels correlation vs causation |

### Phase 3 (future)

Dashboard and report generation tools — separate design.

### Tool Governance Pattern

Every tool follows:

```
1. Validate inputs (allowed dataset? partition filter?)
2. Check governance (table covered by rules?)
3. Execute with guardrails (cost limits, max bytes billed)
4. Audit log (who, what, when, cost, domain)
5. Return results with context (freshness, caveats, classification)
```

## Credentials

- File: `niete-bq-prod-48ae5260d1ea.json` (shared GCP service account key)
- Distribution: Data team provides to each org member
- Location: Must be in each project directory
- Path in config: `./niete-bq-prod-48ae5260d1ea.json` (relative — portable)
- `.gitignore`: Must include the credentials filename

## Rules Distribution

Rules ship with the plugin in two copies:

| Location | Who reads | Purpose |
|----------|-----------|---------|
| `${CLAUDE_PLUGIN_ROOT}/rules/` | Agents (data-analyst, data-admin) | Build governed queries |
| `~/.claude/rules/taleemabad/` | Claude Code system | Auto-loaded as session context |

Session-start hook syncs plugin rules → user rules directory.

## Migration Path

For existing users on v0.11.0:

1. Update plugin (auto-updates via session-start hook git tag check)
2. Existing `.mcp.json` files in project directories become **redundant** — plugin provides the MCP config now
3. Existing `~/.claude/taleemabad-venv/` becomes **orphaned** — can be cleaned up
4. `/taleemabad-setup` still works (just simpler now)
5. Old `.mcp.json` files should be **deleted** from project directories

### Coexistence: Plugin `.mcp.json` vs Project `.mcp.json`

If a project has its own `.mcp.json` that also declares a `taleemabad-data` server, Claude Code will see **two servers with the same name**. The project-level config takes precedence (shadows the plugin config). This means:
- Old project `.mcp.json` files will override the plugin config silently
- Users must delete old per-project `.mcp.json` files to use the plugin config
- The simplified `/taleemabad-setup` should check for and offer to remove existing `.mcp.json` files

### Cleanup Steps

The updated `/taleemabad-setup` or a new `/taleemabad-cleanup` command should:
1. Delete `~/.claude/taleemabad-venv/` if it exists (orphaned)
2. Warn if current project has a `.mcp.json` with `taleemabad-data` and offer to remove it
3. Remove stale MCP entries from `~/.claude/settings.json` if present

## Risks

| Risk | Mitigation |
|------|------------|
| `uv` not on PATH | Claude Code ships uv at `~/.claude/uv`. Session-start hook can add to PATH if needed. |
| First startup slow (~15s) | One-time cost. Subsequent starts are instant. Show progress message. |
| `${CLAUDE_PLUGIN_ROOT}` not expanded | Standard plugin variable — claude-mem and everything-claude-code both use it successfully. |
| Credentials file missing in non-data project | Server starts but returns helpful error on tool calls (graceful degradation). Does NOT crash. |
| `TALEEMABAD_USER` not set | Server falls back to "unknown". Queries still work. Audit logs lack user name. |
| Old per-project `.mcp.json` shadows plugin config | Setup command warns and offers cleanup. Documented in migration path. |
| `${TALEEMABAD_USER}` not expanded by Claude Code | Env vars in `.mcp.json` `env` block are passed to the process — the shell expands them. If not set, the value is empty string, and `config.py` defaults to "unknown". |

## Success Criteria

- [ ] `claude plugin install` + copy credentials + restart = working MCP
- [ ] No `/taleemabad-init` needed for new projects
- [ ] No venv management by users
- [ ] No `.mcp.json` generation by users
- [ ] All 6 existing tools work
- [ ] Phase 1 tools (preview_table, save_query_results, describe_data) work
- [ ] Audit logging works for all tools
- [ ] Works on Windows and macOS
- [ ] Existing users can migrate without data loss

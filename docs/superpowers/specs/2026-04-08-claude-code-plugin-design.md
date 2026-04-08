# Taleemabad Data — Claude Code Plugin Design

**Date:** 2026-04-08
**Status:** Approved
**Author:** Claude + User

---

## Overview

Convert the Taleemabad Data MCP server + governance rules into a formal Claude Code plugin that installs globally, auto-updates via git tags, and provides intelligent data agents to every team member.

## Goals

1. One-command installation for non-technical staff
2. Auto-update rules/agents without user action
3. Two intelligent agents (data-analyst, data-admin) that enforce governance
4. Add analysis/visualization via a second MCP server (bigquery-analytics)
5. Self-healing query loop that handles schema drift gracefully
6. Preserve all existing observability (audit, feedback, dashboard)

## Non-Goals

- Rewriting the existing MCP server
- Changing the Streamlit dashboard
- Building custom analysis tools (use third-party MCP)

---

## Plugin Directory Structure

```
~/.claude/plugins/taleemabad-data/
├── manifest.json                    # Plugin metadata (name, version, description)
├── .mcp.json                        # Two MCP servers config
├── agents/
│   ├── data-analyst.md              # Primary query agent
│   └── data-admin.md               # Diagnostics agent
├── rules/
│   ├── index.md                     # Rules router (region -> domain)
│   ├── bigquery.md
│   ├── data-governance.md
│   ├── caching.md
│   ├── failure-handling.md
│   ├── observability.md
│   ├── versioning.md
│   ├── ict-islamabad/              # Full ICT rules tree
│   │   ├── dimensions/teachers/teacher-query-rules.md
│   │   ├── lesson_plans/lp-query-rules.md
│   │   ├── coaching_observations/observation-query-rules.md
│   │   ├── coaching_ai/ai-coaching-rules.md
│   │   ├── student_results/ai-assessment-rules.md
│   │   ├── student_results/aser-enumerator-rules.md
│   │   └── training/training-query-rules.md
│   └── rawalpindi/                  # Full RWP rules tree
│       ├── dimensions/users/user-query-rules.md
│       ├── lesson_plans/lp-query-rules.md
│       ├── coaching/human-coaching-rules.md
│       ├── coaching/ai-coaching-rules.md
│       ├── student_results/ai-assessment-rules.md
│       └── student_results/human-assessment-rules.md
├── hooks/
│   └── on_session_start.sh          # Auto-update via git tags
├── install.sh                       # Unix installer
├── install.ps1                      # Windows installer
└── README.md                        # Quick start guide
```

---

## Two MCP Servers

Configured in the plugin's `.mcp.json`. Both connect to `niete-bq-prod`.

### taleemabad-data (existing, unchanged)

The governance and audit layer. No code changes.

| Tool | Purpose |
|------|---------|
| `execute_query` | Run governed SQL with cost guardrails + audit logging |
| `list_datasets` | Browse allowed datasets and tables |
| `get_table_schema` | Get columns and types |
| `check_table_freshness` | Check table last modified time |
| `submit_feedback` | Log thumbs up/down on results |
| `get_version` | Return version, user, project info |

### bigquery-analytics (new, third-party)

Analysis and visualization layer. Third-party package (e.g., `@ergut/bigquery-mcp`).

| Category | Tools |
|----------|-------|
| Analysis | describe_data, analyze_trends, find_correlations, detect_anomalies, generate_insights |
| Dashboard | create_dashboard, add_chart, add_metric_card, add_table_widget, export_dashboard |
| Reports | generate_html_report, generate_pdf_report, create_summary_report, save_query_results |

**Routing rule:** All data queries go through `taleemabad-data` first (governance + audit). `bigquery-analytics` is only used for analysis and visualization of already-retrieved results, or when the user explicitly asks for charts/reports/trends.

---

## Two Agents

### data-analyst (primary, ~95% of interactions)

**Trigger:** User asks anything about Taleemabad data — teacher counts, LP rates, observation scores, training progress, student results, coaching metrics.

**Always active globally.** Agent description contains sufficient keywords for Claude to route data questions automatically.

**Flow:**
1. **Intercept** — Claude routes data question to this agent
2. **Read rules** — Agent reads `rules/index.md`, determines region and domain, reads relevant rule files
3. **Clarify** — Agent asks mandatory clarification questions defined in the rules (region, teacher level, time period, session, aggregation level, etc.)
4. **Generate SQL** — Agent builds governed SQL following rules exactly
5. **Self-healing execute** — Run through diagnosis loop (see below)
6. **Present** — Show results with freshness timestamp, cost, domain, caveats
7. **Analyze** (optional) — If user wants trends/charts/reports, route to bigquery-analytics MCP
8. **Feedback** — Ask for thumbs up/down via submit_feedback

**What it does NOT do:**
- Generate ad-hoc SQL outside of rules
- Schema browsing or diagnostics (data-admin's job)
- Setup or installation help

### data-admin (diagnostics)

**Trigger:** User asks about table freshness, schema, audit logs, costs, pipeline health, setup issues.

**Capabilities:**
- Table freshness checks via `check_table_freshness`
- Schema browsing via `list_datasets` + `get_table_schema`
- Audit log queries (reads from `mcp_audit.activity_log`)
- Cost analysis
- Setup troubleshooting
- Version info via `get_version`

---

## Self-Healing Query Loop

When the data-analyst agent generates and executes a query, this loop handles failures:

```
Generate SQL from rules
  |
  +-- Dry run (cost check)
  |     Pass -> Execute
  |     Fail -> DIAGNOSIS
  |
  +-- Execute
  |     Success + rows > 0 -> Present results
  |     Success + zero rows -> ZERO-ROW CHECK
  |     Fail -> DIAGNOSIS
  |
  +-- DIAGNOSIS
  |     Column not found:
  |       -> get_table_schema, compare vs rules
  |       -> Find renamed/new column, adjust query, retry
  |       -> Log RULE_DRIFT
  |     Table not found:
  |       -> list_datasets, search for similar name
  |       -> If found: adjust, retry. If not: hard stop.
  |       -> Log RULE_DRIFT
  |     Syntax/type error:
  |       -> Read error, fix SQL, retry
  |     Permission denied:
  |       -> Hard stop immediately, tell user
  |
  +-- ZERO-ROW CHECK
  |     -> Run COUNT(*) on the base table with partition filter
  |     -> Data exists? Filters too narrow, tell user
  |     -> No data? Table empty, tell user
  |     -> Log VERIFICATION_WARNING
  |
  +-- HARD STOP (after 2 retries)
        -> Stop retrying
        -> Show: error, what was tried, recommendation
        -> Log QUERY_FAILURE
```

**Key constraints:**
- Max 2 retries (consistent with failure-handling.md rules)
- Results that return data are trusted — no second-guessing
- Outlier/NULL detection left to bigquery-analytics MCP on user request
- Every drift/failure logged for your visibility

---

## Ungoverned Requests

When a user asks a question with no matching rules:

1. Agent reads `rules/index.md`, finds no matching domain
2. Tells user: "No governed query exists for this request"
3. Offers to check if relevant tables exist (schema browse via data-admin)
4. Logs `UNGOVERNED_REQUEST` to audit with the original question
5. **Never generates ad-hoc SQL**

These logs become your backlog — you see what users need that isn't covered yet.

---

## Audit Domains (new additions)

| Domain | Meaning | Your action |
|--------|---------|-------------|
| `RULE_DRIFT` | Schema changed vs what rules say | Update the rules file |
| `QUERY_FAILURE` | Failed after 2 retries | Investigate table/permissions |
| `UNGOVERNED_REQUEST` | No rules for this question | Write new rules |
| `VERIFICATION_WARNING` | Zero rows returned unexpectedly | Check data pipeline |

Existing domains (per query: teachers, lesson_plans, observations, training, etc.) remain unchanged.

---

## Installation

### One-command install

**Unix (macOS/Linux):**
```bash
curl -sL https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/install.ps1 | iex
```

### What the install script does

1. Clone repo to `~/.claude/plugins/taleemabad-data/`
2. Create dedicated venv at `~/.claude/taleemabad-venv/`
3. Install `taleemabad-data-mcp` package into venv (from repo)
4. Install `bigquery-analytics` MCP via npm/npx
5. Prompt for user name + path to GCP credentials JSON
6. Save config to `~/.claude/taleemabad-data-mcp.env`
7. Print success message with version

### Prerequisites
- Python 3.11+
- Node.js (for bigquery-analytics MCP)
- Git
- GCP service account key JSON file
- Claude Code installed

---

## Auto-Update

### Mechanism

Plugin hook `hooks/on_session_start.sh` runs every time Claude Code opens:

```bash
cd ~/.claude/plugins/taleemabad-data
git fetch --tags --quiet 2>/dev/null
LATEST=$(git describe --tags --abbrev=0 origin/main 2>/dev/null)
CURRENT=$(git describe --tags --abbrev=0 2>/dev/null)
if [ "$LATEST" != "$CURRENT" ] && [ -n "$LATEST" ]; then
  git checkout "$LATEST" --quiet
  echo "Taleemabad Data Plugin updated to $LATEST"
fi
```

### Update flow (developer side)

1. Edit rules, agents, or plugin files in repo
2. Commit and push
3. Tag: `git tag v0.5.0 && git push --tags`
4. Every user gets the update next time they open Claude Code

### Safety

- Only pulls tagged releases, never raw commits
- If git fails (no network, etc.): silent, uses current version
- Never breaks a running session — update happens at session start only

---

## What Changes vs Current System

| Component | Current | After plugin |
|-----------|---------|-------------|
| MCP server code | 6 tools | **Unchanged** (same 6 tools) |
| Audit/observability | BigQuery + JSONL fallback | **Unchanged** + 4 new audit domains |
| Streamlit dashboard | Reads mcp_audit tables | **Unchanged** |
| Rules location | `~/.claude/rules/taleemabad/` | `~/.claude/plugins/taleemabad-data/rules/` |
| MCP config | `~/.claude/settings.json` | Plugin's `.mcp.json` |
| Agent definitions | None (Claude reads raw rules) | Two formal agents with defined flows |
| Analysis/visualization | None | bigquery-analytics MCP (new) |
| Installation | Manual multi-step | One-command script |
| Updates | Manual `upgrade` command | Auto on session start via git tags |
| Self-healing | None | Diagnosis + retry loop |
| Ungoverned tracking | None | Logged to audit |

---

## Migration for Existing Users

Users who already have the current setup:

1. Run the install script — it creates the plugin
2. Remove old rules: `rm -rf ~/.claude/rules/taleemabad/`
3. Remove old MCP config from `~/.claude/settings.json` (the `taleemabad-data` key)
4. The install script can do steps 2-3 automatically if it detects the old setup

---

## Spec Review Fixes

Issues identified during spec review and their resolutions:

### 1. Plugin system verification (Critical)

The plugin directory structure (`manifest.json`, `agents/`, `hooks/`) is based on observed Claude Code plugin conventions (e.g., `superpowers`, `everything-claude-code` plugins). **Before implementation:** examine actual installed plugins at `~/.claude/plugins/` to confirm the exact format. If the format differs, adapt the directory structure accordingly. Fallback: rules in `~/.claude/rules/`, MCP in `settings.json`, agents as global CLAUDE.md instructions.

### 2. Git detached HEAD fix (Critical)

The auto-update script uses `git checkout <tag>` which detaches HEAD. Fixed approach:

```bash
cd ~/.claude/plugins/taleemabad-data
# Check for pinned version (rollback escape hatch)
if [ -n "$TALEEMABAD_PIN_VERSION" ]; then exit 0; fi

git fetch --tags --quiet 2>/dev/null || exit 0
LATEST=$(git tag -l 'v*' --sort=-v:refname | head -1)
CURRENT=$(cat .current-version 2>/dev/null || echo "none")
if [ "$LATEST" != "$CURRENT" ] && [ -n "$LATEST" ]; then
  git checkout "$LATEST" --quiet 2>/dev/null
  echo "$LATEST" > .current-version
  echo "Taleemabad Data Plugin updated to $LATEST"
fi
```

Version tracked via `.current-version` file, not `git describe`.

### 3. MCP routing enforcement (Critical)

The agent prompt alone is insufficient to prevent Claude from calling `bigquery-analytics` tools directly. Mitigation:

- **Agent prompt** explicitly lists allowed `bigquery-analytics` tools: `analyze_trends`, `find_correlations`, `detect_anomalies`, `generate_insights`, `create_dashboard`, `add_chart`, `add_metric_card`, `generate_html_report`, `export_dashboard`
- **Blocked tools** from `bigquery-analytics`: `execute_query`, `build_query`, `preview_table` — agent prompt says "NEVER call these, use taleemabad-data equivalents"
- **Accept risk** that prompt-based enforcement is not 100% — but audit logging via `taleemabad-data` will show gaps if bypassed

### 4. Third-party MCP evaluation (Important)

Before implementation, evaluate candidate packages:
- `@ergut/bigquery-mcp` — verify exact tool list
- Alternatives: `@modelcontextprotocol/bigquery`, community packages
- Requirements: same `GOOGLE_APPLICATION_CREDENTIALS` auth, analysis/visualization tools
- If no package provides dashboard/report tools, fall back to Streamlit for visualization

### 5. Credential sharing (Important)

Both MCP servers use the same `GOOGLE_APPLICATION_CREDENTIALS` env var in `.mcp.json`. The install script writes the credentials path once, referenced by both server configs. No separate auth needed.

### 6. Agent context budget (Important)

Rules files total ~50KB of markdown. Agents should NOT load all rules eagerly. Strategy:
- Agent loads `rules/index.md` first (router, ~2KB)
- Loads specific domain rules on demand based on user question (~2-5KB each)
- Max ~10KB of rules in context per query
- Detailed agent prompts will be written during implementation

### 7. Installation security (Minor)

Changed from `curl | bash` to two-step:
```bash
# Unix
curl -sLO https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/install.sh
chmod +x install.sh && ./install.sh

# Windows
Invoke-WebRequest -Uri "...install.ps1" -OutFile install.ps1
.\install.ps1
```

### 8. Rollback mechanism (Minor)

Added `TALEEMABAD_PIN_VERSION` env var. When set, the auto-update hook skips entirely:
```bash
export TALEEMABAD_PIN_VERSION=v0.4.5  # Pin to this version
```

### 9. Path reference migration (Minor)

Migration checklist must include updating all internal cross-references:
- `CLAUDE.md` references to `~/.claude/rules/taleemabad/`
- Rule files that reference other rule files by path
- Any hardcoded paths in CLI commands

---

## Open Questions (remaining)

1. **Which bigquery-analytics MCP package?** Evaluate during implementation. Must support `GOOGLE_APPLICATION_CREDENTIALS` auth and provide analysis/visualization tools.
2. **Exact Claude Code plugin format?** Verify by examining existing installed plugins before writing manifest.json.

# Claude Code Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the Taleemabad Data MCP server + governance rules as a distributable Claude Code plugin with one-command installation, auto-update via git tags, two intelligent agents, and a self-healing query loop.

**Architecture:** The plugin lives in the repo at `plugin/` and is distributed as a git-cloned directory at `~/.claude/plugins/taleemabad-data/`. It uses the standard Claude Code plugin format (`.claude-plugin/plugin.json`, `agents/`, `hooks/`, `.mcp.json`) discovered from examining installed plugins. The existing MCP server code is **not changed** — the plugin wraps it with distribution, configuration, agents, and a second analytics MCP server.

**Tech Stack:** Python 3.11+, FastMCP (existing), Node.js/npx (for analytics MCP), Bash + PowerShell (install scripts), Git (auto-update), JSON (plugin manifest, hooks config)

---

## Subsystem Breakdown

This plan covers 6 independent subsystems. Each can be tested in isolation:

1. **Plugin scaffold** — directory structure, manifest, package.json
2. **Agent definitions** — data-analyst and data-admin markdown agents
3. **MCP configuration** — `.mcp.json` with both servers wired up
4. **Hooks** — session-start auto-update script
5. **Install scripts** — Unix `install.sh` and Windows `install.ps1`
6. **CLI integration** — new `bump` command, migration instructions update

---

## File Map

### New files (all inside repo at `plugin/`)

| File | Responsibility |
|------|---------------|
| `plugin/.claude-plugin/plugin.json` | Plugin manifest — name, version, agents list, skills, commands |
| `plugin/package.json` | npm package descriptor (required by plugin system) |
| `plugin/agents/data-analyst.md` | Primary query agent — rules routing, SQL generation, self-healing loop |
| `plugin/agents/data-admin.md` | Diagnostics agent — schema, freshness, audit log, costs |
| `plugin/.mcp.json` | Two MCP server configs (taleemabad-data + bigquery-analytics) |
| `plugin/hooks/hooks.json` | Session start hook config (points to auto-update script) |
| `plugin/hooks/run-hook.cmd` | Windows hook runner shim |
| `plugin/hooks/session-start/update.sh` | Auto-update logic using `.current-version` file |
| `plugin/rules/` | Symlink-free copy of all rules (copied from `src/.../rules/`) |
| `plugin/install.sh` | Unix two-step installer |
| `plugin/install.ps1` | Windows two-step installer |
| `plugin/README.md` | Quick-start guide for users |
| `plugin/.current-version` | Tracks installed tag (written by update hook) |

### Modified files

| File | Change |
|------|--------|
| `src/taleemabad_data_mcp/__main__.py` | Add `bump` subcommand |
| `src/taleemabad_data_mcp/cli.py` | Implement `bump` command (patch/minor version bump) |
| `CLAUDE.md` | Update rules path reference to new plugin location |
| `docs/INSTALL.md` | Add plugin installation section |
| `src/taleemabad_data_mcp/rules/` | Source of truth — `plugin/rules/` is synced from here on `bump` |

---

## Task 0: Verify plugin format from installed plugins

**Files:**
- Read only (no code written in this task)

Before scaffolding anything, confirm the exact Claude Code plugin format from real installed plugins. This is the "Critical prerequisite" from Spec Review Fix #1.

- [ ] **Step 1: Confirm manifest file path**

```bash
ls ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/.claude-plugin/
cat ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/.claude-plugin/plugin.json | python3 -m json.tool
```

Expected: file exists at `.claude-plugin/plugin.json` with `name`, `version`, `agents` fields.

- [ ] **Step 2: Confirm hooks variable name**

```bash
cat ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/hooks/hooks.json
```

Expected: `"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"` — confirms `CLAUDE_PLUGIN_ROOT` is the correct variable.

- [ ] **Step 3: Confirm agent frontmatter fields**

```bash
head -8 ~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/agents/code-reviewer.md
```

Expected: frontmatter has `name:`, `description:`, `model: inherit` — confirms `model: inherit` is valid.

- [ ] **Step 4: If format differs from above expectations**

If `.claude-plugin/plugin.json` does not exist or uses different field names: document the actual format, update Tasks 2 and 5 accordingly before proceeding.

**Verification results (pre-confirmed):**
- Manifest: `.claude-plugin/plugin.json` ✓
- Hooks variable: `${CLAUDE_PLUGIN_ROOT}` ✓
- Agent frontmatter: `model: inherit` valid ✓

---

## Task 1: Verify bigquery-analytics MCP candidate

**Files:**
- Read: (web search / npm registry only — no code changes)

Before writing any config that references `@ergut/bigquery-mcp`, verify it exists and has the right tools.

- [ ] **Step 1: Check npm for bigquery analytics MCP packages**

```bash
npx --yes @ergut/bigquery-mcp --version 2>/dev/null || echo "not found"
npm view @ergut/bigquery-mcp 2>/dev/null | head -20 || echo "not found"
```

- [ ] **Step 2: Check alternative packages**

```bash
npm view @modelcontextprotocol/server-bigquery 2>/dev/null | head -10 || echo "not found"
npm search bigquery mcp 2>/dev/null | head -20
```

- [ ] **Step 3: Decision — record result**

In `plugin/.mcp.json` task (Task 4), use whichever package exists. If none found, use `"bigquery-analytics": null` as a placeholder comment and document the fallback (Streamlit). Record the chosen package name in a comment in `plugin/README.md`.

---

## Task 2: Plugin scaffold

**Files:**
- Create: `plugin/.claude-plugin/plugin.json`
- Create: `plugin/package.json`
- Create: `plugin/.current-version`
- Create: `plugin/README.md`

- [ ] **Step 1: Create plugin directory skeleton**

```bash
mkdir -p plugin/.claude-plugin plugin/agents plugin/hooks/session-start plugin/rules
```

- [ ] **Step 2: Write plugin manifest**

Create `plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "taleemabad-data",
  "version": "1.0.0",
  "description": "Governed BigQuery analytics for Taleemabad — ICT/Islamabad and Rawalpindi regions. Enforces data governance rules, audit logging, and cost guardrails.",
  "author": {
    "name": "Orenda Project",
    "url": "https://github.com/Orenda-Project"
  },
  "homepage": "https://github.com/Orenda-Project/taleemabad-data-mcp",
  "repository": "https://github.com/Orenda-Project/taleemabad-data-mcp",
  "license": "MIT",
  "keywords": ["bigquery", "data-governance", "analytics", "taleemabad", "education"],
  "agents": [
    "./agents/data-analyst.md",
    "./agents/data-admin.md"
  ]
}
```

- [ ] **Step 3: Write package.json**

Create `plugin/package.json`:

```json
{
  "name": "taleemabad-data-plugin",
  "version": "1.0.0",
  "description": "Taleemabad Data Claude Code plugin",
  "license": "MIT",
  "private": true
}
```

- [ ] **Step 4: Write initial .current-version**

```bash
echo "v1.0.0" > plugin/.current-version
```

- [ ] **Step 5: Write README.md**

Create `plugin/README.md`:

````markdown
# Taleemabad Data Plugin

Governed BigQuery analytics for Claude Code. Enforces data governance, cost guardrails, and audit logging for Taleemabad data across ICT/Islamabad and Rawalpindi regions.

## Quick Install

**Unix (macOS/Linux):**
```bash
curl -sLO https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.sh
chmod +x install.sh && ./install.sh
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.ps1" -OutFile install.ps1
.\install.ps1
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (for analytics MCP)
- Git
- GCP service account key JSON file
- Claude Code installed

## What Gets Installed

- `~/.claude/plugins/taleemabad-data/` — plugin directory (this repo, cloned)
- `~/.claude/taleemabad-venv/` — dedicated Python venv with MCP server
- `~/.claude/taleemabad-data-mcp.env` — saved credentials and config

## Agents

- **data-analyst** — answers questions about teacher data, lesson plans, observations, training, student results
- **data-admin** — schema browsing, table freshness, audit log queries, cost analysis

## Auto-Update

Rules and agents update automatically each time Claude Code opens. To pin a version:
```bash
export TALEEMABAD_PIN_VERSION=v1.0.0
```

## Troubleshooting

Run `/data-admin` and ask "what version am I running?" for diagnostics.
````

- [ ] **Step 6: Commit scaffold**

```bash
git add plugin/
git commit -m "feat: add plugin scaffold (manifest, package.json, README)"
```

---

## Task 3: Agent definitions

**Files:**
- Create: `plugin/agents/data-analyst.md`
- Create: `plugin/agents/data-admin.md`

### data-analyst agent

- [ ] **Step 1: Write data-analyst agent**

Create `plugin/agents/data-analyst.md`:

````markdown
---
name: data-analyst
description: |
  Use this agent when the user asks ANY question about Taleemabad data — teacher counts,
  lesson plan usage, observation scores, training progress, student results, coaching metrics,
  or any data from ICT/Islamabad or Rawalpindi districts. Examples: "how many teachers passed
  level 1?", "show me LP completion rates this week", "what's the FICO score for school X?",
  "how many AI coaching sessions happened in RWP?". Use for ALL data queries. Do NOT use for
  schema browsing, setup help, or audit log queries — those go to data-admin.
model: inherit
---

You are the Taleemabad Data Analyst. You answer questions about Taleemabad education data by following strict governance rules, generating SQL, and executing queries through the taleemabad-data MCP server.

## Rules

Before answering any data question:
1. Read `rules/index.md` to determine the region and relevant rule file
2. Read the specific rule file for the domain (teachers, lesson_plans, coaching_observations, etc.)
3. Follow ALL mandatory clarifications defined in that rule file before generating SQL
4. Never generate ad-hoc SQL — only SQL that follows the rule definitions

## Query Flow

### Step 1: Read rules
- Always start by reading `rules/index.md`
- Determine region from user's question or ask: "Which region — ICT/Islamabad or Rawalpindi?"
- Read the relevant domain rule file

### Step 2: Clarify
Ask the mandatory clarification questions defined in the rule file. Common ones:
- Teacher queries: teacher level (PRIMARY/MIDDLE/SECONDARY) + region
- LP queries: academic session (2024-25 or 2025-26)
- Observation queries: section (B/C/D or all) + aggregation level
- Training queries: which level(s)
- Do NOT ask more than 3 rounds of clarification — escalate if unresolved

### Step 3: Generate SQL
- Follow the rule file's query patterns exactly
- Every query MUST have a partition filter (BigQuery rule — hard requirement)
- Use parameterized queries conceptually (the MCP handles actual parameterization)
- Use the canonical table hierarchy from bigquery.md (analytics_events > events_partitioned, NEVER analytics_analyticsevent)

### Step 4: Self-healing execute

```
Dry run first (cost check via execute_query with dry_run=True):
  If cost > BIGQUERY_MAX_BYTES: show estimated cost, ask user to confirm
  If syntax error: fix and retry once

Execute:
  Success + rows > 0: present results (go to Step 5)
  Success + zero rows: run COUNT(*) on base table with partition filter
    Data exists? → Filters too narrow, tell user, suggest broader range
    No data? → Table empty or partition missing, tell user
    Log VERIFICATION_WARNING via execute_query
  Error:
    Column not found → call get_table_schema, find correct column name, retry
    Table not found → call list_datasets, search for similar name, retry if found
    Syntax/type error → read error message, fix SQL, retry
    Permission denied → hard stop immediately, tell user, do not retry
    Log RULE_DRIFT if schema mismatch found

Max 2 retries total. After 2 failures:
  Stop retrying
  Tell user: what failed, what was tried, what to do next
  Log QUERY_FAILURE
```

### Step 5: Present results
Always include:
- The data (table or summary)
- Freshness: "Data from [table] — last modified [date]" (use check_table_freshness)
- Cost: "Query scanned ~X MB"
- Domain: which rule file was used
- Any caveats from the rule file (e.g., DRAFT status, CONFLICT status)

### Step 6: Optional analysis
If the user asks for trends, charts, correlation, or reports:
- Use bigquery-analytics MCP tools: `analyze_trends`, `find_correlations`, `detect_anomalies`, `generate_insights`, `create_dashboard`, `add_chart`, `add_metric_card`, `generate_html_report`, `export_dashboard`
- NEVER use bigquery-analytics for data retrieval — only for analysis of already-retrieved results
- NEVER call these bigquery-analytics tools: `execute_query`, `build_query`, `preview_table` — use taleemabad-data equivalents instead

### Step 7: Feedback
After presenting results, ask: "Was this helpful? (👍 / 👎 + optional comment)"
Call `submit_feedback` with their response.

## Ungoverned Requests

If `rules/index.md` has no matching domain for the user's question:
1. Tell user: "No governed query exists for '[their question]'. I can only run queries defined in the governance rules."
2. Offer: "Would you like me to check if relevant tables exist?" (routes to data-admin)
3. Log the gap: call `execute_query` with domain="UNGOVERNED_REQUEST" and a note in the query text
4. Never generate ad-hoc SQL

## What You Do NOT Do

- Generate SQL outside of rule definitions
- Browse schemas or run diagnostics (use data-admin)
- Help with installation or setup
- Query `tbproddb.analytics_analyticsevent` — it is banned (68.6 GB unpartitioned)
- Run queries without partition filters
- Serve stale cached data silently
````

- [ ] **Step 2: Write data-admin agent**

Create `plugin/agents/data-admin.md`:

````markdown
---
name: data-admin
description: |
  Use this agent when the user asks about: table schemas, table freshness or last-updated timestamps,
  audit log queries, query costs, data pipeline health, plugin version, setup or installation issues,
  or any diagnostic/investigative question about the data infrastructure. Examples: "when was
  coaching_observation last updated?", "what tables are in RUMI_DB?", "show me recent audit logs",
  "how much did yesterday's queries cost?", "what version of the plugin am I running?",
  "why is my query failing?". Do NOT use for answering data questions — use data-analyst for those.
model: inherit
---

You are the Taleemabad Data Admin. You provide diagnostics, schema browsing, audit analysis, and infrastructure health checks using the taleemabad-data MCP server tools.

## Capabilities

### Schema & Discovery
- `list_datasets` — browse available datasets and tables
- `get_table_schema` — get columns and types for a specific table
- Use for: "what columns does X table have?", "what tables are in RUMI_DB?", "does table X exist?"

### Freshness
- `check_table_freshness` — when was a table last modified
- Use for: "is X table up to date?", "when was coaching_observation last updated?", pipeline health checks

### Version & Identity
- `get_version` — returns plugin version, user name, project, configured datasets
- Use for: "what version am I running?", "who is this configured for?", setup verification

### Audit Log Queries
- Query `mcp_audit.activity_log` via `execute_query`
- Show recent query history, cost summaries, domain breakdowns, RULE_DRIFT events, UNGOVERNED_REQUEST gaps
- Always filter by `session_id` or `user_name` or date range — never pull the whole log

### Cost Analysis
- Query `mcp_audit.activity_log` for `bytes_processed` + `cost_usd` fields
- Aggregate by day, domain, or user
- Flag queries above threshold

### Troubleshooting
When a user reports a failing query:
1. Get the error message
2. Call `get_table_schema` on the referenced table
3. Check if the column/table referenced in the error exists
4. If RULE_DRIFT suspected: compare schema to rule file, report discrepancy
5. Suggest the fix (update rule file or adjust query)

## Rules for Admin Queries

- Audit log queries MUST have a date/session filter (partition rules apply)
- Report schema findings clearly: "Table X has column Y (type Z)" — don't guess
- When checking for table existence: use `list_datasets` first, then `get_table_schema`
- Permission errors: tell user exactly what dataset/table failed and what they should ask the data team
````

- [ ] **Step 3: Commit agents**

```bash
git add plugin/agents/
git commit -m "feat: add data-analyst and data-admin agent definitions"
```

---

## Task 4: MCP configuration

**Files:**
- Create: `plugin/.mcp.json`

This requires the result of Task 1 (which bigquery-analytics package exists).

- [ ] **Step 1: Write .mcp.json with taleemabad-data server**

Create `plugin/.mcp.json`. The `${TALEEMABAD_CREDENTIALS}` and `${TALEEMABAD_USER}` tokens are replaced by the install script when it copies this to `~/.claude/plugins/taleemabad-data/`:

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "${HOME}/.claude/taleemabad-venv/bin/python",
      "args": ["-m", "taleemabad_data_mcp", "serve"],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "${TALEEMABAD_CREDENTIALS}",
        "BIGQUERY_MAX_BYTES": "1073741824",
        "TALEEMABAD_USER": "${TALEEMABAD_USER}",
        "LOG_LEVEL": "INFO"
      }
    },
    "bigquery-analytics": {
      "command": "npx",
      "args": ["-y", "@ergut/bigquery-mcp@latest"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "${TALEEMABAD_CREDENTIALS}",
        "BIGQUERY_PROJECT": "niete-bq-prod"
      }
    }
  }
}
```

**Note:** If Task 1 found no valid bigquery-analytics package, replace the `bigquery-analytics` block with a comment explaining the fallback and remove it from the manifest's agent list.

- [ ] **Step 2: Validate JSON is well-formed**

```bash
python3 -m json.tool plugin/.mcp.json
```
Expected: prints formatted JSON with no errors.

- [ ] **Step 3: Commit**

```bash
git add plugin/.mcp.json
git commit -m "feat: add plugin MCP server configuration"
```

---

## Task 5: Auto-update hook

**Files:**
- Create: `plugin/hooks/hooks.json`
- Create: `plugin/hooks/run-hook.cmd`
- Create: `plugin/hooks/session-start/update.sh`

- [ ] **Step 1: Write session-start update script**

Create `plugin/hooks/session-start/update.sh`:

```bash
#!/usr/bin/env bash
# Auto-update Taleemabad Data Plugin on session start
# Uses .current-version file to avoid git describe / detached HEAD issues
# Set TALEEMABAD_PIN_VERSION env var to skip updates and stay on current version

PLUGIN_DIR="${HOME}/.claude/plugins/taleemabad-data"

# Respect pin — if user has pinned a version, skip update silently
if [ -n "$TALEEMABAD_PIN_VERSION" ]; then
  exit 0
fi

# Must be inside the plugin directory
if [ ! -d "$PLUGIN_DIR" ]; then
  exit 0
fi

cd "$PLUGIN_DIR" || exit 0

# Fetch latest tags quietly — if network fails, continue with current version
git fetch --tags --quiet 2>/dev/null || exit 0

# Find latest semantic version tag
LATEST=$(git tag -l 'v*' --sort=-v:refname 2>/dev/null | head -1)
CURRENT=$(cat .current-version 2>/dev/null || echo "none")

# No tags found — nothing to update
if [ -z "$LATEST" ]; then
  exit 0
fi

# Already on latest — nothing to do
if [ "$LATEST" = "$CURRENT" ]; then
  exit 0
fi

# Update to latest tag.
# NOTE: `git checkout <tag>` intentionally creates a detached HEAD — this is expected.
# The plugin directory is a read-only, auto-managed clone. Version tracking uses
# .current-version, not git describe. "HEAD detached at v1.0.0" in this dir is normal.
git checkout "$LATEST" --quiet 2>/dev/null
if [ $? -eq 0 ]; then
  echo "$LATEST" > .current-version
  # Reinstall Python package after update
  "${HOME}/.claude/taleemabad-venv/bin/pip" install \
    --quiet --force-reinstall \
    "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@${LATEST}" 2>/dev/null
  echo "[Taleemabad Data] Updated to ${LATEST}"
fi
```

- [ ] **Step 2: Make script executable**

```bash
chmod +x plugin/hooks/session-start/update.sh
```

- [ ] **Step 3: Write hooks.json**

Create `plugin/hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start",
            "async": true
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Write run-hook.cmd (Windows shim)**

Create `plugin/hooks/run-hook.cmd`:

```cmd
@echo off
REM Windows shim to run session-start hook
REM Mirrors the pattern used by superpowers plugin
set "HOOK_DIR=%~dp0%1"
if exist "%HOOK_DIR%\update.sh" (
  bash "%HOOK_DIR%\update.sh"
)
```

- [ ] **Step 5: Commit hooks**

```bash
git add plugin/hooks/
git commit -m "feat: add session-start auto-update hook"
```

---

## Task 6: Sync rules into plugin directory

The `plugin/rules/` directory must be a copy of `src/taleemabad_data_mcp/rules/`. This is done at install time and on `bump`.

- [ ] **Step 1: Copy rules to plugin/**

```bash
cp -r src/taleemabad_data_mcp/rules/. plugin/rules/
```

- [ ] **Step 2: Verify all rule files present**

```bash
find plugin/rules/ -name "*.md" | sort
```

Expected output: all 13+ rule files (index.md, bigquery.md, caching.md, data-governance.md, failure-handling.md, observability.md, versioning.md + ict-islamabad/* + rawalpindi/*).

- [ ] **Step 3: Commit rules**

```bash
git add plugin/rules/
git commit -m "feat: sync governance rules into plugin directory"
```

---

## Task 7: Unix install script

**Files:**
- Create: `plugin/install.sh`

- [ ] **Step 1: Write install.sh**

Create `plugin/install.sh`:

```bash
#!/usr/bin/env bash
# Taleemabad Data Plugin — Unix Installer
# Two-step install (download script, then run) — not curl|bash
set -e

REPO="https://github.com/Orenda-Project/taleemabad-data-mcp.git"
PLUGIN_DIR="${HOME}/.claude/plugins/taleemabad-data"
VENV_DIR="${HOME}/.claude/taleemabad-venv"
ENV_FILE="${HOME}/.claude/taleemabad-data-mcp.env"

echo ""
echo "=== Taleemabad Data Plugin Installer ==="
echo ""

# --- Prerequisites check ---
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found. Install Python 3.11+"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "ERROR: git not found. Install git"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "WARN: node not found. bigquery-analytics MCP will not work."; }

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
  echo "✓ Python ${PYTHON_VERSION}"
else
  echo "ERROR: Python 3.11+ required. Found ${PYTHON_VERSION}"; exit 1
fi

# --- Detect existing install ---
if [ -d "$PLUGIN_DIR" ]; then
  echo "Existing install detected at ${PLUGIN_DIR}"
  echo "Running upgrade instead..."
  cd "$PLUGIN_DIR"
  git fetch --tags --quiet
  LATEST=$(git tag -l 'v*' --sort=-v:refname | head -1)
  git checkout "${LATEST:-main}" --quiet
  [ -n "$LATEST" ] && echo "$LATEST" > .current-version
  "${VENV_DIR}/bin/pip" install --quiet --force-reinstall \
    "git+${REPO}@${LATEST:-main}[dashboard]"
  # Re-substitute .mcp.json in case template changed in this release
  if [ -f "$ENV_FILE" ]; then
    SAVED_USER=$(grep '^TALEEMABAD_USER=' "$ENV_FILE" | cut -d= -f2-)
    SAVED_CREDS=$(grep '^GOOGLE_APPLICATION_CREDENTIALS=' "$ENV_FILE" | cut -d= -f2-)
    if [ -n "$SAVED_USER" ] && [ -n "$SAVED_CREDS" ]; then
      sed -e "s|\${HOME}|${HOME}|g" \
          -e "s|\${TALEEMABAD_CREDENTIALS}|${SAVED_CREDS}|g" \
          -e "s|\${TALEEMABAD_USER}|${SAVED_USER}|g" \
          "${PLUGIN_DIR}/plugin/.mcp.json" > "${PLUGIN_DIR}/.mcp.json"
      echo "✓ MCP config refreshed"
    fi
  fi
  echo "✓ Upgraded to ${LATEST:-latest}"
  exit 0
fi

# --- Detect old rules-based setup ---
OLD_RULES="${HOME}/.claude/rules/taleemabad"
if [ -d "$OLD_RULES" ]; then
  echo ""
  echo "Old setup detected at ~/.claude/rules/taleemabad/"
  read -p "Migrate to plugin? Old rules will be removed. [y/N] " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    MIGRATE_OLD=true
  fi
fi

# --- Clone plugin ---
echo "Cloning plugin to ${PLUGIN_DIR}..."
git clone --quiet "$REPO" "$PLUGIN_DIR"
cd "$PLUGIN_DIR"
LATEST=$(git tag -l 'v*' --sort=-v:refname | head -1)
if [ -n "$LATEST" ]; then
  git checkout "$LATEST" --quiet
  echo "$LATEST" > .current-version
  echo "✓ Pinned to ${LATEST}"
fi

# --- Create venv ---
echo "Creating Python venv at ${VENV_DIR}..."
python3 -m venv "$VENV_DIR"
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip

# --- Install MCP server ---
echo "Installing taleemabad-data-mcp..."
"${VENV_DIR}/bin/pip" install --quiet \
  "git+${REPO}@${LATEST:-main}[dashboard]"
echo "✓ MCP server installed"

# --- Prompt for credentials ---
echo ""
echo "=== Configuration ==="
read -p "Your name (for audit logs): " TALEEMABAD_USER
read -e -p "Path to GCP service account JSON: " CREDENTIALS_PATH
CREDENTIALS_PATH="${CREDENTIALS_PATH/#\~/$HOME}"

if [ ! -f "$CREDENTIALS_PATH" ]; then
  echo "ERROR: File not found: ${CREDENTIALS_PATH}"; exit 1
fi

# --- Save config ---
cat > "$ENV_FILE" << EOF
TALEEMABAD_USER=${TALEEMABAD_USER}
GOOGLE_APPLICATION_CREDENTIALS=${CREDENTIALS_PATH}
EOF
chmod 600 "$ENV_FILE"
echo "✓ Config saved to ${ENV_FILE}"

# --- Write final .mcp.json with substituted values ---
sed -e "s|\${HOME}|${HOME}|g" \
    -e "s|\${TALEEMABAD_CREDENTIALS}|${CREDENTIALS_PATH}|g" \
    -e "s|\${TALEEMABAD_USER}|${TALEEMABAD_USER}|g" \
    "${PLUGIN_DIR}/plugin/.mcp.json" > "${PLUGIN_DIR}/.mcp.json"
echo "✓ MCP config written"

# --- Migrate old setup ---
if [ "${MIGRATE_OLD}" = "true" ]; then
  rm -rf "$OLD_RULES"
  echo "✓ Removed old rules at ~/.claude/rules/taleemabad/"
  # TODO: remove taleemabad-data key from ~/.claude/settings.json
  # (Manual step — settings.json editing is complex and user-specific)
  echo "ACTION REQUIRED: Remove the 'taleemabad-data' key from ~/.claude/settings.json manually"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Plugin installed at: ${PLUGIN_DIR}"
echo "Version: ${LATEST:-latest}"
echo ""
echo "Restart Claude Code to activate the plugin."
echo "Ask 'what version of taleemabad data am I running?' to verify."
```

- [ ] **Step 2: Make executable**

```bash
chmod +x plugin/install.sh
```

- [ ] **Step 3: Smoke test dry run (no actual install)**

```bash
bash -n plugin/install.sh
```
Expected: no errors (syntax check only).

- [ ] **Step 4: Commit**

```bash
git add plugin/install.sh
git commit -m "feat: add Unix install script"
```

---

## Task 8: Windows install script

**Files:**
- Create: `plugin/install.ps1`

- [ ] **Step 1: Write install.ps1**

Create `plugin/install.ps1`:

```powershell
# Taleemabad Data Plugin — Windows PowerShell Installer
# Two-step install: download this file, then run it
# Usage: .\install.ps1
param()
$ErrorActionPreference = "Stop"

$REPO = "https://github.com/Orenda-Project/taleemabad-data-mcp.git"
$PLUGIN_DIR = "$env:USERPROFILE\.claude\plugins\taleemabad-data"
$VENV_DIR = "$env:USERPROFILE\.claude\taleemabad-venv"
$ENV_FILE = "$env:USERPROFILE\.claude\taleemabad-data-mcp.env"

Write-Host ""
Write-Host "=== Taleemabad Data Plugin Installer ===" -ForegroundColor Cyan
Write-Host ""

# --- Prerequisites check ---
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python not found. Install Python 3.11+ from python.org"
    exit 1
}
$pythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$pyOk = & python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>$null; $pyOkCode = $LASTEXITCODE
if ($pyOkCode -ne 0) {
    Write-Error "Python 3.11+ required. Found $pythonVersion"
    exit 1
}
Write-Host "✓ Python $pythonVersion"

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) { Write-Error "git not found. Install Git for Windows."; exit 1 }
Write-Host "✓ git"

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) { Write-Warning "node not found. bigquery-analytics MCP will not work." }

# --- Detect existing install ---
if (Test-Path $PLUGIN_DIR) {
    Write-Host "Existing install found at $PLUGIN_DIR — running upgrade..."
    Set-Location $PLUGIN_DIR
    git fetch --tags --quiet
    $LATEST = (git tag -l 'v*' --sort=-v:refname | Select-Object -First 1)
    if ($LATEST) { git checkout $LATEST --quiet; Set-Content .current-version $LATEST }
    & "$VENV_DIR\Scripts\pip" install --quiet --force-reinstall "git+${REPO}@${LATEST}"
    # Re-substitute .mcp.json in case template changed in this release
    if (Test-Path $ENV_FILE) {
        $envContent = Get-Content $ENV_FILE | ForEach-Object {
            $parts = $_ -split '=', 2; [PSCustomObject]@{Key=$parts[0]; Value=$parts[1]}
        }
        $savedUser = ($envContent | Where-Object Key -eq 'TALEEMABAD_USER').Value
        $savedCreds = ($envContent | Where-Object Key -eq 'GOOGLE_APPLICATION_CREDENTIALS').Value
        if ($savedUser -and $savedCreds) {
            $winPython = "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -replace '\\', '\\\\'
            $mcpTemplate = Get-Content "$PLUGIN_DIR\plugin\.mcp.json" -Raw
            $mcpFinal = $mcpTemplate `
                -replace [regex]::Escape('${HOME}/.claude/taleemabad-venv/bin/python'), $winPython `
                -replace '\$\{HOME\}', ($env:USERPROFILE -replace '\\', '\\\\') `
                -replace '\$\{TALEEMABAD_CREDENTIALS\}', ($savedCreds -replace '\\', '\\\\') `
                -replace '\$\{TALEEMABAD_USER\}', $savedUser
            $mcpFinal | Set-Content "$PLUGIN_DIR\.mcp.json"
            Write-Host "✓ MCP config refreshed"
        }
    }
    Write-Host "✓ Upgraded to $LATEST"
    exit 0
}

# --- Clone plugin ---
Write-Host "Cloning plugin to $PLUGIN_DIR..."
git clone --quiet $REPO $PLUGIN_DIR
Set-Location $PLUGIN_DIR
$LATEST = (git tag -l 'v*' --sort=-v:refname | Select-Object -First 1)
if ($LATEST) {
    git checkout $LATEST --quiet
    Set-Content .current-version $LATEST
    Write-Host "✓ Pinned to $LATEST"
}

# --- Create venv ---
Write-Host "Creating Python venv at $VENV_DIR..."
python -m venv $VENV_DIR
& "$VENV_DIR\Scripts\pip" install --quiet --upgrade pip

# --- Install MCP server ---
Write-Host "Installing taleemabad-data-mcp..."
$installTag = if ($LATEST) { $LATEST } else { "main" }
& "$VENV_DIR\Scripts\pip" install --quiet "git+${REPO}@${installTag}[dashboard]"
Write-Host "✓ MCP server installed"

# --- Prompt for credentials ---
Write-Host ""
Write-Host "=== Configuration ===" -ForegroundColor Cyan
$TALEEMABAD_USER = Read-Host "Your name (for audit logs)"
$CREDENTIALS_PATH = Read-Host "Path to GCP service account JSON"
$CREDENTIALS_PATH = $CREDENTIALS_PATH -replace "~", $env:USERPROFILE

if (-not (Test-Path $CREDENTIALS_PATH)) {
    Write-Error "File not found: $CREDENTIALS_PATH"
    exit 1
}

# --- Save config ---
"TALEEMABAD_USER=$TALEEMABAD_USER`nGOOGLE_APPLICATION_CREDENTIALS=$CREDENTIALS_PATH" | Set-Content $ENV_FILE
Write-Host "✓ Config saved to $ENV_FILE"

# --- Write final .mcp.json with substituted values ---
# On Windows, replace the Unix venv path pattern with the Windows equivalent
$winPython = "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -replace '\\', '\\\\'
$mcpTemplate = Get-Content "$PLUGIN_DIR\plugin\.mcp.json" -Raw
$mcpFinal = $mcpTemplate `
    -replace [regex]::Escape('${HOME}/.claude/taleemabad-venv/bin/python'), $winPython `
    -replace '\$\{HOME\}', ($env:USERPROFILE -replace '\\', '\\\\') `
    -replace '\$\{TALEEMABAD_CREDENTIALS\}', ($CREDENTIALS_PATH -replace '\\', '\\\\') `
    -replace '\$\{TALEEMABAD_USER\}', $TALEEMABAD_USER
$mcpFinal | Set-Content "$PLUGIN_DIR\.mcp.json"
Write-Host "✓ MCP config written"

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Plugin installed at: $PLUGIN_DIR"
Write-Host "Version: $LATEST"
Write-Host ""
Write-Host "Restart Claude Code to activate the plugin."
Write-Host "Ask 'what version of taleemabad data am I running?' to verify."
```

- [ ] **Step 2: Syntax check**

```powershell
# Run from PowerShell to syntax-check (no actual install)
powershell -Command "& { [scriptblock]::Create((Get-Content plugin\install.ps1 -Raw)) | Out-Null; Write-Host 'Syntax OK' }"
```

Or just visually verify the script is well-formed before committing.

- [ ] **Step 3: Commit**

```bash
git add plugin/install.ps1
git commit -m "feat: add Windows PowerShell install script"
```

---

## Task 9: `bump` CLI command

The `bump` command must: (a) increment the version in `__init__.py` + `pyproject.toml`, and (b) sync `plugin/rules/` from `src/.../rules/`, (c) update `plugin/.claude-plugin/plugin.json` version, and (d) update `plugin/.current-version`.

**Files:**
- Modify: `src/taleemabad_data_mcp/cli.py`
- Modify: `src/taleemabad_data_mcp/__main__.py`
- Create: `tests/test_bump.py`

- [ ] **Step 1: Read existing cli.py**

```bash
cat src/taleemabad_data_mcp/cli.py
```

Understand the current CLI structure before modifying.

- [ ] **Step 2: Read existing __main__.py**

```bash
cat src/taleemabad_data_mcp/__main__.py
```

- [ ] **Step 3: Read existing __init__.py for version format**

```bash
cat src/taleemabad_data_mcp/__init__.py
```

- [ ] **Step 4: Write the failing tests FIRST (TDD)**

Create `tests/test_bump.py`:

```python
"""Tests for bump_version CLI function — TDD: write tests before implementation."""
import re
import json
import shutil
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def fake_repo(tmp_path):
    """Create a minimal fake repo structure for testing bump_version."""
    src = tmp_path / "src" / "taleemabad_data_mcp"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text('__version__ = "0.4.8"\n')

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "taleemabad-data-mcp"
        version = "0.4.8"
    """))

    # Create source rules (what bump_version copies FROM)
    rules = src / "rules"
    rules.mkdir()
    (rules / "index.md").write_text("# Rules Index\n")
    (rules / "bigquery.md").write_text("# BigQuery\n")

    # Create plugin directory (what bump_version writes TO)
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / ".current-version").write_text("v0.4.8\n")

    manifest_dir = plugin_dir / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(
        json.dumps({"name": "taleemabad-data", "version": "0.4.8"}) + "\n"
    )

    # Existing plugin/rules with stale content (should be replaced by bump)
    plugin_rules = plugin_dir / "rules"
    plugin_rules.mkdir()
    (plugin_rules / "old-stale.md").write_text("stale content\n")

    return tmp_path


def _call_bump(fake_repo, minor=False):
    """Call bump_version with fake_repo as the project root."""
    from taleemabad_data_mcp.cli import bump_version
    # Patch Path(__file__).parent inside bump_version to point at fake_repo/src/taleemabad_data_mcp
    fake_cli_file = fake_repo / "src" / "taleemabad_data_mcp" / "cli.py"
    with patch("taleemabad_data_mcp.cli.__file__", str(fake_cli_file)):
        bump_version(minor=minor)


def test_patch_bump_updates_init(fake_repo):
    _call_bump(fake_repo, minor=False)
    text = (fake_repo / "src" / "taleemabad_data_mcp" / "__init__.py").read_text()
    assert '__version__ = "0.4.9"' in text


def test_minor_bump_updates_init(fake_repo):
    _call_bump(fake_repo, minor=True)
    text = (fake_repo / "src" / "taleemabad_data_mcp" / "__init__.py").read_text()
    assert '__version__ = "0.5.0"' in text


def test_bump_updates_pyproject(fake_repo):
    _call_bump(fake_repo, minor=False)
    text = (fake_repo / "pyproject.toml").read_text()
    assert 'version = "0.4.9"' in text


def test_bump_syncs_rules_to_plugin(fake_repo):
    """After bump, plugin/rules/ should contain src rules, not stale content."""
    _call_bump(fake_repo, minor=False)
    plugin_rules = fake_repo / "plugin" / "rules"
    assert (plugin_rules / "index.md").exists()
    assert (plugin_rules / "bigquery.md").exists()
    # Old stale file should be gone (directory was replaced)
    assert not (plugin_rules / "old-stale.md").exists()


def test_bump_updates_plugin_manifest_version(fake_repo):
    _call_bump(fake_repo, minor=False)
    manifest = json.loads(
        (fake_repo / "plugin" / ".claude-plugin" / "plugin.json").read_text()
    )
    assert manifest["version"] == "0.4.9"


def test_bump_updates_current_version_file(fake_repo):
    _call_bump(fake_repo, minor=False)
    content = (fake_repo / "plugin" / ".current-version").read_text().strip()
    assert content == "v0.4.9"
```

- [ ] **Step 5: Run tests to confirm they FAIL (expected)**

```bash
uv run pytest tests/test_bump.py -v
```
Expected: all tests FAIL with `ImportError` or `AttributeError` — `bump_version` doesn't exist yet.

- [ ] **Step 6: Add bump function to cli.py**

In `src/taleemabad_data_mcp/cli.py`, add this function (after existing imports):

```python
def bump_version(minor: bool = False) -> None:
    """Bump package version (patch or minor) and sync plugin rules."""
    import re
    import shutil
    from pathlib import Path

    repo_root = Path(__file__).parent.parent.parent  # src/../..
    init_file = Path(__file__).parent / "__init__.py"
    pyproject_file = repo_root / "pyproject.toml"
    plugin_rules_dir = repo_root / "plugin" / "rules"
    src_rules_dir = Path(__file__).parent / "rules"

    # --- Read current version from __init__.py ---
    init_text = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    if not match:
        raise RuntimeError("Could not find __version__ in __init__.py")
    current = match.group(1)
    major, minor_v, patch = current.split(".")

    # --- Compute new version ---
    if minor:
        new_version = f"{major}.{int(minor_v) + 1}.0"
    else:
        new_version = f"{major}.{minor_v}.{int(patch) + 1}"

    # --- Update __init__.py ---
    new_init = re.sub(
        r'(__version__\s*=\s*)["\'][^"\']+["\']',
        f'\\1"{new_version}"',
        init_text
    )
    init_file.write_text(new_init)

    # --- Update pyproject.toml ---
    if pyproject_file.exists():
        toml_text = pyproject_file.read_text()
        new_toml = re.sub(
            r'(version\s*=\s*)["\'][^"\']+["\']',
            f'\\1"{new_version}"',
            toml_text,
            count=1
        )
        pyproject_file.write_text(new_toml)

    # --- Sync plugin/rules/ from src ---
    if src_rules_dir.exists():
        if plugin_rules_dir.exists():
            shutil.rmtree(plugin_rules_dir)
        shutil.copytree(src_rules_dir, plugin_rules_dir)
        print(f"✓ Synced rules to plugin/rules/")

    # --- Update plugin manifest version ---
    plugin_json = repo_root / "plugin" / ".claude-plugin" / "plugin.json"
    if plugin_json.exists():
        import json
        manifest = json.loads(plugin_json.read_text())
        manifest["version"] = new_version
        plugin_json.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"✓ Updated plugin/manifest version to {new_version}")

    # --- Update plugin/.current-version ---
    current_version_file = repo_root / "plugin" / ".current-version"
    if current_version_file.exists():
        current_version_file.write_text(f"v{new_version}\n")

    print(f"✓ Version bumped: {current} → {new_version}")
    print(f"  Next: git add -A && git commit -m 'chore: bump version to v{new_version}' && git push && git tag v{new_version} && git push --tags")
```

- [ ] **Step 7: Wire bump into __main__.py**

In `src/taleemabad_data_mcp/__main__.py`, add a `bump` subcommand to the argument parser:

```python
# In the argparse section, add:
bump_parser = subparsers.add_parser("bump", help="Bump version and sync plugin rules")
bump_parser.add_argument("--minor", action="store_true", help="Bump minor version instead of patch")

# In the dispatch section, add:
elif args.command == "bump":
    from .cli import bump_version
    bump_version(minor=getattr(args, "minor", False))
```

- [ ] **Step 8: Run tests to confirm they PASS**

```bash
uv run pytest tests/test_bump.py -v
```
Expected: all 6 tests PASS.

- [ ] **Step 9: Commit**

```bash
git add src/taleemabad_data_mcp/cli.py src/taleemabad_data_mcp/__main__.py tests/test_bump.py
git commit -m "feat: add bump CLI command with rules sync"
```

---

## Task 10: Update documentation

Update `CLAUDE.md`, versioning rules, and `docs/INSTALL.md` to reflect the new plugin setup.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `src/taleemabad_data_mcp/rules/versioning.md`
- Modify: `.claude/rules/versioning.md`
- Modify: `docs/INSTALL.md`

- [ ] **Step 1: Update CLAUDE.md push workflow**

In `CLAUDE.md`, verify `python -m taleemabad_data_mcp bump` is in the Push Workflow section. If not, add it before `git push`.

- [ ] **Step 2: Update versioning.md rules**

In both `src/taleemabad_data_mcp/rules/versioning.md` and `.claude/rules/versioning.md`, add after the Push Workflow section:

```markdown
## What `bump` Does

Running `python -m taleemabad_data_mcp bump` also:
- Syncs `plugin/rules/` from `src/taleemabad_data_mcp/rules/` (ensures plugin ships latest rules)
- Updates `plugin/.claude-plugin/plugin.json` version field
- Updates `plugin/.current-version`
```

- [ ] **Step 3: Add plugin installation section to docs/INSTALL.md**

In `docs/INSTALL.md`, add a new section "## Installing as a Claude Code Plugin" with:

```markdown
## Installing as a Claude Code Plugin

The recommended installation method for team members is the one-command plugin installer.
This installs the plugin globally in Claude Code and auto-updates rules on every session start.

### Unix (macOS/Linux)
```bash
curl -sLO https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.sh
chmod +x install.sh && ./install.sh
```

### Windows (PowerShell)
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.ps1" -OutFile install.ps1
.\install.ps1
```

### Prerequisites
- Python 3.11+, Git, Node.js 18+ (for analytics MCP), GCP service account JSON, Claude Code

### Migrating from Manual Setup

If you previously installed via the manual setup (rules in `~/.claude/rules/taleemabad/`):

1. Run the install script above — it detects the old setup and offers to migrate
2. If not auto-removed: `rm -rf ~/.claude/rules/taleemabad/`
3. Edit `~/.claude/settings.json` — remove the `taleemabad-data` key from `mcpServers`
4. Restart Claude Code
5. Verify: ask "what version of taleemabad data am I running?"

### Pinning a Version

To prevent auto-updates:
```bash
export TALEEMABAD_PIN_VERSION=v1.0.0
```
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md src/taleemabad_data_mcp/rules/versioning.md .claude/rules/versioning.md docs/INSTALL.md
git commit -m "docs: update versioning rules and add plugin installation guide"
```

---

## Task 11: End-to-end smoke test

Verify the plugin can be loaded by Claude Code in a local test.

- [ ] **Step 1: Validate plugin JSON files**

```bash
python3 -m json.tool plugin/.claude-plugin/plugin.json
python3 -m json.tool plugin/.mcp.json
python3 -m json.tool plugin/hooks/hooks.json
python3 -m json.tool plugin/package.json
```
Expected: all print formatted JSON without errors.

- [ ] **Step 2: Validate agent markdown frontmatter**

```bash
python3 -c "
import re
for f in ['plugin/agents/data-analyst.md', 'plugin/agents/data-admin.md']:
    text = open(f).read()
    assert text.startswith('---'), f'{f} missing frontmatter'
    end = text.index('---', 3)
    front = text[3:end]
    assert 'name:' in front, f'{f} missing name'
    assert 'description:' in front, f'{f} missing description'
    print(f'✓ {f}')
"
```
Expected: both files print ✓.

- [ ] **Step 3: Verify plugin rules are present**

```bash
python3 -c "
from pathlib import Path
rules = list(Path('plugin/rules').rglob('*.md'))
assert len(rules) >= 13, f'Expected 13+ rules, found {len(rules)}'
print(f'✓ {len(rules)} rule files in plugin/rules/')
"
```

- [ ] **Step 4: Verify update script is executable**

```bash
[ -x plugin/hooks/session-start/update.sh ] && echo "✓ executable" || echo "FAIL: not executable"
```

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest --tb=short
```
Expected: all tests PASS, no regressions.

- [ ] **Step 6: Bump version and final commit**

```bash
python -m taleemabad_data_mcp bump --minor
git add -A
git commit -m "chore: bump version for plugin release"
git push origin master && git push origin master:main
```

---

## Migration Reference

For users already running the old setup, document this checklist in `docs/INSTALL.md` under a "Migrating from manual setup" section:

1. Run `install.sh` (detects old setup, offers to remove it)
2. If not auto-removed: `rm -rf ~/.claude/rules/taleemabad/`
3. Edit `~/.claude/settings.json` — remove the `taleemabad-data` key from `mcpServers`
4. Restart Claude Code
5. Verify: ask "what version of taleemabad data am I running?"

---

## Assumptions & Risks

| Risk | Mitigation |
|------|-----------|
| `@ergut/bigquery-mcp` doesn't exist or lacks needed tools | Task 1 verifies; fallback to Streamlit documented |
| Claude Code plugin API changes | Using verified format from 3 installed plugins (superpowers, ECC, claude-hud) |
| Windows path separator in .mcp.json | install.ps1 double-escapes backslashes in JSON |
| Auto-update breaks running session | Hook is async, runs at SessionStart only |
| Permission errors on Railway | Unaffected — plugin is local Claude Code only |

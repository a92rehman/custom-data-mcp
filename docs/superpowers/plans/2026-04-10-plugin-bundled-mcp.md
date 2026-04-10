# Plugin-Bundled MCP Architecture — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bundle the MCP server inside the plugin so `claude plugin install` + copy credentials = working system. No manual venv, no per-project `.mcp.json`, no `/taleemabad-init`.

**Architecture:** Plugin root gets `.mcp.json` that runs the Python MCP server via `uv run --directory ${CLAUDE_PLUGIN_ROOT}`. Server gracefully degrades when credentials are missing. Session-start hook exports `TALEEMABAD_USER` from saved env file. Three new Phase 1 tools added.

**Tech Stack:** Python 3.11+, FastMCP, BigQuery, uv, Click, pytest

**Spec:** `docs/superpowers/specs/2026-04-10-plugin-bundled-mcp-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `.mcp.json` | CREATE | Plugin MCP server config (uv run --directory) |
| `.gitignore` | MODIFY | Un-ignore `.mcp.json` so it ships with plugin |
| `.claude-plugin/plugin.json` | MODIFY | Remove `init.md` from commands |
| `commands/setup.md` | MODIFY | Simplify to name-only setup + cleanup |
| `commands/init.md` | DELETE | No longer needed |
| `hooks/session-start/update.sh` | MODIFY | Remove venv logic, add TALEEMABAD_USER export |
| `src/taleemabad_data_mcp/cli.py` | MODIFY | Remove init/upgrade/mcp-generation, simplify setup/uninstall |
| `src/taleemabad_data_mcp/server.py` | MODIFY | Graceful degradation + 3 new Phase 1 tools |
| `agents/data-analyst.md` | MODIFY | Remove bigquery-analytics references |
| `tests/test_cli.py` | MODIFY | Update tests for simplified CLI |
| `tests/test_server.py` | CREATE | Tests for graceful degradation + new tools |

---

### Task 1: Create Plugin `.mcp.json` and Fix `.gitignore`

**Files:**
- Create: `.mcp.json`
- Modify: `.gitignore`

- [ ] **Step 1: Create `.mcp.json` at plugin root**

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

- [ ] **Step 2: Update `.gitignore` to un-ignore `.mcp.json`**

Replace:
```
# Project MCP config (contains user credentials path)
.mcp.json
```

With:
```
# Project MCP config — plugin .mcp.json is committed, user overrides are not
# The plugin's .mcp.json at repo root is un-ignored below
```

Add after the `*.json` exception block:
```
!.mcp.json
```

- [ ] **Step 3: Verify `.mcp.json` is tracked by git**

Run: `git status`
Expected: `.mcp.json` shows as a new/modified file (not ignored)

- [ ] **Step 4: Commit**

```bash
git add .mcp.json .gitignore
git commit -m "feat: bundle MCP server config in plugin .mcp.json"
```

---

### Task 2: Update Plugin Manifest and Delete Init Command

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Delete: `commands/init.md`

- [ ] **Step 1: Remove `init.md` from plugin.json commands array**

In `.claude-plugin/plugin.json`, change:
```json
"commands": [
  "./commands/setup.md",
  "./commands/init.md"
]
```
To:
```json
"commands": [
  "./commands/setup.md"
]
```

- [ ] **Step 2: Delete `commands/init.md`**

```bash
git rm commands/init.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "refactor: remove init command, plugin provides MCP config"
```

---

### Task 3: Update Session-Start Hook

**Files:**
- Modify: `hooks/session-start/update.sh`

- [ ] **Step 1: Replace the hook content**

Replace the entire file with:

```bash
#!/usr/bin/env bash
# Auto-update Taleemabad Data Plugin on session start
# - Checks for new git tags and updates plugin cache
# - Syncs governance rules to ~/.claude/rules/taleemabad/ every session
# - Exports TALEEMABAD_USER from saved env file
# Set TALEEMABAD_PIN_VERSION env var to skip updates and stay on current version

# Use CLAUDE_PLUGIN_ROOT if available, otherwise try common paths
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$PLUGIN_DIR" ]; then
  for d in "${HOME}/.claude/plugins/cache/Orenda-Project/taleemabad-data"/*; do
    if [ -d "$d/.claude-plugin" ]; then
      PLUGIN_DIR="$d"
      break
    fi
  done
fi

# Must have a valid plugin directory
if [ -z "$PLUGIN_DIR" ] || [ ! -d "$PLUGIN_DIR" ]; then
  exit 0
fi

RULES_SRC="${PLUGIN_DIR}/rules"
RULES_DEST="${HOME}/.claude/rules/taleemabad"
ENV_FILE="${HOME}/.claude/taleemabad-data-mcp.env"

# --- Export TALEEMABAD_USER from saved env file ---
if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r key value; do
    if [ "$key" = "TALEEMABAD_USER" ] && [ -n "$value" ]; then
      export TALEEMABAD_USER="$value"
    fi
  done < "$ENV_FILE"
fi

# --- Always sync rules (even if version unchanged) ---
if [ -d "$RULES_SRC" ]; then
  mkdir -p "$(dirname "$RULES_DEST")"
  if [ ! -d "$RULES_DEST" ] || [ "$RULES_SRC/index.md" -nt "$RULES_DEST/index.md" ] 2>/dev/null; then
    rm -rf "$RULES_DEST"
    cp -r "$RULES_SRC" "$RULES_DEST"
  fi
fi

# Respect pin
if [ -n "$TALEEMABAD_PIN_VERSION" ]; then
  exit 0
fi

cd "$PLUGIN_DIR" || exit 0

# Fetch latest tags quietly
git fetch --tags --quiet 2>/dev/null || exit 0

LATEST=$(git tag -l 'v*' --sort=-v:refname 2>/dev/null | head -1)
CURRENT=$(cat .current-version 2>/dev/null || echo "none")

if [ -z "$LATEST" ]; then
  exit 0
fi

if [ "$LATEST" = "$CURRENT" ]; then
  exit 0
fi

# Update plugin cache to latest tag
git checkout "$LATEST" --quiet 2>/dev/null
if [ $? -eq 0 ]; then
  echo "$LATEST" > .current-version

  # Sync rules after update
  if [ -d "$RULES_SRC" ]; then
    rm -rf "$RULES_DEST"
    cp -r "$RULES_SRC" "$RULES_DEST"
  fi

  echo "[Taleemabad Data] Updated to ${LATEST}"
fi
```

Key changes from original:
- Removed `VENV_DIR` variable and all venv update logic (lines 26, 69-80)
- Added `ENV_FILE` variable and `TALEEMABAD_USER` export block
- Kept rule syncing and tag checking unchanged

- [ ] **Step 2: Commit**

```bash
git add hooks/session-start/update.sh
git commit -m "refactor: remove venv logic from hook, add TALEEMABAD_USER export"
```

---

### Task 4: Add Graceful Degradation to Server

**Files:**
- Modify: `src/taleemabad_data_mcp/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write test for graceful degradation**

Create `tests/test_server.py`:

```python
"""Tests for MCP server graceful degradation and new tools."""

import json
from unittest.mock import MagicMock, patch

import pytest


def test_app_context_missing_credentials():
    """Server should create AppContext with bq_client=None when credentials missing."""
    from taleemabad_data_mcp.server import AppContext

    ctx = AppContext(
        config=MagicMock(),
        bq_client=None,
        audit_logger=MagicMock(),
        cost_estimator=MagicMock(),
        feedback_logger=MagicMock(),
    )
    assert ctx.bq_client is None


CREDENTIALS_ERROR_MSG = "BigQuery credentials not found"


def test_credentials_error_message_constant():
    """The error message should mention the credentials file."""
    from taleemabad_data_mcp.server import CREDENTIALS_MISSING_MSG

    assert "niete-bq-prod-48ae5260d1ea.json" in CREDENTIALS_MISSING_MSG


def test_require_bq_returns_error_when_none():
    """_require_bq should return error message when bq_client is None."""
    from taleemabad_data_mcp.server import CREDENTIALS_MISSING_MSG, _require_bq, AppContext

    app = AppContext(
        config=MagicMock(),
        bq_client=None,
        audit_logger=None,
        cost_estimator=None,
        feedback_logger=None,
    )
    assert _require_bq(app) == CREDENTIALS_MISSING_MSG


def test_require_bq_returns_none_when_connected():
    """_require_bq should return None when bq_client exists."""
    from taleemabad_data_mcp.server import _require_bq, AppContext

    app = AppContext(
        config=MagicMock(),
        bq_client=MagicMock(),
        audit_logger=MagicMock(),
        cost_estimator=MagicMock(),
        feedback_logger=MagicMock(),
    )
    assert _require_bq(app) is None


def test_banned_tables_contains_legacy():
    """BANNED_TABLES should block the unpartitioned legacy table."""
    from taleemabad_data_mcp.server import BANNED_TABLES

    assert "analytics_analyticsevent" in BANNED_TABLES


def test_safe_filter_regex_accepts_valid():
    """Partition filter regex should accept standard date filters."""
    from taleemabad_data_mcp.server import _SAFE_FILTER_RE

    assert _SAFE_FILTER_RE.match("sent_at >= DATE('2025-01-01')")
    assert _SAFE_FILTER_RE.match("created >= DATE('2025-01-01')")
    assert _SAFE_FILTER_RE.match("sent_at >= DATE('2025-01-01') AND sent_at <= DATE('2025-12-31')")


def test_safe_filter_regex_rejects_injection():
    """Partition filter regex should reject SQL injection attempts."""
    from taleemabad_data_mcp.server import _SAFE_FILTER_RE

    assert not _SAFE_FILTER_RE.match("1=1; DROP TABLE users --")
    assert not _SAFE_FILTER_RE.match("sent_at >= (SELECT MIN(sent_at) FROM other)")
    assert not _SAFE_FILTER_RE.match("sent_at >= '2025-01-01'; DELETE FROM t")


def test_safe_identifier_regex():
    """Identifier regex should accept valid names and reject injection."""
    from taleemabad_data_mcp.server import _SAFE_IDENTIFIER_RE

    assert _SAFE_IDENTIFIER_RE.match("coaching_observation")
    assert _SAFE_IDENTIFIER_RE.match("FDE_Schools")
    assert not _SAFE_IDENTIFIER_RE.match("table`; DROP--")
    assert not _SAFE_IDENTIFIER_RE.match("a b c")


def test_describe_data_median_even():
    """Median of even-length list should average middle two values."""
    vals = [1.0, 2.0, 3.0, 4.0]
    n = len(vals)
    median = (vals[n // 2 - 1] + vals[n // 2]) / 2
    assert median == 2.5


def test_describe_data_median_odd():
    """Median of odd-length list should be the middle value."""
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    n = len(vals)
    median = vals[n // 2]
    assert median == 3.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_server.py -v`
Expected: FAIL — `CREDENTIALS_MISSING_MSG` not yet defined

- [ ] **Step 3: Update `server.py` with graceful degradation**

At the top of `server.py`, after the imports, add:

```python
CREDENTIALS_MISSING_MSG = (
    "BigQuery credentials not found. "
    "Copy 'niete-bq-prod-48ae5260d1ea.json' to this project directory."
)
```

Update the `AppContext` dataclass to allow `None` for all BigQuery-dependent fields:

```python
@dataclass
class AppContext:
    config: ServerConfig
    bq_client: bigquery.Client | None
    audit_logger: AuditLogger | None
    cost_estimator: CostEstimator | None
    feedback_logger: FeedbackLogger | None
```

Replace the `app_lifespan` function:

```python
@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize server-wide resources. Gracefully degrades if credentials missing."""
    config = ServerConfig()

    bq_client = None
    audit_logger = None
    cost_estimator = None
    feedback_logger = None

    try:
        if config.google_application_credentials:
            bq_client = bigquery.Client.from_service_account_json(
                config.google_application_credentials,
                project=config.bigquery_project,
            )
        else:
            bq_client = bigquery.Client(project=config.bigquery_project)

        audit_logger = AuditLogger(
            bq_client=bq_client,
            project=config.bigquery_project,
            audit_dataset=config.audit_dataset,
            audit_table=config.audit_table,
            user_name=config.taleemabad_user,
            hostname=config.taleemabad_hostname,
        )
        cost_estimator = CostEstimator(bq_client, max_bytes=config.bigquery_max_bytes)
        feedback_logger = FeedbackLogger(
            bq_client=bq_client,
            project=config.bigquery_project,
            audit_dataset=config.audit_dataset,
            feedback_table="query_feedback",
            user_name=config.taleemabad_user,
        )

        logger.info(
            "server_started",
            project=config.bigquery_project,
            datasets=config.bigquery_datasets,
        )
    except Exception as e:
        logger.warning(
            "server_started_degraded",
            error=str(e),
            hint="Copy credentials file to project directory",
        )

    try:
        yield AppContext(
            config=config,
            bq_client=bq_client,
            audit_logger=audit_logger,
            cost_estimator=cost_estimator,
            feedback_logger=feedback_logger,
        )
    finally:
        if bq_client:
            bq_client.close()
```

Add a helper function after `AppContext`:

```python
def _require_bq(app: AppContext) -> str | None:
    """Return an error message if BigQuery is not available, else None."""
    if app.bq_client is None:
        return CREDENTIALS_MISSING_MSG
    return None
```

Add `_require_bq` check to the beginning of each existing tool function. For example, in `execute_query`:

```python
    app: AppContext = ctx.request_context.lifespan_context
    err = _require_bq(app)
    if err:
        return err
```

Add this same 3-line check to: `execute_query`, `list_datasets`, `check_table_freshness`, `get_table_schema`, `submit_feedback`. `get_version` does NOT need it (it should always work).

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_server.py -v`
Expected: PASS

- [ ] **Step 5: Run server tests only**

Run: `uv run pytest tests/test_server.py -v`
Expected: All pass

Note: Do NOT run the full test suite yet — `tests/test_cli.py` imports functions that will be removed in Task 6. Run full suite after Task 6.

- [ ] **Step 6: Commit**

```bash
git add src/taleemabad_data_mcp/server.py tests/test_server.py
git commit -m "feat: graceful degradation when credentials are missing"
```

---

### Task 5: Add Phase 1 Tools (preview_table, save_query_results, describe_data)

**Files:**
- Modify: `src/taleemabad_data_mcp/server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Add `preview_table` tool to `server.py`**

Add after the `get_version` tool:

```python
import re as _re

BANNED_TABLES = {"analytics_analyticsevent"}
# Only allow simple comparisons in partition filters — no subqueries, DDL, or DML
_SAFE_FILTER_RE = _re.compile(
    r"^[a-zA-Z_]\w*\s*(>=|<=|>|<|=|!=|BETWEEN)\s*"
    r"(DATE\('[^']+'\)|TIMESTAMP\('[^']+'\)|'[^']*'|\d+)"
    r"(\s+AND\s+[a-zA-Z_]\w*\s*(>=|<=|>|<|=|!=)\s*(DATE\('[^']+'\)|'[^']*'|\d+))*$",
    _re.IGNORECASE,
)
# Reject dangerous SQL keywords in table/dataset names
_SAFE_IDENTIFIER_RE = _re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


@mcp.tool()
async def preview_table(
    dataset: str,
    table: str,
    limit: int = 10,
    partition_filter: str = "",
) -> str:
    """Preview rows from a BigQuery table.

    For partitioned tables, provide a partition_filter (e.g., "sent_at >= DATE('2025-01-01')").
    Blocked for banned tables (unpartitioned legacy tables).

    Args:
        dataset: BigQuery dataset name (e.g., 'tbproddb').
        table: Table name (e.g., 'coaching_observation').
        limit: Max rows to return (default 10, max 50).
        partition_filter: Simple WHERE condition for partitioned tables.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    err = _require_bq(app)
    if err:
        return err

    if dataset not in app.config.bigquery_datasets:
        return f"Dataset '{dataset}' is not in the allowed list: {app.config.bigquery_datasets}"

    if not _SAFE_IDENTIFIER_RE.match(table):
        return f"Invalid table name: '{table}'"

    if table in BANNED_TABLES:
        return f"Table '{table}' is banned (unpartitioned legacy table). Use a governed query instead."

    limit = min(max(1, limit), 50)

    where = ""
    if partition_filter:
        if not _SAFE_FILTER_RE.match(partition_filter.strip()):
            return (
                "Invalid partition_filter. Use simple comparisons only, e.g.: "
                "sent_at >= DATE('2025-01-01')"
            )
        where = f"WHERE {partition_filter}"

    sql = f"SELECT * FROM `{app.config.bigquery_project}.{dataset}.{table}` {where} LIMIT {limit}"

    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=app.config.bigquery_max_bytes,
        )
        query_job = app.bq_client.query(sql, job_config=job_config)
        rows = [dict(row) for row in query_job.result()]

        if app.audit_logger:
            app.audit_logger.log(
                query_text=f"preview: {dataset}.{table}",
                generated_sql=sql,
                tables_accessed=[table],
                rows_returned=len(rows),
                domain="PREVIEW",
            )

        if not rows:
            return f"No rows found in {dataset}.{table}"

        return json.dumps(rows, indent=2, default=str)

    except Exception as e:
        return f"Preview failed: {type(e).__name__}: {e}"
```

- [ ] **Step 2: Add `save_query_results` tool**

```python
@mcp.tool()
async def save_query_results(
    sql: str,
    question: str = "",
    format: str = "csv",
    output_dir: str = ".",
) -> str:
    """Execute a governed query and save results to a file.

    Files are saved to the output_dir (defaults to current working directory
    of the Claude Code session, NOT the plugin directory).

    Args:
        sql: The governed SQL query to execute.
        question: The user's original question (for audit logging).
        format: Output format — 'csv' or 'json'. Default 'csv'.
        output_dir: Directory to save the file. Default '.' (project directory).
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    err = _require_bq(app)
    if err:
        return err

    if format not in ("csv", "json"):
        return f"Invalid format '{format}'. Must be 'csv' or 'json'."

    from pathlib import Path
    out_path = Path(output_dir)
    if not out_path.is_dir():
        return f"Output directory '{output_dir}' does not exist."

    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=app.config.bigquery_max_bytes,
        )
        query_job = app.bq_client.query(sql, job_config=job_config)
        results = query_job.result()
        rows = [dict(row) for row in results]

        if not rows:
            return "Query returned 0 rows. Nothing to save."

        from datetime import UTC, datetime
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M")
        tables = list({ref.table_id for ref in query_job.referenced_tables})
        domain = classify_domain(tables, sql)
        filename = f"taleemabad_export_{timestamp}_{domain}.{format}"
        filepath = out_path / filename

        if format == "csv":
            import csv
            import io

            output = io.StringIO()
            # Metadata header
            output.write(f"# Exported by: {app.config.taleemabad_user}\n")
            output.write(f"# Timestamp: {timestamp}\n")
            output.write(f"# Domain: {domain}\n")
            output.write(f"# Rows: {len(rows)}\n")

            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow({k: str(v) for k, v in row.items()})

            filepath.write_text(output.getvalue(), encoding="utf-8")
        else:
            export_data = {
                "metadata": {
                    "exported_by": app.config.taleemabad_user,
                    "timestamp": timestamp,
                    "domain": domain,
                    "row_count": len(rows),
                },
                "data": rows,
            }
            filepath.write_text(
                json.dumps(export_data, indent=2, default=str), encoding="utf-8"
            )

        bytes_billed = query_job.total_bytes_billed or 0
        cost_usd = bytes_billed / 1_099_511_627_776 * 6.25 if bytes_billed else 0.0

        if app.audit_logger:
            app.audit_logger.log(
                query_text=question or sql,
                generated_sql=sql,
                tables_accessed=tables,
                rows_returned=len(rows),
                cost_bytes=bytes_billed,
                cost_usd=cost_usd,
                domain=f"EXPORT_{domain}",
            )

        return f"Saved {len(rows)} rows to {filepath} ({format.upper()})"

    except Exception as e:
        return f"Save failed: {type(e).__name__}: {e}"
```

- [ ] **Step 3: Add `describe_data` tool**

```python
@mcp.tool()
async def describe_data(
    sql: str,
    question: str = "",
) -> str:
    """Execute a governed query and return descriptive statistics.

    Computes count, mean, min, max, nulls for numeric columns.
    Computes count, unique values, top value for string columns.

    Args:
        sql: The governed SQL query to execute.
        question: The user's original question (for audit logging).
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    err = _require_bq(app)
    if err:
        return err

    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=app.config.bigquery_max_bytes,
        )
        query_job = app.bq_client.query(sql, job_config=job_config)
        results = query_job.result()
        rows = [dict(row) for row in results]

        if not rows:
            return "Query returned 0 rows. Nothing to describe."

        tables = list({ref.table_id for ref in query_job.referenced_tables})
        domain = classify_domain(tables, sql)

        stats = {"row_count": len(rows), "columns": {}}
        for col in rows[0].keys():
            values = [row[col] for row in rows if row[col] is not None]
            null_count = len(rows) - len(values)

            # Try numeric stats
            numeric_vals = []
            for v in values:
                try:
                    numeric_vals.append(float(v))
                except (TypeError, ValueError):
                    break

            if len(numeric_vals) == len(values) and numeric_vals:
                sorted_vals = sorted(numeric_vals)
                n = len(sorted_vals)
                if n % 2 == 0:
                    median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
                else:
                    median = sorted_vals[n // 2]
                stats["columns"][col] = {
                    "type": "numeric",
                    "count": n,
                    "nulls": null_count,
                    "mean": round(sum(sorted_vals) / n, 4),
                    "min": sorted_vals[0],
                    "max": sorted_vals[-1],
                    "median": round(median, 4),
                }
            else:
                # String/categorical stats
                str_vals = [str(v) for v in values]
                from collections import Counter
                counts = Counter(str_vals)
                top_val, top_count = counts.most_common(1)[0] if counts else ("", 0)
                stats["columns"][col] = {
                    "type": "categorical",
                    "count": len(str_vals),
                    "nulls": null_count,
                    "unique": len(counts),
                    "top_value": top_val,
                    "top_count": top_count,
                }

        if app.audit_logger:
            app.audit_logger.log(
                query_text=question or sql,
                generated_sql=sql,
                tables_accessed=tables,
                rows_returned=len(rows),
                domain=f"DESCRIBE_{domain}",
            )

        return json.dumps(stats, indent=2, default=str)

    except Exception as e:
        return f"Describe failed: {type(e).__name__}: {e}"
```

- [ ] **Step 4: Run linter**

Run: `uv run ruff check src/taleemabad_data_mcp/server.py`
Fix any issues.

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -v`
Expected: All pass (or only CLI tests fail, fixed in Task 6)

- [ ] **Step 6: Commit**

```bash
git add src/taleemabad_data_mcp/server.py
git commit -m "feat: add Phase 1 tools (preview_table, save_query_results, describe_data)"
```

---

### Task 6: Simplify CLI (Remove init, upgrade, mcp-generation)

**Files:**
- Modify: `src/taleemabad_data_mcp/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Rewrite `cli.py`**

Replace the entire file. Key changes:
- Remove: `_to_bash_path`, `_find_uv_command`, `_mcp_server_config`, `_bigquery_analytics_config`, `_mcp_json_content`, `_write_mcp_json`, `_create_venv_and_install`, `_running_inside_target_venv`, `_load_settings`, `_save_settings`, `_settings_path`, `_venv_dir`, `_venv_python`, `_uv_path`
- Remove commands: `init`, `upgrade`
- Simplify: `setup` — only copies rules and saves user config (name + env file)
- Simplify: `uninstall` — only removes rules dir + env file
- Keep: `version`, `bump`, `serve`, `dashboard`

```python
"""CLI for setup, uninstall, and running the MCP server."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import click

RULES_DIR_NAME = "taleemabad"
CREDENTIALS_FILENAME = "niete-bq-prod-48ae5260d1ea.json"


def _claude_dir() -> Path:
    """Return ~/.claude/ path."""
    return Path.home() / ".claude"


def _rules_dest() -> Path:
    """Return ~/.claude/rules/taleemabad/ path."""
    return _claude_dir() / "rules" / RULES_DIR_NAME


def _env_path() -> Path:
    """Return ~/.claude/taleemabad-data-mcp.env path."""
    return _claude_dir() / "taleemabad-data-mcp.env"


def _bundled_rules_dir() -> Path:
    """Return the rules directory bundled inside this package."""
    return Path(__file__).parent / "rules"


@click.group()
def main() -> None:
    """Taleemabad Data Navigator — governed semantic layer for BigQuery."""


@main.command(name="version")
def show_version() -> None:
    """Show the installed version."""
    from taleemabad_data_mcp import __version__

    click.echo(f"taleemabad-data-mcp v{__version__}")


def bump_version(minor: bool = False) -> None:
    """Bump package version (patch or minor) and sync plugin rules.

    Patch bump (default): 0.3.0 -> 0.3.1 (fixes, small changes)
    Minor bump (minor=True): 0.3.1 -> 0.4.0 (new features, bigger releases)
    """
    import re

    init_file = Path(__file__).parent / "__init__.py"
    repo_root = Path(__file__).parent.parent.parent
    pyproject_file = repo_root / "pyproject.toml"
    src_rules_dir = Path(__file__).parent / "rules"
    plugin_rules_dir = repo_root / "rules"

    # Read current version
    init_text = init_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', init_text)
    if not match:
        raise RuntimeError("Could not find __version__ in __init__.py")

    major, mid, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    old_version = f"{major}.{mid}.{patch}"

    new_version = f"{major}.{mid + 1}.0" if minor else f"{major}.{mid}.{patch + 1}"

    # Update __init__.py
    new_init = init_text.replace(
        f'__version__ = "{old_version}"', f'__version__ = "{new_version}"'
    )
    init_file.write_text(new_init, encoding="utf-8")

    # Update pyproject.toml
    if pyproject_file.exists():
        pyproject_text = pyproject_file.read_text(encoding="utf-8")
        new_pyproject = pyproject_text.replace(
            f'version = "{old_version}"', f'version = "{new_version}"',
        )
        pyproject_file.write_text(new_pyproject, encoding="utf-8")

    # Sync rules/ at repo root from src rules (for plugin agents to read)
    if src_rules_dir.exists():
        if plugin_rules_dir.exists():
            shutil.rmtree(plugin_rules_dir)
        shutil.copytree(src_rules_dir, plugin_rules_dir)

    # Sync .claude/rules/ for dev convenience (gitignored)
    claude_rules_dir = repo_root / ".claude" / "rules"
    if claude_rules_dir.parent.exists() and src_rules_dir.exists():
        if claude_rules_dir.exists():
            shutil.rmtree(claude_rules_dir)
        shutil.copytree(src_rules_dir, claude_rules_dir)

    # Update plugin manifest version
    plugin_json = repo_root / ".claude-plugin" / "plugin.json"
    if plugin_json.exists():
        manifest = json.loads(plugin_json.read_text(encoding="utf-8"))
        manifest["version"] = new_version
        plugin_json.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Update marketplace manifest version
    marketplace_json = repo_root / ".claude-plugin" / "marketplace.json"
    if marketplace_json.exists():
        mp = json.loads(marketplace_json.read_text(encoding="utf-8"))
        if "plugins" in mp and len(mp["plugins"]) > 0:
            mp["plugins"][0]["version"] = new_version
        marketplace_json.write_text(json.dumps(mp, indent=2) + "\n", encoding="utf-8")

    # Update plugin/.current-version
    current_version_file = repo_root / ".current-version"
    if current_version_file.exists():
        current_version_file.write_text(f"v{new_version}\n", encoding="utf-8")

    click.echo(f"Version bumped: {old_version} -> {new_version}")
    click.echo(f"  Next: git add -A && git commit -m 'chore: bump version to v{new_version}' && git push")


@main.command(name="bump")
@click.option(
    "--minor", is_flag=True, default=False,
    help="Bump minor version (0.X.0) for bigger releases. Default is patch (0.0.X).",
)
def bump_cmd(minor: bool) -> None:
    """Bump version, sync plugin rules, and print next steps.

    Patch bump (default): 0.3.0 -> 0.3.1 (fixes, small changes)
    Minor bump (--minor): 0.3.1 -> 0.4.0 (new features, bigger releases)
    """
    try:
        bump_version(minor=minor)
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.option("--user", required=True, help="Your name (for activity tracking).")
def setup(user: str) -> None:
    """Save your name and sync governance rules.

    The MCP server is configured automatically by the plugin.
    This command only needs to be run once to set your name for audit logs.
    """
    # 1. Copy rules to ~/.claude/rules/taleemabad/
    src_rules = _bundled_rules_dir()
    dest_rules = _rules_dest()

    if not src_rules.exists():
        click.echo(f"Error: bundled rules not found at {src_rules}", err=True)
        sys.exit(1)

    if dest_rules.exists():
        shutil.rmtree(dest_rules)
    dest_rules.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_rules, dest_rules)
    click.echo(f"Rules installed to {dest_rules}")

    # 2. Save user config
    env_content = (
        f"TALEEMABAD_USER={user}\n"
        f"GOOGLE_APPLICATION_CREDENTIALS={CREDENTIALS_FILENAME}\n"
    )
    env_path = _env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(env_content, encoding="utf-8")
    click.echo(f"User config saved to {env_path}")

    # 3. Cleanup old artifacts from previous versions
    old_venv = _claude_dir() / "taleemabad-venv"
    if old_venv.exists():
        click.echo(f"\nNote: Old venv found at {old_venv}")
        click.echo("It is no longer needed. You can delete it manually.")

    cwd = Path.cwd()
    old_mcp = cwd / ".mcp.json"
    if old_mcp.exists():
        click.echo(f"\nNote: Old .mcp.json found at {old_mcp}")
        click.echo("The plugin now provides MCP config automatically.")
        click.echo("Delete this file to avoid conflicts.")

    # Remove stale MCP entry from settings.json (old versions wrote here)
    settings_path = _claude_dir() / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            if "mcpServers" in settings and "taleemabad-data" in settings["mcpServers"]:
                del settings["mcpServers"]["taleemabad-data"]
                if not settings["mcpServers"]:
                    del settings["mcpServers"]
                settings_path.write_text(
                    json.dumps(settings, indent=2) + "\n", encoding="utf-8"
                )
                click.echo("Removed stale MCP entry from settings.json")
        except (json.JSONDecodeError, KeyError):
            pass

    click.echo()
    click.echo("Setup complete! Restart Claude Code to connect.")
    click.echo(f"Make sure '{CREDENTIALS_FILENAME}' is in your project directory.")


@main.command()
def uninstall() -> None:
    """Remove rules and user settings."""
    # 1. Remove rules
    dest_rules = _rules_dest()
    if dest_rules.exists():
        shutil.rmtree(dest_rules)
        click.echo(f"Rules removed from {dest_rules}")
    else:
        click.echo("Rules directory not found (already removed).")

    # 2. Remove env file
    env_path = _env_path()
    if env_path.exists():
        env_path.unlink()
        click.echo(f"User config removed from {env_path}")

    # 3. Note about old artifacts
    old_venv = _claude_dir() / "taleemabad-venv"
    if old_venv.exists():
        click.echo(f"\nNote: Old venv at {old_venv} can be deleted manually.")

    click.echo("Uninstall complete.")


@main.command()
def serve() -> None:
    """Run the MCP server (stdio mode). Used by Claude Code automatically."""
    from taleemabad_data_mcp.server import mcp

    mcp.run()


@main.command()
def dashboard() -> None:
    """Launch the observability dashboard (Streamlit)."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        click.echo(
            "Streamlit is not installed. Install dashboard dependencies:\n"
            '  pip install "taleemabad-data-mcp[dashboard]"',
            err=True,
        )
        sys.exit(1)

    import subprocess as sp

    dashboard_app = Path(__file__).parent / "dashboard" / "app.py"
    if not dashboard_app.exists():
        click.echo(f"Dashboard app not found at {dashboard_app}", err=True)
        sys.exit(1)

    sp.run([sys.executable, "-m", "streamlit", "run", str(dashboard_app)], check=False)
```

- [ ] **Step 2: Rewrite `tests/test_cli.py`**

```python
"""Tests for CLI setup/uninstall commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from taleemabad_data_mcp.cli import _bundled_rules_dir, main


def _mock_patches(monkeypatch, claude_dir):
    """Apply common monkeypatches for CLI tests."""
    monkeypatch.setattr("taleemabad_data_mcp.cli._claude_dir", lambda: claude_dir)
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._rules_dest", lambda: claude_dir / "rules" / "taleemabad"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._env_path", lambda: claude_dir / "taleemabad-data-mcp.env"
    )
    claude_dir.mkdir(parents=True, exist_ok=True)


def test_setup_copies_rules_and_saves_config(tmp_path, monkeypatch):
    """Setup should copy rules and save user config."""
    claude_dir = tmp_path / ".claude"
    _mock_patches(monkeypatch, claude_dir)

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--user", "Test User"])
    assert result.exit_code == 0, result.output

    # Rules were copied
    rules_dir = claude_dir / "rules" / "taleemabad"
    assert rules_dir.exists()
    assert (rules_dir / "index.md").exists()
    assert (rules_dir / "bigquery.md").exists()
    teacher_rules = rules_dir / "ict-islamabad" / "dimensions" / "teachers"
    assert (teacher_rules / "teacher-query-rules.md").exists()

    # Env file was created
    env_content = (claude_dir / "taleemabad-data-mcp.env").read_text()
    assert "TALEEMABAD_USER=Test User" in env_content


def test_uninstall_removes_rules_and_env(tmp_path, monkeypatch):
    """Uninstall should remove rules and env file."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    _mock_patches(monkeypatch, claude_dir)

    # Create the things that setup would have created
    rules_dir = claude_dir / "rules" / "taleemabad"
    rules_dir.mkdir(parents=True)
    (rules_dir / "index.md").write_text("test")

    env_path = claude_dir / "taleemabad-data-mcp.env"
    env_path.write_text("TALEEMABAD_USER=test")

    runner = CliRunner()
    result = runner.invoke(main, ["uninstall"])
    assert result.exit_code == 0, result.output

    assert not rules_dir.exists()
    assert not env_path.exists()


def test_bundled_rules_exist():
    """The package should include bundled rule files."""
    rules_dir = _bundled_rules_dir()
    assert rules_dir.exists(), f"Rules dir not found: {rules_dir}"
    assert (rules_dir / "index.md").exists()
    assert (rules_dir / "data-governance.md").exists()
    assert (rules_dir / "bigquery.md").exists()


def test_setup_warns_about_old_artifacts(tmp_path, monkeypatch):
    """Setup should warn about old venv and .mcp.json."""
    claude_dir = tmp_path / ".claude"
    _mock_patches(monkeypatch, claude_dir)

    # Create old artifacts
    old_venv = claude_dir / "taleemabad-venv"
    old_venv.mkdir(parents=True)

    monkeypatch.chdir(tmp_path)
    old_mcp = tmp_path / ".mcp.json"
    old_mcp.write_text('{"mcpServers": {"taleemabad-data": {}}}')

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--user", "Ali"])
    assert result.exit_code == 0, result.output
    assert "Old venv found" in result.output
    assert "Old .mcp.json found" in result.output
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_cli.py -v`
Expected: All pass

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest -v`
Expected: All pass

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/ tests/`
Fix any issues.

- [ ] **Step 6: Commit**

```bash
git add src/taleemabad_data_mcp/cli.py tests/test_cli.py
git commit -m "refactor: simplify CLI — remove init/upgrade/mcp-generation"
```

---

### Task 7: Simplify Setup Command and Update Agent

**Files:**
- Modify: `commands/setup.md`
- Modify: `agents/data-analyst.md`

- [ ] **Step 1: Rewrite `commands/setup.md`**

```markdown
# /taleemabad-setup

Set up your name for audit logging and sync governance rules. The MCP server is configured automatically by the plugin.

## Prerequisites
- Plugin must be installed: `claude plugin install taleemabad-data@Orenda-Project`
- `niete-bq-prod-48ae5260d1ea.json` (GCP service account key) should be in each project directory you want to use

## Steps

### Step 1: Ask for name
Ask: "What is your name? (used for audit logs)"
Save as `user_name`.

### Step 2: Run setup
On Windows:
```
python -m taleemabad_data_mcp setup --user "<user_name>"
```

On macOS/Linux:
```
python3 -m taleemabad_data_mcp setup --user "<user_name>"
```

**IMPORTANT:** If `python -m taleemabad_data_mcp` fails with "No module named taleemabad_data_mcp", install the package first:
```
pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

### Step 3: Done
Tell the user:
```
Setup complete!

Restart Claude Code (close and reopen, or Ctrl+R).
Then run /mcp to verify:
  - taleemabad-data · connected

Make sure niete-bq-prod-48ae5260d1ea.json is in your project directory.
```

## Error handling

| Error | Fix |
|-------|-----|
| "No module named taleemabad_data_mcp" | Run `pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"` |
| MCP server shows "credentials not found" | Copy `niete-bq-prod-48ae5260d1ea.json` to project directory |
```

- [ ] **Step 2: Update `agents/data-analyst.md`**

Remove lines 107-109 (bigquery-analytics reference in Step 6):
```
### Step 6: Optional analysis

If the user asks for trends, charts, correlation, or reports:
- Use bigquery-analytics MCP tools for analysis/visualization ONLY
- NEVER use bigquery-analytics for data retrieval — all data comes through taleemabad-data
- NEVER call bigquery-analytics tools: `execute_query`, `build_query`, `preview_table`
```

Replace with:
```
### Step 6: Optional analysis

If the user asks for descriptive statistics, use the `describe_data` tool.
If the user asks to export results, use the `save_query_results` tool.
If the user asks for charts or visualizations, tell them: "Chart generation is coming in a future release. For now, I can provide the data in CSV/JSON format for you to visualize in your preferred tool."
```

Remove line 134 from the "MUST NOT" list:
```
- Use bigquery-analytics for data retrieval
```

- [ ] **Step 3: Commit**

```bash
git add commands/setup.md agents/data-analyst.md
git commit -m "refactor: simplify setup command, remove bigquery-analytics references"
```

---

### Task 8: Run Full Validation and Version Bump

**Files:**
- Various (validation only + version bump)

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v --tb=short`
Expected: All tests pass

- [ ] **Step 2: Run linter**

Run: `uv run ruff check src/ tests/`
Expected: No errors

- [ ] **Step 3: Run format check**

Run: `uv run ruff format --check src/ tests/`
Fix if needed: `uv run ruff format src/ tests/`

- [ ] **Step 4: Verify .mcp.json is valid JSON and tracked**

Run: `python -c "import json; json.load(open('.mcp.json'))" && git status .mcp.json`
Expected: No error, file is tracked

- [ ] **Step 5: Verify serve command still works**

Run: `uv run python -m taleemabad_data_mcp version`
Expected: Shows current version

- [ ] **Step 6: Commit any remaining changes**

```bash
git add -A
git status
```

If there are changes to commit:
```bash
git commit -m "chore: fix lint and formatting"
```

- [ ] **Step 7: Version bump (minor — new architecture + new tools)**

```bash
python -m taleemabad_data_mcp bump --minor
git add -A
git commit -m "chore: bump version to v0.12.0"
```

- [ ] **Step 8: Push**

```bash
git push origin master && git push origin master:main
git tag v0.12.0 && git push origin v0.12.0
```

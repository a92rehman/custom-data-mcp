# Data Governance MCP — Taleemabad

Python MCP server — thin BigQuery execution layer with governed data agents.
See [VISION.md](docs/VISION.md) for why and what. See [README.md](README.md) for installation.

## For Data Questions

**All data questions MUST go through the `data-analyst` agent first.** The workflow:

1. Dispatch the `data-analyst` agent with the user's question
2. The agent reads governance rules, asks mandatory clarification questions, and returns governed SQL
3. **You (parent session) execute the SQL** via `execute_query` MCP tool
4. Present results to the user with freshness, cost, and rule file used

The agent generates the SQL but cannot call MCP tools directly — you must execute it.
Do NOT generate SQL yourself. Do NOT call `execute_query` without the agent's governed SQL.

## Architecture
- **MCP server is a thin execution layer** — runs queries, estimates costs, logs audits
- **Governance rules live in the plugin's `rules/` directory** — read by the data-analyst subagent
- **Two server modes:** stdio (local) or streamable-http (remote Railway deployment)
- **Remote deployment:** MCP server runs on Railway, plugin connects via URL
- **Self-healing loops** — two automated recovery systems:
  - **Query loop:** `execute_query` returns structured JSON errors. `data-analyst` Phase 4 dispatches `query-fixer` subagent (max 3 attempts), opens a ticket, and escalates if unfixable.
  - **System loop:** `system-doctor` agent detects and fixes infrastructure issues (MCP connectivity, env config, rules sync, hook crashes). Auto-triggered via sentinel file from session-start hook, or manually via `/taleemabad-doctor`.
- **Ticket system** — all self-healing actions tracked as tickets (JSONL + BigQuery). Dashboard page at `7_Tickets.py`.
- **Session-start hook is Python-first** — `hooks/session-start/update.py` handles Windows paths natively, falls back to bash. Writes `~/.claude/taleemabad-doctor-needed` sentinel when health checks fail.

## Tech Stack
- **Language:** Python 3.11+
- **MCP Framework:** FastMCP
- **Database:** Google BigQuery (project: niete-bq-prod)
- **Dashboard:** Streamlit + Plotly (optional `[dashboard]` extra)
- **Config:** pydantic-settings with `.env` support
- **Testing:** pytest + pytest-asyncio
- **Linting:** ruff
- **Package manager:** uv

## Commands
```bash
uv sync                                    # Install dependencies
uv run python -m taleemabad_data_mcp       # Run server (stdio)
uv run pytest                              # Run tests
uv run pytest --cov=src/taleemabad_data_mcp --cov-report=term-missing
uv run ruff check src/ tests/             # Lint
uv run ruff format src/ tests/            # Format
```

## CLI Commands
```bash
python -m taleemabad_data_mcp setup --email <email>  # Save email
python -m taleemabad_data_mcp version       # Show installed version
python -m taleemabad_data_mcp serve         # Run MCP server (stdio)
python -m taleemabad_data_mcp serve-remote  # Run MCP server (HTTP, Railway)
python -m taleemabad_data_mcp dashboard     # Launch Streamlit dashboard
python -m taleemabad_data_mcp uninstall     # Remove user config
python -m taleemabad_data_mcp bump          # Patch version bump (bump --minor for minor)
```

## Project Structure
```
.mcp.json                       # Plugin MCP server config (remote URL)
.claude-plugin/
  plugin.json                   # Plugin manifest (agents, commands)
  marketplace.json              # Marketplace listing
src/taleemabad_data_mcp/        # Python MCP server package
  __init__.py                   # Package version (__version__)
  __main__.py                   # Entry point (routes to CLI)
  cli.py                        # CLI: setup, bump, serve, serve-remote, dashboard, uninstall
  server.py                     # FastMCP instance, 12 MCP tools
  config.py                     # Configuration management (env vars)
  rules/                        # SOURCE OF TRUTH — governance rules
  engine/                       # Audit, cost estimation, domain classification, errors, tickets
  models/                       # Pydantic models (audit, feedback, ticket)
  dashboard/                    # Streamlit observability dashboard (incl. Tickets page)
agents/                         # Plugin agents (loaded by Claude Code plugin system)
  data-analyst.md               # Primary — reads rules, asks clarifications, generates governed SQL, retry loop
  data-admin.md                 # Diagnostics — schema, freshness, audit, troubleshooting
  query-fixer.md                # Subagent — diagnoses failed SQL, proposes corrected query
  system-doctor.md              # Infrastructure — detects/fixes MCP, env, rules, hook issues
commands/                       # Plugin slash commands
hooks/                          # Plugin hooks (session-start: Python-first, bash fallback)
rules/                          # DERIVED COPY — synced from src/ by bump command
tests/
docs/
```

## MCP Tools
| Tool | Purpose |
|------|---------|
| `execute_query` | Run governed SQL against BigQuery (structured JSON response, cost guardrails + audit). Supports `legacy_format=True` for backward compat. |
| `list_datasets` | Auto-discover and browse all BigQuery datasets and tables |
| `get_table_schema` | Get columns and types for a table |
| `check_table_freshness` | Check when a table was last modified |
| `submit_feedback` | Log optional thumbs up/down + comment on a query result |
| `get_version` | Return installed version, user name, project, and datasets |
| `preview_table` | Quick peek at table data (SQL injection protected) |
| `save_query_results` | Export governed query results to CSV or JSON with metadata |
| `describe_data` | Descriptive statistics on query results |
| `report_ticket` | Open a self-healing ticket (query or system loop) |
| `update_ticket` | Add actions/diagnosis to an existing ticket |
| `close_ticket` | Close a ticket with final status and resolution notes |

## Distribution
Teams install via Claude Code plugin system:
```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
# Then in Claude Code: /taleemabad-setup (one time, for email)
```
The plugin bundles `.mcp.json` pointing to the remote MCP server URL. No local Python, uv, or credentials needed.

## For Developers: Editing Governance Rules

Rules define what queries are valid. They live in `src/taleemabad_data_mcp/rules/`.

### How rules propagate
```
src/taleemabad_data_mcp/rules/   ← SOURCE OF TRUTH (committed)
        │
        │  `python -m taleemabad_data_mcp bump`
        └──▶ rules/                           (plugin agents read from here)
                │
                │  git push --tags
                │  session-start hook: shallow clone → extract rules/
                ▼
PLUGIN_CACHE/rules/              ← User's copy (auto-downloaded)
                │
                │  session-start hook writes absolute path
                ▼
~/.claude/taleemabad-rules-path  ← Pointer file (agent reads this to find rules)
```

### How the agent finds rules
The data-analyst agent runs as a subprocess from the user's working directory — NOT the plugin directory. It cannot use relative paths to find rules in the plugin cache.

The session-start hook writes `~/.claude/taleemabad-rules-path` containing the absolute path to the rules directory (e.g., `/home/user/.claude/plugins/cache/Orenda-Project/taleemabad-data/0.17.15/rules`). The agent reads this file first, then uses the path to read `index.md` and domain-specific rule files.

### Steps to add a new rule
1. Create the `.md` file in `src/taleemabad_data_mcp/rules/<region>/<domain>/`
2. Add an entry in `src/taleemabad_data_mcp/rules/index.md`
3. Run `python -m taleemabad_data_mcp bump`
4. Commit, tag, and push — users get it automatically

### Important
- `rules/` at repo root is a derived copy — overwritten by bump
- Never edit `rules/` directly
- Rules are NOT placed in `~/.claude/rules/` — that bypasses agent governance

## Code Conventions
- Type hints on all function signatures
- Pydantic models for all data structures
- `async def` for all tool functions
- Docstrings on all public functions
- No `print()` — use structured logging via structlog
- BigQuery client as singleton via lifespan pattern

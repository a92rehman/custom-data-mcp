# Data Governance MCP — Taleemabad

Python MCP server — thin BigQuery execution layer.
Claude Code reads governance rules from `.claude/rules/` and uses MCP tools to execute queries.
See [VISION.md](docs/VISION.md) for why and what. See [README.md](README.md) for installation.

## Architecture
- **Governance logic lives in `.claude/rules/`** — Claude Code reads rules, understands business logic, generates queries
- **MCP server is a thin execution layer** — runs queries, estimates costs, logs audits
- **Two server modes:** stdio (local Claude Code plugin) or streamable-http (remote Railway deployment)
- **Remote deployment:** MCP server runs on Railway, plugin connects via URL — no local Python/credentials needed
- **No YAML engine** — no metric parsing at runtime. Claude reads the rules directly.

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
python -m taleemabad_data_mcp setup --email <email>  # Save email + sync rules
python -m taleemabad_data_mcp version       # Show installed version
python -m taleemabad_data_mcp serve         # Run MCP server (stdio, used by Claude Code locally)
python -m taleemabad_data_mcp serve-remote  # Run MCP server (HTTP, for Railway deployment)
python -m taleemabad_data_mcp dashboard     # Launch Streamlit dashboard (needs [dashboard] extra)
python -m taleemabad_data_mcp uninstall     # Remove rules + user config
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
  server.py                     # FastMCP instance, 9 MCP tools
  config.py                     # Configuration management (env vars)
  rules/                        # SOURCE OF TRUTH — governance rules (32 MD files, 3 regions)
    index.md                    # READ FIRST — routes to general rules + regions
    bigquery.md                 # Partition policy, event table hierarchy
    ict-islamabad/              # Region: ICT (org_id=1, dataset: tbproddb)
    rawalpindi/                 # Region: RWP (RUMI_DB + TaleemHub_DB)
    moawin-akhuwat/             # Region: Moawin/Akhuwat (neondb + zavia1)
  engine/
    audit_logger.py             # BigQuery audit writes + local JSON Lines fallback
    feedback_logger.py          # Feedback writes (thumbs up/down) + local fallback
    cost_estimator.py           # BigQuery dry-run cost estimation
    domain_classifier.py        # Classify queries by domain
  models/
    audit.py                    # AuditLogEntry with cost tracking + domain + email fields
    feedback.py                 # FeedbackEntry (rating, comment)
  dashboard/                    # Streamlit observability dashboard (deployed on Railway)
agents/                         # Plugin agents (loaded by Claude Code plugin system)
  data-analyst.md               # Primary — reads rules, generates governed SQL
  data-admin.md                 # Diagnostics — schema, freshness, audit, troubleshooting
commands/                       # Plugin slash commands
  setup.md                      # /taleemabad-setup — save email + sync rules
hooks/                          # Plugin hooks (auto-update via git tags)
rules/                          # DERIVED COPY — synced from src/ by bump command
                                # Plugin agents read from this location
tests/
docs/
  INSTALL.md                    # Quick reference (points to README)
  VISION.md                     # Strategic vision, 15 sections
  superpowers/                  # Historical design specs and plans
# Railway deployment (two services from same repo)
Procfile                        # Dashboard service: bash railway_start.sh
railway_start.sh                # Streamlit dashboard startup
railway_start_mcp.sh            # MCP server startup (HTTP transport)
nixpacks.toml                   # Railway build config (Python 3.11)
runtime.txt                     # Python version for Railway
requirements.txt                # Railway dependencies (includes dashboard + MCP extras)
```

## MCP Tools
| Tool | Purpose |
|------|---------|
| `execute_query` | Run governed SQL against BigQuery (cost guardrails + audit + domain tagging) |
| `list_datasets` | Auto-discover and browse all BigQuery datasets and tables |
| `get_table_schema` | Get columns and types for a table |
| `check_table_freshness` | Check when a table was last modified |
| `submit_feedback` | Log optional thumbs up/down + comment on a query result |
| `get_version` | Return installed version, user name, project, and datasets |
| `preview_table` | Quick peek at table data (SQL injection protected, banned table guard) |
| `save_query_results` | Export governed query results to CSV or JSON with metadata |
| `describe_data` | Descriptive statistics (mean, median, min, max, nulls, unique) on query results |

## Environment Variables

These are **server-side only** (Railway deployment). Users do NOT need to set any environment variables.

```
# Railway MCP server environment:
BIGQUERY_PROJECT=niete-bq-prod             # Required
GOOGLE_CREDENTIALS_JSON=<json>             # Full JSON content of service account key
TALEEMABAD_REMOTE_MODE=true                # Enable HTTP transport
BIGQUERY_MAX_BYTES=1073741824              # Default 1GB
AUDIT_DATASET=mcp_audit                    # Default
AUDIT_TABLE=activity_log                   # Default
```

## Distribution
Teams install via Claude Code plugin system:
```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
# Then in Claude Code: /taleemabad-setup (one time, for email)
# No credentials file needed — the MCP server runs remotely on Railway
```
The plugin bundles `.mcp.json` pointing to the remote MCP server URL. No local Python, uv, or credentials needed. Setup syncs rules to `~/.claude/rules/taleemabad/` and saves user email.

## Adding or Editing Governance Rules

Rules are the core of this project — they define what queries are valid.

### Where to edit
Always edit in `.claude/rules/` in the project directory. This is your **working copy** — Claude Code loads these as session context so you can test immediately.

### How rules propagate
```
.claude/rules/                   ← EDIT HERE (working copy, gitignored)
        │
        │  `python -m taleemabad_data_mcp bump`
        ├──▶ src/taleemabad_data_mcp/rules/   (ships with Python package)
        └──▶ rules/                           (plugin agents read from here)
                │
                │  git push + session-start hook on user machines
                ▼
~/.claude/rules/taleemabad/      ← User's copy (auto-synced every session)
```

### Steps to add a new rule
1. Create the `.md` file in `.claude/rules/<region>/<domain>/`
2. Add an entry in `.claude/rules/index.md` pointing to the new file
3. Run `python -m taleemabad_data_mcp bump` — syncs to `src/rules/` and `rules/`
4. Commit and push — users get it automatically on next session start

### Who reads rules
- **You (developer)** — edit `.claude/rules/` directly, loaded as Claude Code context
- **Plugin agents** (`data-analyst.md`, `data-admin.md`) — read from `${CLAUDE_PLUGIN_ROOT}/rules/`
- **End users** — `~/.claude/rules/taleemabad/` auto-synced by session-start hook
- All copies are kept in sync by the bump command + session-start hook

### Important
- `.claude/rules/` is gitignored — the committed version is `src/taleemabad_data_mcp/rules/`
- `bump` detects which exists and uses `.claude/rules/` as source if present, otherwise `src/rules/`
- Never edit `rules/` at repo root directly — it's overwritten by bump

## Code Conventions
- Type hints on all function signatures
- Pydantic models for all data structures
- `async def` for all tool functions
- Docstrings on all public functions — these become tool descriptions for the LLM
- No `print()` — use structured logging via structlog
- BigQuery client as singleton via lifespan pattern — never create clients in tool functions

## Event Table Hierarchy
| Table | Status | Partition |
|-------|--------|-----------|
| `tbproddb.analytics_events` | **PRIMARY** | DAY on `sent_at` (70M+ rows) |
| `tbproddb.events_partitioned` | FALLBACK | DAY on `created` (7.5 GB) |
| `tbproddb.analytics_analyticsevent` | NEVER USE | Unpartitioned (68.6 GB) |

## Domain Context
- Taleemabad is a Pakistani EdTech platform with apps for teacher training and lesson plans
- 5 datasets: tbproddb (466 tables), RUMI_DB (70 tables), TaleemHub_DB (60 tables), neondb (Schoolpilot), zavia1 (Zavia)
- **Rules are organized by region** — always determine region first
- **ICT/Islamabad** (org_id=1): teachers, lesson plans, observations (FICO), training — complete
- **Rawalpindi**: users, AI lesson plans, human+AI coaching, student assessments — complete
- **Moawin/Akhuwat**: users, AI lesson plans, AI coaching (with lesson fidelity), student assessments — complete
- levels = teacher level (PRIMARY, MIDDLE, SECONDARY) — stored as JSON array
- FICO is the classroom observation framework (Sections B, C, D)
- Theory of Change: LP Adoption → Coaching → Classroom Practice → Teacher Behavior → Student Outcomes

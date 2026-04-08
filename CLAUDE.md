# Data Governance MCP — Taleemabad

Python MCP server — thin BigQuery execution layer.
Claude Code reads governance rules from `.claude/rules/` and uses MCP tools to execute queries.
See [VISION.md](docs/VISION.md) for why and what. See [README.md](README.md) for installation.

## Architecture
- **Governance logic lives in `.claude/rules/`** — Claude Code reads rules, understands business logic, generates queries
- **MCP server is a thin execution layer** — runs queries, estimates costs, logs audits
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
python -m taleemabad_data_mcp setup      # First-time install (--user, --credentials)
python -m taleemabad_data_mcp upgrade    # Update rules + config (reads saved credentials)
python -m taleemabad_data_mcp init       # Create .mcp.json in current project
python -m taleemabad_data_mcp version    # Show installed version
python -m taleemabad_data_mcp serve      # Run MCP server (used by Claude Code)
python -m taleemabad_data_mcp dashboard  # Launch Streamlit dashboard (needs [dashboard] extra)
python -m taleemabad_data_mcp uninstall  # Remove rules, config, venv
python -m taleemabad_data_mcp bump       # Patch version bump (bump --minor for minor)
```

## Project Structure
```
src/
  taleemabad_data_mcp/
    __init__.py           # Package version (__version__)
    __main__.py           # Entry point (routes to CLI)
    cli.py                # CLI: setup, upgrade, init, version, serve, dashboard, uninstall
    server.py             # FastMCP instance, MCP tools
    config.py             # Configuration management (env vars)
    engine/
      audit_logger.py     # BigQuery audit writes + local JSON Lines fallback
      feedback_logger.py  # Feedback writes (thumbs up/down) + local fallback
      cost_estimator.py   # BigQuery dry-run cost estimation
      domain_classifier.py # Classify queries by domain (teachers, LPs, observations, training)
    models/
      audit.py            # AuditLogEntry with cost tracking + domain field
      feedback.py         # FeedbackEntry (rating, comment)
    dashboard/            # Streamlit observability dashboard
      app.py              # Entry point with st.navigation
      pages/              # Overview, Query Analytics, Feedback, Cost, Errors, Freshness
      data/               # BigQuery queries + client for dashboard
      components/         # Shared filters, charts, styles
    rules/                # Governance rules (bundled in wheel, copied on setup)
      index.md            # READ FIRST — routes to general rules + regions
      bigquery.md         # Partition policy, event table hierarchy
      ict-islamabad/      # Region: ICT (org_id=1, dataset: tbproddb)
      rawalpindi/         # Region: RWP (RUMI_DB + TaleemHub_DB)
tests/
docs/
  INSTALL.md              # User installation guide with troubleshooting
  VISION.md               # Why this exists, 15-section strategy
  research/               # Background research (5 reports)
  superpowers/            # Design specs and implementation plans
.claude/
  rules/                  # Dev copy — mirrors src/.../rules/
```

## MCP Tools
| Tool | Purpose |
|------|---------|
| `execute_query` | Run governed SQL against BigQuery (cost guardrails + audit + domain tagging) |
| `list_datasets` | Browse allowed datasets and tables |
| `get_table_schema` | Get columns and types for a table |
| `check_table_freshness` | Check when a table was last modified |
| `submit_feedback` | Log optional thumbs up/down + comment on a query result |
| `get_version` | Return installed version, user name, project, and datasets |

## Environment Variables
```
BIGQUERY_PROJECT=niete-bq-prod             # Required
BIGQUERY_DATASETS=RUMI_DB,TaleemHub_DB,tbproddb  # Required
GOOGLE_APPLICATION_CREDENTIALS=<path>      # Required (service account JSON)
BIGQUERY_MAX_BYTES=1073741824              # Default 1GB
CACHE_TTL_SECONDS=3600                     # Default 1hr
LOG_LEVEL=INFO
TALEEMABAD_USER=<name>                     # For activity tracking
AUDIT_DATASET=mcp_audit                    # Default
AUDIT_TABLE=activity_log                   # Default
```

## Distribution
Teams install via dedicated venv:
```bash
python -m venv ~/.claude/taleemabad-venv
~/.claude/taleemabad-venv/bin/pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Name" --credentials /path/to/key.json
```
This copies rules to `~/.claude/rules/taleemabad/`, adds MCP config to `~/.claude/settings.json`, and saves credentials for future upgrades.

Updates only need: `pip install --force-reinstall ... && python -m taleemabad_data_mcp upgrade`

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
- 3 main datasets: RUMI_DB (70 tables), TaleemHub_DB (60 tables), tbproddb (466 tables)
- **Rules are organized by region** — always determine region first
- **ICT/Islamabad** (org_id=1): teachers, lesson plans, observations (FICO), training — complete
- **Rawalpindi**: users, AI lesson plans, human+AI coaching, student assessments — complete
- **Moawin**: not yet available
- levels = teacher level (PRIMARY, MIDDLE, SECONDARY) — stored as JSON array
- FICO is the classroom observation framework (Sections B, C, D)
- Theory of Change: LP Adoption → Coaching → Classroom Practice → Teacher Behavior → Student Outcomes

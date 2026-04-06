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

## Project Structure
```
src/
  taleemabad_data_mcp/
    __init__.py
    __main__.py           # Entry point (routes to CLI)
    cli.py                # CLI: setup, uninstall, serve commands
    server.py             # FastMCP instance, MCP tools
    config.py             # Configuration management (env vars)
    engine/
      audit_logger.py     # BigQuery audit writes + local JSON Lines fallback
      cost_estimator.py   # BigQuery dry-run cost estimation
    models/
      audit.py            # AuditLogEntry with cost tracking fields
    rules/                # Governance rules (single source of truth)
      index.md            # READ FIRST — routes to general rules + regions
      data-governance.md  # General (all regions)
      bigquery.md         # Partition policy, event table rules
      caching.md          # Freshness, loop prevention
      failure-handling.md # Retries, circuit breaker
      observability.md    # Telemetry, audit logging
      ict-islamabad/      # Region: ICT (org_id=1, dataset: tbproddb)
        dimensions/teachers/
        lesson_plans/
        coaching_observations/
        training/
tests/
docs/
  VISION.md
  research/
.claude/
  rules/                  # Dev copy — mirrors src/.../rules/
```

## MCP Tools
| Tool | Purpose |
|------|---------|
| `execute_query` | Run governed SQL against BigQuery (cost guardrails + audit) |
| `list_datasets` | Browse allowed datasets and tables |
| `get_table_schema` | Get columns and types for a table |
| `check_table_freshness` | Check when a table was last modified |

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
Teams install with one command:
```bash
uvx taleemabad-data-mcp setup --user "Name" --credentials /path/to/key.json
```
This copies rules to `~/.claude/rules/taleemabad/` and adds MCP config to `~/.claude/settings.json`.
Nothing is added to the user's project directory.

## Code Conventions
- Type hints on all function signatures
- Pydantic models for all data structures
- `async def` for all tool functions
- Docstrings on all public functions — these become tool descriptions for the LLM
- No `print()` — use structured logging via structlog
- BigQuery client as singleton via lifespan pattern — never create clients in tool functions

## Domain Context
- Taleemabad is a Pakistani EdTech platform with apps for teacher training and lesson plans
- 3 main datasets: RUMI_DB (70 tables), TaleemHub_DB (60 tables), tbproddb (466 tables)
- **Rules are organized by region** — always determine region first
- organization_id = region (1 = ICT/Islamabad, others TBD)
- ICT/Islamabad rules are complete (tbproddb). Punjab/RWP and Moawin rules will be added later.
- levels = teacher level (PRIMARY, MIDDLE, SECONDARY) — stored as JSON array
- FICO is the classroom observation framework (Sections B, C, D)
- Theory of Change: LP Adoption → Coaching → Classroom Practice → Teacher Behavior → Student Outcomes

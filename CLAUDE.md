# Data Governance MCP — Taleemabad

Python MCP server — thin BigQuery execution layer.
Claude Code reads governance rules from `.claude/rules/` and uses MCP tools to execute queries.
See @docs/VISION.md for why and what. See @README.md for installation.

## Architecture
- **Governance logic lives in `.claude/rules/`** — Claude Code reads rules, understands business logic, generates queries
- **MCP server is a thin execution layer** — runs queries, estimates costs, validates partitions, logs audits
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
    __main__.py           # Entry point
    server.py             # FastMCP instance, lifespan, MCP tools (execute_query, list_datasets, get_table_schema)
    config.py             # Configuration management (env vars)
    engine/               # Supporting logic
      audit_logger.py     # Immutable audit log entries
      cost_estimator.py   # BigQuery dry-run cost estimation
      partition_validator.py  # Partition-first enforcement
    models/               # Pydantic models (audit entries)
    tools/                # Reserved for future tool modules
    resources/            # MCP resource definitions (future)
    prompts/              # MCP prompt templates (future)
tests/
docs/
  VISION.md
  research/
.claude/
  rules/
    index.md              # READ FIRST — points to all domain rules
    data-governance.md    # General governance rules
    bigquery.md           # BigQuery coding rules
    caching.md            # Caching rules
    failure-handling.md   # Failure handling rules
    observability.md      # Logging rules
    dimensions/
      teachers/           # Teacher data definitions + query rules
    theory_of_change/     # LP, FICO, training, student metrics (TBD)
```

## Environment Variables
```
BIGQUERY_PROJECT=niete-bq-prod             # Required
BIGQUERY_DATASETS=RUMI_DB,TaleemHub_DB,tbproddb  # Required
GOOGLE_APPLICATION_CREDENTIALS=<path>      # Required (service account JSON)
BIGQUERY_MAX_BYTES=1073741824              # Default 1GB
CACHE_TTL_SECONDS=3600                     # Default 1hr
LOG_LEVEL=INFO
```

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
- organization_id = region (1 = ICT/Islamabad)
- levels = teacher level (PRIMARY, MIDDLE, SECONDARY) — stored as JSON array
- FICO is the classroom observation framework (Sections B, C, D)
- Theory of Change: LP Adoption → Coaching → Classroom Practice → Teacher Behavior → Student Outcomes

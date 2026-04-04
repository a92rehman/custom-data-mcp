# Data Governance MCP — Taleemabad

Python MCP server — governed semantic layer for BigQuery.
See @docs/VISION.md for why and what. See @README.md for installation.

## Tech Stack
- **Language:** Python 3.11+
- **MCP Framework:** FastMCP
- **Database:** Google BigQuery
- **Config:** pydantic-settings with `.env` support
- **Testing:** pytest + pytest-asyncio
- **Linting:** ruff
- **Package manager:** uv

## Commands
```bash
uv sync                                    # Install dependencies
uv run python -m taleemabad_data_mcp       # Run server (stdio)
uv run pytest                              # Run tests
uv run pytest tests/test_rule_engine.py -v # Single file
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
    server.py             # FastMCP instance, tool/resource/prompt definitions
    config.py             # Configuration management (env vars)
    tools/                # MCP tool implementations
      query_tools.py
      governance_tools.py
      schema_tools.py
    resources/            # MCP resource definitions
    prompts/              # MCP prompt templates
    rules/                # Gold metric YAML definitions
    engine/               # Core governance logic
      rule_engine.py      # YAML rule loader, metric resolver
      query_builder.py    # SQL generation from metric definitions
      cache.py            # Freshness-aware query cache
      audit_logger.py     # Audit log entries
    models/               # Pydantic models
tests/
docs/
  VISION.md
  research/
```

## Environment Variables
```
BIGQUERY_PROJECT=<gcp-project-id>        # Required
BIGQUERY_DATASETS=<comma-separated>       # Required
GOOGLE_APPLICATION_CREDENTIALS=<path>     # Optional if using ADC
BIGQUERY_MAX_BYTES=1073741824            # Default 1GB
CACHE_TTL_SECONDS=3600                   # Default 1hr
LOG_LEVEL=INFO
```

## Metric YAML Schema
Each Gold metric is a YAML file in `src/taleemabad_data_mcp/rules/`:
```yaml
name: lp_weekly_adoption_rate
display_name: "LP Adoption Rate (Weekly)"
description: "Percentage of teachers engaging with lesson plans per week"
category: theory_of_change
tier: gold
status: certified  # draft | review | approved | certified | deprecated
target: ">= 65%"
source_table: fact_lesson_plan_usage
dimensions: [school_id, region_id, grade, subject]
freshness_sla_hours: 4
sensitivity: internal  # public | internal | external_guarded
owner: pedagogy_team
lineage:
  silver: fact_lesson_plan_usage
  bronze: raw_app_events
```

## Code Conventions
- Type hints on all function signatures
- Pydantic models for all data structures
- `async def` for all tool functions
- Docstrings on all public functions — these become tool descriptions for the LLM
- No `print()` — use structured logging
- Use parameterized queries — never string-interpolate SQL
- BigQuery client as singleton via lifespan pattern — never create clients in tool functions

## Domain Context
- Taleemabad is a Pakistani EdTech platform with apps for teacher training and lesson plans
- FICO is the classroom observation framework (Sections B, C, D)
- Theory of Change: LP Adoption → Coaching → Classroom Practice → Teacher Behavior → Student Outcomes
- Regional behavior is config-driven, not code-deployed

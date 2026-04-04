# Taleemabad Data Governance MCP

A governed semantic layer between business teams and BigQuery. Ask a question in natural language, get the right number — every time, with full audit trail.

See [VISION.md](docs/VISION.md) for why this exists and where it's going.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Google Cloud SDK with BigQuery access
- Access to Taleemabad's BigQuery project

## Installation

```bash
git clone <repo-url>
cd Taleemabad-Data-MCP
uv sync
cp .env.example .env
# Edit .env — see CLAUDE.md for all environment variables
```

## Connect to Claude Code

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "uv",
      "args": ["run", "python", "-m", "taleemabad_data_mcp"],
      "env": {
        "BIGQUERY_PROJECT": "your-project",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/key.json"
      }
    }
  }
}
```

## Tools

| Tool | Purpose |
|------|---------|
| `execute_query` | Run a governed SQL query against BigQuery (with cost guardrails) |
| `list_datasets` | Browse allowed BigQuery datasets and their tables |
| `get_table_schema` | Get columns and types for a specific table |

## Example Interactions

> "What's the LP adoption rate this month?"

> "Show me FICO Section B scores for Rawalpindi schools, Q1 2026."

> "How is student proficiency rate calculated?"

> "I need teacher training completion by region but can't find a metric."

## Contributing

Internal Taleemabad project. See [CLAUDE.md](CLAUDE.md) for coding conventions.

1. Branch from `main`
2. Write tests (target 80%+ coverage)
3. Run lint + tests before pushing
4. PR with description — metric changes need architect approval

## Documentation

| Document | What you'll learn |
|----------|-------------------|
| [VISION.md](docs/VISION.md) | Why this exists, principles, governance design, roadmap |
| [CLAUDE.md](CLAUDE.md) | Tech stack, project structure, commands, coding conventions |
| [Research](docs/research/) | Background research (5 reports) |

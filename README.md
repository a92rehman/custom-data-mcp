# Taleemabad Data Governance MCP

A governed semantic layer between business teams and BigQuery. Ask a question in natural language, get the right number — every time, with full audit trail.

See [VISION.md](docs/VISION.md) for why this exists and where it's going.

## Install

One-time setup. Takes ~2 minutes. You need Python 3.11+, [Claude Code](https://claude.ai/code), and the service account key file (ask the data team).

### macOS / Linux

```bash
# 1. Install
python3 -m venv ~/.claude/taleemabad-venv
~/.claude/taleemabad-venv/bin/pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Your Name" --credentials /path/to/niete-bq-prod-key.json

# 2. Connect a project
cd your-project
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp init

# 3. Open Claude Code
claude
```

### Windows (PowerShell)

```powershell
# 1. Install
python -m venv "$env:USERPROFILE\.claude\taleemabad-venv"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp setup --user "Your Name" --credentials "C:\path\to\niete-bq-prod-key.json"

# 2. Connect a project
cd your-project
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp init

# 3. Open Claude Code
claude
```

### Verify

Run `/mcp` in Claude Code — you should see `taleemabad-data · ✔ connected`.

Then ask a question:
> How many active teachers are in ICT/Islamabad?

## Update

```bash
# macOS / Linux
~/.claude/taleemabad-venv/bin/pip install --upgrade "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Your Name" --credentials /path/to/key.json

# Windows
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install --upgrade "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp setup --user "Your Name" --credentials "C:\path\to\key.json"
```

## Uninstall

```bash
# macOS / Linux
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp uninstall
rm -rf ~/.claude/taleemabad-venv

# Windows
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp uninstall
Remove-Item "$env:USERPROFILE\.claude\taleemabad-venv" -Recurse -Force
```

Delete `.mcp.json` from any projects where you ran `init`.

## Tools

| Tool | Purpose |
|------|---------|
| `execute_query` | Run a governed SQL query against BigQuery (with cost guardrails + audit) |
| `list_datasets` | Browse allowed BigQuery datasets and their tables |
| `get_table_schema` | Get columns and types for a specific table |
| `check_table_freshness` | Check when a table was last modified |

## Example Interactions

> "What's the LP adoption rate this month?"

> "Show me FICO Section B scores for ICT schools, Q1 2026."

> "How is student proficiency rate calculated?"

> "I need teacher training completion by region but can't find a metric."

## Activity Tracking

Every query is logged to BigQuery (`mcp_audit.activity_log`) and locally (`~/.claude/taleemabad-logs/activity.jsonl`). The data team can query the audit table to see:
- Who asked what questions, when
- Which domains are most queried
- BigQuery cost per user
- Questions that didn't match any rule (gap detection)

## Developer Setup

For contributing to this project:

```bash
git clone https://github.com/Orenda-Project/taleemabad-data-mcp.git
cd taleemabad-data-mcp
uv sync --extra dev
cp .env.example .env
# Edit .env — see CLAUDE.md for all environment variables
```

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

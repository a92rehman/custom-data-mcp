# Taleemabad Data Governance MCP

A governed semantic layer between business teams and BigQuery. Ask a question in natural language, get the right number — every time, with full audit trail.

See [VISION.md](docs/VISION.md) for why this exists and where it's going.

## Install

One-time setup. Takes ~2 minutes. You need Python 3.11+, Git, [Claude Code](https://claude.ai/code), and the service account key file (ask the data team).

**For v0.6.0+:** See **[CROSS_PLATFORM_SETUP.md](docs/CROSS_PLATFORM_SETUP.md)** for all platforms (Windows, macOS, iOS).

**Upgrading from v0.5.x?** See **[MIGRATION_v0.5_to_v0.6.md](docs/MIGRATION_v0.5_to_v0.6.md)** — one config change fixes MCP server on all platforms.

**Detailed reference:** See **[INSTALL.md](docs/INSTALL.md)** for comprehensive step-by-step instructions with troubleshooting.

### Quick Start (macOS / Linux)

```bash
python3 -m venv ~/.claude/taleemabad-venv
~/.claude/taleemabad-venv/bin/pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Your Name" --credentials /path/to/key.json

cd your-project
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp init
claude
```

### Quick Start (Windows PowerShell)

```powershell
python -m venv "$env:USERPROFILE\.claude\taleemabad-venv"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp setup --user "Your Name" --credentials "C:\path\to\key.json"

cd your-project
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp init
claude
```

> **Do NOT run `taleemabad-data-mcp` directly.** Always use the full path with the venv. See [INSTALL.md](docs/INSTALL.md) for details.

### Verify

Run `/mcp` in Claude Code — you should see `taleemabad-data · connected`.

Then ask: *"How many active PRIMARY teachers are in ICT/Islamabad?"*

### Check Version

```bash
# macOS / Linux
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp version

# Windows
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp version
```

Or ask Claude Code: **"What version of the data MCP am I running?"**

## Update

No need to re-enter your name or credentials:

```bash
# macOS / Linux
~/.claude/taleemabad-venv/bin/pip install --force-reinstall "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp upgrade

# Windows
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install --force-reinstall "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp upgrade
```

Restart Claude Code and check the version to confirm.

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
| `execute_query` | Run a governed SQL query against BigQuery (cost guardrails + audit) |
| `list_datasets` | Browse allowed BigQuery datasets and their tables |
| `get_table_schema` | Get columns and types for a specific table |
| `check_table_freshness` | Check when a table was last modified |
| `submit_feedback` | Submit optional thumbs up/down feedback on a query result |
| `get_version` | Check the installed MCP version, user, and project info |

## Regions

| Region | Status | Datasets |
|--------|--------|----------|
| ICT/Islamabad | Complete | `tbproddb` |
| Rawalpindi | Complete | `RUMI_DB` + `TaleemHub_DB` |
| Moawin | Not yet available | — |

## Example Interactions

> "What's the LP adoption rate this month?"

> "Show me FICO Section B scores for ICT schools, Q1 2026."

> "How many teachers passed Level 1 training?"

> "Show me reading assessment results for Rawalpindi."

## Observability Dashboard

A Streamlit dashboard tracks MCP adoption, quality, and cost. Deploy on Railway or run locally:

```bash
pip install "taleemabad-data-mcp[dashboard]"
python -m taleemabad_data_mcp dashboard
```

Pages: Overview, Query Analytics, Feedback, Cost, Errors, Data Freshness.

## Activity Tracking

Every query is logged to BigQuery (`mcp_audit.activity_log`) and locally (`~/.claude/taleemabad-logs/activity.jsonl`). Users can optionally give thumbs up/down feedback stored in `mcp_audit.query_feedback`. The dashboard visualizes:
- Active users and query volume trends
- Satisfaction rate (expectation vs reality)
- Level of confidence (governance success + satisfaction)
- BigQuery cost per user and domain
- Error rates and governance gaps
- Data freshness status

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
| [INSTALL.md](docs/INSTALL.md) | Step-by-step setup with troubleshooting |
| [VISION.md](docs/VISION.md) | Why this exists, principles, governance design, roadmap |
| [CLAUDE.md](CLAUDE.md) | Tech stack, project structure, commands, coding conventions |
| [Research](docs/research/) | Background research (5 reports) |

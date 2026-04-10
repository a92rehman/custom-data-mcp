# Taleemabad Data Governance MCP

A governed semantic layer between business teams and BigQuery. Ask a question in natural language, get the right number — every time, with full audit trail.

See [VISION.md](docs/VISION.md) for why this exists and where it's going.

## Prerequisites

Before installing, make sure you have:

1. **Claude Code** — [Install here](https://docs.anthropic.com/en/docs/claude-code/overview)
2. **GCP Service Account Key** — ask the data team for `niete-bq-prod-48ae5260d1ea.json`

> **Note:** You do NOT need to install Python, Node.js, or uv yourself. The plugin handles everything automatically.

## Install (All Platforms)

Works on **Windows**, **macOS**, **Linux**, and **iOS** (via Claude Code terminal).

### Step 1: Add Marketplace and Install Plugin

Open your terminal and run these two commands:

```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

The first command registers the Orenda-Project repository as a plugin source.
The second installs the plugin (agents, slash commands, governance rules, AND the MCP server).

### Step 2: Copy Credentials

Copy `niete-bq-prod-48ae5260d1ea.json` (from the data team) into your project directory.

### Step 3: Run Setup (One Time)

Open Claude Code in your project directory and type:

```
/taleemabad-setup
```

The setup will ask for your **name** (for audit logs) and sync governance rules. That's it.

### Step 4: Restart Claude Code

Close and reopen Claude Code (or press `Ctrl+R`).

### Step 5: Verify

Type `/mcp` in Claude Code. You should see:

```
taleemabad-data · connected
```

Then try: *"How many active PRIMARY teachers are in ICT/Islamabad?"*

## Add to Another Project

After setup, adding the MCP to a new project is one step:

1. Copy `niete-bq-prod-48ae5260d1ea.json` to the new project directory
2. Done — the plugin provides the MCP config automatically

No `/taleemabad-init` needed. No `.mcp.json` generation. Just copy the credentials file.

## Update

**Rules and agents auto-update** on every Claude Code session start. No action needed.

To manually force a plugin update:

```bash
claude plugin update taleemabad-data@Orenda-Project
```

## Uninstall

```bash
claude plugin uninstall taleemabad-data@Orenda-Project
claude plugin marketplace remove Orenda-Project
```

## Tools

| Tool | Purpose |
|------|---------|
| `execute_query` | Run a governed SQL query against BigQuery (cost guardrails + audit) |
| `list_datasets` | Browse allowed BigQuery datasets and their tables |
| `get_table_schema` | Get columns and types for a specific table |
| `check_table_freshness` | Check when a table was last modified |
| `submit_feedback` | Submit thumbs up/down feedback on a query result |
| `get_version` | Check installed version, user, and project info |
| `preview_table` | Quick peek at table data (10 rows, with SQL injection protection) |
| `save_query_results` | Export governed query results to CSV or JSON |
| `describe_data` | Descriptive statistics on governed query results |

## Regions

| Region | Status | Datasets |
|--------|--------|----------|
| ICT/Islamabad | Complete | `tbproddb` |
| Rawalpindi | Complete | `RUMI_DB` + `TaleemHub_DB` |
| Moawin | Not yet available | — |

## Example Queries

> "What's the LP adoption rate this month?"

> "Show me FICO Section B scores for ICT schools, Q1 2026."

> "How many teachers passed Level 1 training?"

> "Show me reading assessment results for Rawalpindi."

## Troubleshooting

### Plugin not found after install
Make sure you ran both commands:
```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

### /taleemabad-setup not recognized
Restart Claude Code after installing the plugin. The slash command is provided by the plugin.

### MCP shows "credentials not found"
Copy `niete-bq-prod-48ae5260d1ea.json` to your project directory. The MCP server starts automatically but needs this file to connect to BigQuery.

### MCP shows "failed" in /mcp
- Check that `uv` is accessible: run `uv version` in your terminal
- If `uv` is not found, Claude Code ships it at `~/.claude/uv`

### "Git access required" error during setup
The repository is private. Ask IT to add your GitHub account to the [Orenda-Project](https://github.com/Orenda-Project) organization.

### Old `.mcp.json` from previous version
If you used a previous version (v0.11.0 or earlier), delete the `.mcp.json` file from your project directories. The plugin now provides this automatically.

## Observability Dashboard

A Streamlit dashboard tracks MCP adoption, quality, and cost:

```bash
pip install "taleemabad-data-mcp[dashboard]"
python -m taleemabad_data_mcp dashboard
```

Pages: Overview, Query Analytics, Feedback, Cost, Errors, Data Freshness.

## Developer Setup

For contributing to this project:

```bash
git clone https://github.com/Orenda-Project/taleemabad-data-mcp.git
cd taleemabad-data-mcp
uv sync --extra dev
cp .env.example .env
# Edit .env — see CLAUDE.md for all environment variables
```

## Documentation

| Document | What you'll learn |
|----------|-------------------|
| [VISION.md](docs/VISION.md) | Why this exists, principles, governance design, roadmap |
| [CLAUDE.md](CLAUDE.md) | Tech stack, project structure, commands, coding conventions |
| [Research](docs/research/) | Background research (5 reports) |

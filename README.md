# Taleemabad Data Governance MCP

A governed semantic layer between business teams and BigQuery. Ask a question in natural language, get the right number — every time, with full audit trail.

See [VISION.md](docs/VISION.md) for why this exists and where it's going.

## Prerequisites

Before installing, make sure you have:

1. **Claude Code** — [Install here](https://docs.anthropic.com/en/docs/claude-code/overview)
2. **Node.js 18+** — [Install here](https://nodejs.org/) (needed for bigquery-analytics MCP)
3. **Git** — [Install here](https://git-scm.com/downloads)
4. **GCP Service Account Key** — ask the data team for `niete-bq-prod-*.json`

> **Note:** You do NOT need to install Python or uv yourself. The setup wizard handles that automatically.

## Install (All Platforms)

Works on **Windows**, **macOS**, **Linux**, and **iOS** (via Claude Code terminal).

### Step 1: Add Marketplace and Install Plugin

Open your terminal and run these two commands:

```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

The first command registers the Orenda-Project repository as a plugin source.
The second installs the plugin (agents, slash commands, governance rules).

### Step 2: Run Setup

Open Claude Code in any project directory and type:

```
/taleemabad-setup
```

The setup wizard will:
- Download `uv` (Python package manager) if needed
- Ask for your **name** (for audit logs)
- Ask for the **path to your GCP service account JSON file**
- Write `.mcp.json` to your current project
- Pre-download the data package (~30-60 seconds first time)

### Step 3: Restart Claude Code

Close and reopen Claude Code (or press `Ctrl+R`).

### Step 4: Verify

Type `/mcp` in Claude Code. You should see:

```
taleemabad-data · connected
bigquery-analytics · connected
```

Then try: *"How many active PRIMARY teachers are in ICT/Islamabad?"*

## Add to Another Project

After setup, adding the MCP to a new project takes seconds:

```
/taleemabad-init
```

This reads your saved credentials and writes `.mcp.json` to the current project. Restart Claude Code to connect.

## Update

**Rules and agents auto-update** on every Claude Code session start. No action needed.

To manually force a plugin update:

```bash
claude plugin update taleemabad-data@Orenda-Project
```

To update the MCP server version in a project (updates `.mcp.json` to latest tag):

```
/taleemabad-setup
```

## Uninstall

```bash
claude plugin uninstall taleemabad-data@Orenda-Project
claude plugin marketplace remove Orenda-Project
```

Then delete `.mcp.json` from any projects where you ran setup or init.

## Tools

| Tool | Source | Purpose |
|------|--------|---------|
| `execute_query` | taleemabad-data | Run a governed SQL query against BigQuery (cost guardrails + audit) |
| `list_datasets` | taleemabad-data | Browse allowed BigQuery datasets and their tables |
| `get_table_schema` | taleemabad-data | Get columns and types for a specific table |
| `check_table_freshness` | taleemabad-data | Check when a table was last modified |
| `submit_feedback` | taleemabad-data | Submit thumbs up/down feedback on a query result |
| `get_version` | taleemabad-data | Check installed version, user, and project info |
| BigQuery tools | bigquery-analytics | Raw BigQuery access for analysis, trends, charts |

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

### MCP shows "failed" in /mcp
- Check that your GCP credentials file exists at the path you provided
- Check that `uv` is accessible: run `uv version` in your terminal
- If `uv` is not found, run `/taleemabad-setup` again — it will download it

### "Git access required" error during setup
The repository is private. Ask IT to add your GitHub account to the [Orenda-Project](https://github.com/Orenda-Project) organization.

### bigquery-analytics shows "failed"
This MCP requires Node.js. Install it from [nodejs.org](https://nodejs.org/).

### .mcp.json and git
`.mcp.json` contains your credentials path. Add it to `.gitignore` if your project is version-controlled:
```
echo ".mcp.json" >> .gitignore
```

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

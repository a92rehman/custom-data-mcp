# Taleemabad Data Governance MCP

A governed semantic layer between business teams and BigQuery. Ask a question in natural language, get the right number — every time, with full audit trail.

See [VISION.md](docs/VISION.md) for why this exists and where it's going.

## Prerequisites

Before installing, make sure you have:

1. **Claude Code** — [Install here](https://docs.anthropic.com/en/docs/claude-code/overview)
2. **Work email** — must be `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`

> **Note:** You do NOT need Python, Node.js, uv, or any credentials file. The MCP server runs remotely — just install the plugin and go.

## Install (All Platforms)

Works on **Windows**, **macOS**, **Linux**, and **iOS** (via Claude Code terminal).

### Step 1: Add Marketplace and Install Plugin

Open your terminal and run these two commands:

```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

The first command registers the Orenda-Project repository as a plugin source.
The second installs the plugin (agents, slash commands, and governance rules).

### Step 2: Run Setup (One Time)

Open Claude Code in any project directory and type:

```
/taleemabad-setup
```

The setup will ask for your **work email** (for audit logs) and sync governance rules. That's it.

### Step 3: Restart Claude Code

Close and reopen Claude Code (or press `Ctrl+R`).

### Step 4: Verify

Type `/mcp` in Claude Code. You should see:

```
taleemabad-data · connected
```

Then try: *"How many active PRIMARY teachers are in ICT/Islamabad?"*

## Add to Another Project

After setup, the MCP works in **every project automatically** — no extra steps needed. The plugin connects to the remote server; no per-project credentials required.

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
| `list_datasets` | Browse all BigQuery datasets and their tables (auto-discovered) |
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
| Moawin/Akhuwat | Complete | `neondb` + `zavia1` |

## Example Queries

> "What's the LP adoption rate this month?"

> "Show me FICO Section B scores for ICT schools, Q1 2026."

> "How many teachers passed Level 1 training?"

> "Show me reading assessment results for Rawalpindi."

## Architecture

```
User's Machine                              Railway
┌──────────────────────────┐     HTTPS     ┌──────────────────────┐
│ Claude Code               │─────────────>│ MCP Server           │
│  ├─ Plugin                │              │  ├─ FastMCP (HTTP)    │
│  │   ├─ agents/           │              │  ├─ BigQuery client   │
│  │   ├─ rules/            │              │  ├─ Audit logger      │
│  │   ├─ commands/         │              │  ├─ Cost estimator    │
│  │   └─ .mcp.json (URL)  │              │  └─ Feedback logger   │
│  └─ ~/.claude/ (email)    │              └──────────────────────┘
└──────────────────────────┘
```

- **Plugin** runs locally: agents, governance rules, slash commands
- **MCP server** runs on Railway: BigQuery access, audit logging, cost guardrails
- **No local dependencies** needed — no Python, no credentials file

## Troubleshooting

### Plugin not found after install
Make sure you ran both commands:
```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

### /taleemabad-setup not recognized
Restart Claude Code after installing the plugin. The slash command is provided by the plugin.

### MCP shows "Setup required"
Run `/taleemabad-setup` and enter your work email.

### MCP shows "Unauthorized domain"
You must use a work email ending with `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`.

### MCP shows "failed" or "disconnected" in /mcp
- Check your internet connection
- The remote server may be restarting — wait a minute and try again
- Run `/mcp` to see the connection status

### "Git access required" error during setup
The repository is private. Ask IT to add your GitHub account to the [Orenda-Project](https://github.com/Orenda-Project) organization.

### Upgrading from v0.14 or earlier
Previous versions required a credentials file and local Python. These are no longer needed:
- Delete `niete-bq-prod-48ae5260d1ea.json` from your project directories
- Delete any old `.mcp.json` files from project directories
- Run `/taleemabad-setup` again to enter your email (replaces the old name-based setup)

## Observability Dashboard

A Streamlit dashboard tracks MCP adoption, quality, and cost:

```bash
pip install "taleemabad-data-mcp[dashboard]"
python -m taleemabad_data_mcp dashboard
```

Pages: Overview, Query Analytics, Feedback, Cost, Errors, Data Freshness, Governance.

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

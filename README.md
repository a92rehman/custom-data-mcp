# Taleemabad Data Governance MCP

A governed semantic layer between business teams and BigQuery. Ask a question in natural language, get the right number — every time, with full audit trail.

See [VISION.md](docs/VISION.md) for why this exists and where it's going.

---

## Prerequisites

You need **three things** before installing:

### 1. An IDE with Terminal Access

Any of these works:

| IDE | Download | Notes |
|-----|----------|-------|
| **VS Code** | [code.visualstudio.com](https://code.visualstudio.com/) | Free, most common |
| **Cursor** | [cursor.com](https://cursor.com/) | AI-native editor |
| **Windsurf** | [windsurf.com](https://windsurf.com/) | AI-native editor |
| **Terminal only** | Built-in on macOS/Linux, Windows Terminal on Windows | No IDE needed |

You just need a terminal to run commands. The IDE itself doesn't matter — Claude Code runs in the terminal.

### 2. Claude Code (CLI)

Claude Code is Anthropic's command-line tool. Install it:

```bash
# macOS / Linux
npm install -g @anthropic-ai/claude-code

# Windows (in PowerShell as Administrator)
npm install -g @anthropic-ai/claude-code
```

**Requires Node.js 18+.** If you don't have Node.js:
- Download from [nodejs.org](https://nodejs.org/) (LTS version recommended)
- Or use `winget install OpenJS.NodeJS.LTS` (Windows) / `brew install node` (macOS)

After installing, verify it works:

```bash
claude --version
```

### 3. Anthropic Subscription

Claude Code requires an **Anthropic API subscription** (separate from claude.ai chat subscription):

| Plan | Cost | What You Get |
|------|------|-------------|
| **Claude Pro** | $20/month | Includes Claude Code usage with limits |
| **Claude Max** | $100/month | Higher Claude Code usage limits |
| **API Pay-as-you-go** | Usage-based | Set `ANTHROPIC_API_KEY` env var |

Sign up at [console.anthropic.com](https://console.anthropic.com/) or use your existing claude.ai Pro/Max subscription.

**First time using Claude Code?** Run `claude` in your terminal — it will walk you through authentication.

### 4. Work Email

Your email must be one of:
- `@taleemabad.com`
- `@niete.edu.pk`
- `@niete.pk`

This is used for audit logging. The MCP server validates your domain.

---

## Install

Works on **Windows**, **macOS**, **Linux**, and **iOS** (via Claude Code terminal).

### Step 1: Add Marketplace and Install Plugin

Open your terminal and run:

```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

The first command registers the Orenda-Project repository as a plugin source.
The second installs the plugin (agents, slash commands, governance rules, and MCP server connection).

**Private repository?** You need GitHub access to the [Orenda-Project](https://github.com/Orenda-Project) organization. Ask IT if the install fails with a git error.

### Step 2: Run Setup (One Time)

Open Claude Code in any project directory and type:

```
/taleemabad-setup
```

The setup will ask for your **work email** (for audit logs) and sync governance rules to your machine.

### Step 3: Restart Claude Code

Close and reopen Claude Code, or press `Ctrl+R` to reload.

### Step 4: Verify

Type `/mcp` in Claude Code. You should see:

```
taleemabad-data · connected
```

Then try: *"How many active PRIMARY teachers are in ICT/Islamabad?"*

---

## After Install: How to Use

Once installed, the plugin works **in every project automatically** — no per-project setup needed.

### Ask Questions in Natural Language

Just type your question in Claude Code:

> "What's the LP adoption rate this month?"

> "Show me FICO Section B scores for ICT schools, Q1 2026."

> "How many teachers passed Level 1 training?"

> "Show me reading assessment results for Rawalpindi."

> "What's the average ACR score by designation?"

The AI reads governance rules, generates the correct SQL, runs it against BigQuery with cost guardrails, and returns results with full audit logging.

### Available Slash Commands

| Command | What It Does |
|---------|-------------|
| `/taleemabad-setup` | Save your email + sync governance rules (one-time) |
| `/mcp` | Check MCP connection status |

---

## Update

### Auto-Updates

**Governance rules and agents auto-update** every time you start a new Claude Code session. No action needed for day-to-day use.

### When to Manually Update

Update manually when:
- You're told a new version is available
- A new region or dataset has been added
- You're experiencing issues that might be fixed in a newer version

```bash
claude plugin update taleemabad-data@Orenda-Project
```

### How to Check Your Version

In Claude Code, ask: *"What version of the MCP are you running?"*

Or the AI will call `get_version` which shows the current version, your email, and available datasets.

### Reinstall (If Update Fails)

If the update command doesn't work (e.g., locked directory on Windows):

1. Close **all** Claude Code windows and terminals
2. Open a fresh terminal (not Claude Code) and run:

```bash
claude plugin uninstall taleemabad-data@Orenda-Project
claude plugin marketplace remove Orenda-Project
```

3. Then reinstall:

```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

4. Run `/taleemabad-setup` again in Claude Code.

---

## Uninstall

```bash
claude plugin uninstall taleemabad-data@Orenda-Project
claude plugin marketplace remove Orenda-Project
```

This removes the plugin, agents, rules, and MCP connection. Your email config at `~/.claude/` is not removed.

---

## Tools

The MCP server provides 9 tools that Claude Code uses automatically:

| Tool | Purpose |
|------|---------|
| `execute_query` | Run a governed SQL query against BigQuery (cost guardrails + audit) |
| `list_datasets` | Browse all BigQuery datasets and their tables (auto-discovered) |
| `get_table_schema` | Get columns and types for a specific table |
| `check_table_freshness` | Check when a table was last modified |
| `submit_feedback` | Submit thumbs up/down feedback on a query result |
| `get_version` | Check installed version, user, and project info |
| `preview_table` | Quick peek at table data (10 rows, SQL injection protected) |
| `save_query_results` | Export governed query results to CSV or JSON |
| `describe_data` | Descriptive statistics on governed query results |

You don't call these directly — Claude Code picks the right tool based on your question.

---

## Regions & Datasets

| Region | Status | Datasets | What's Covered |
|--------|--------|----------|----------------|
| ICT/Islamabad | Complete | `tbproddb` | Teachers, lesson plans, coaching/FICO, training, ACR/promotion, student results |
| Rawalpindi | Complete | `RUMI_DB` + `TaleemHub_DB` | Teachers, AI coaching, lesson plans, reading assessments, ASER |
| Moawin/Akhuwat | Complete | `Muawin_Akhuwat_db` + `Zavia_db` | Teachers, schools, attendance, training, AI coaching, lesson plans, reading assessments, student scores |

All datasets accessible to the service account are available dynamically — no configuration needed when new datasets are migrated to BigQuery.

---

## Architecture

```
User's Machine                              Railway (Cloud)
+--------------------------+     HTTPS     +----------------------+
| Claude Code              |-------------->| MCP Server           |
|  +- Plugin               |              |  +- FastMCP (HTTP)    |
|  |   +- agents/          |              |  +- BigQuery client   |
|  |   +- rules/           |              |  +- Audit logger      |
|  |   +- commands/        |              |  +- Cost estimator    |
|  |   +- .mcp.json (URL)  |              |  +- Feedback logger   |
|  +- ~/.claude/ (email)   |              +----------------------+
+--------------------------+                        |
                                                    v
                                            Google BigQuery
                                            (niete-bq-prod)
```

- **Plugin** runs locally: agents read governance rules and generate correct SQL
- **MCP server** runs on Railway: executes queries, enforces cost guardrails, logs audits
- **No local dependencies** needed — no Python, no credentials file, no BigQuery access

---

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

### "Git access required" error during install
The repository is private. Ask IT to add your GitHub account to the [Orenda-Project](https://github.com/Orenda-Project) organization.

### Windows: "directory locked" during update
Close all Claude Code windows and terminals, then retry. The plugin directory gets locked by running processes.

### Upgrading from v0.14 or earlier
Previous versions required a credentials file and local Python. These are no longer needed:
- Delete `niete-bq-prod-48ae5260d1ea.json` from your project directories
- Delete any old `.mcp.json` files from project directories
- Run `/taleemabad-setup` again to enter your email

---

## Observability Dashboard

A live Streamlit dashboard tracks MCP usage, quality, and cost. Deployed on Railway — ask the data team for the URL.

Pages: Overview, Query Analytics, Feedback, Cost, Errors, Data Freshness, Governance.

---

## Developer Setup

For contributing to this project (not needed for regular users):

```bash
git clone https://github.com/Orenda-Project/taleemabad-data-mcp.git
cd taleemabad-data-mcp
uv sync --extra dev
cp .env.example .env
# Edit .env — see CLAUDE.md for all environment variables
```

---

## Documentation

| Document | What You'll Learn |
|----------|-------------------|
| [VISION.md](docs/VISION.md) | Why this exists, governance principles, roadmap |
| [CLAUDE.md](CLAUDE.md) | Tech stack, project structure, commands, coding conventions |
| [Research](docs/research/) | Background research (5 reports) |

# Taleemabad Data Plugin

Governed BigQuery analytics for Claude Code. Enforces data governance, cost guardrails, and audit logging for Taleemabad data across ICT/Islamabad and Rawalpindi regions.

## Quick Install

**Unix (macOS/Linux):**
```bash
curl -sLO https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.sh
chmod +x install.sh && ./install.sh
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.ps1" -OutFile install.ps1
.\install.ps1
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (for analytics MCP)
- Git
- GCP service account key JSON file
- Claude Code installed

## What Gets Installed

- `~/.claude/plugins/taleemabad-data/` — plugin directory (this repo, cloned)
- `~/.claude/taleemabad-venv/` — dedicated Python venv with MCP server
- `~/.claude/taleemabad-data-mcp.env` — saved credentials and config

## Agents

- **data-analyst** — answers questions about teacher data, lesson plans, observations, training, student results
- **data-admin** — schema browsing, table freshness, audit log queries, cost analysis

## Auto-Update

Rules and agents update automatically each time Claude Code opens. To pin a version:
```bash
export TALEEMABAD_PIN_VERSION=v1.0.0
```

## Troubleshooting

Run the data-admin agent and ask "what version am I running?" for diagnostics.

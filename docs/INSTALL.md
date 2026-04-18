# Installation Guide

See the [README](../README.md) for complete installation instructions.

## Quick Reference

```bash
# 1. Add marketplace and install plugin
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project

# 2. Open Claude Code and run setup (one time, for your email)
/taleemabad-setup

# 3. Restart Claude Code, verify:
/mcp
```

## Prerequisites

- Node.js 18+ and Claude Code CLI
- Anthropic subscription (Pro, Max, or API)
- GitHub access to [Orenda-Project](https://github.com/Orenda-Project)
- Work email (`@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`)

No local Python, credentials file, or BigQuery access needed — the MCP server runs remotely.

## How It Works

- The plugin includes agents that read governance rules and generate correct SQL
- Rules auto-update from GitHub on every session start (via session-start hook)
- The MCP server runs on Railway — queries execute remotely
- All queries are audited with your email, cost, and domain

## Migration from v0.14 or Earlier

If you used a previous version:
1. Delete old `.mcp.json` files from your project directories
2. Delete old credentials files (`niete-bq-prod-*.json`) — no longer needed
3. Run `/taleemabad-setup` once to save your email
4. Delete `~/.claude/taleemabad-venv/` if it exists (no longer needed)
5. Delete `~/.claude/rules/taleemabad/` if it exists (rules now live in the plugin)

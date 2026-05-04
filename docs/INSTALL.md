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

- The plugin includes four agents: `data-analyst` (governed queries), `data-admin` (diagnostics), `query-fixer` (auto-fix failed SQL), and `system-doctor` (infrastructure health)
- Rules auto-update from GitHub on every session start (via Python session-start hook)
- The session-start hook writes `~/.claude/taleemabad-rules-path` so agents can find rules regardless of your working directory
- If the hook detects issues (missing env, stale rules), the `system-doctor` agent auto-diagnoses on next session
- The MCP server runs on Railway — queries execute remotely
- All queries are audited with your email, cost, and domain
- Failed queries are automatically retried by the `query-fixer` agent (up to 3 attempts)
- Run `/taleemabad-doctor` anytime to check and fix plugin health

## Migration from v0.14 or Earlier

If you used a previous version:
1. Delete old `.mcp.json` files from your project directories
2. Delete old credentials files (`niete-bq-prod-*.json`) — no longer needed
3. Run `/taleemabad-setup` once to save your email
4. Delete `~/.claude/taleemabad-venv/` if it exists (no longer needed)
5. Delete `~/.claude/rules/taleemabad/` if it exists (rules now live in the plugin)
6. Delete `~/.claude/taleemabad-rules-path` if it exists (recreated automatically on next session)

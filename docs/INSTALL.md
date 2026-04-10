# Installation Guide

See the [README](../README.md) for complete installation instructions.

## Quick Reference

```bash
# 1. Add marketplace and install plugin
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project

# 2. Copy credentials file to your project directory
# (ask the data team for niete-bq-prod-48ae5260d1ea.json)

# 3. Restart Claude Code, then run:
/taleemabad-setup

# 4. Restart Claude Code again, verify:
/mcp
```

## Prerequisites

- Claude Code
- GCP service account key (ask data team for `niete-bq-prod-48ae5260d1ea.json`)

## For New Projects

Just copy `niete-bq-prod-48ae5260d1ea.json` to the project directory. No other steps needed.

## Migration from v0.11.0 or Earlier

If you used a previous version:
1. Delete old `.mcp.json` files from your project directories
2. Run `/taleemabad-setup` once (it will clean up old artifacts)
3. You can delete `~/.claude/taleemabad-venv/` manually (no longer needed)

# Installation Guide

See the [README](../README.md) for complete installation instructions.

## Quick Reference

```bash
# 1. Add marketplace and install plugin
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project

# 2. Restart Claude Code, then run:
/taleemabad-setup

# 3. Restart Claude Code again, verify:
/mcp

# 4. For additional projects:
/taleemabad-init
```

## Prerequisites

- Claude Code
- Node.js 18+ (for bigquery-analytics MCP)
- Git
- GCP service account key (ask data team)

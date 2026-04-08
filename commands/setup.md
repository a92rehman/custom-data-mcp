---
name: taleemabad-setup
description: One-time setup for Taleemabad Data plugin — installs Python venv, configures credentials, and wires MCP server
---

Run the Taleemabad Data plugin setup. This is a one-time step after `claude install`.

## What this does
1. Creates a Python venv at `~/.claude/taleemabad-venv`
2. Installs the `taleemabad-data-mcp` package
3. Prompts for your name and GCP credentials path
4. Writes the configured `.mcp.json` to the plugin directory
5. Saves credentials to `~/.claude/taleemabad-data-mcp.env` for future upgrades

## Instructions for Claude

When this command is invoked:

1. Check if `~/.claude/taleemabad-venv` exists
   - If yes: ask "Venv already exists. Re-run setup? (y/n)"
   - If no: proceed

2. Determine OS:
   - Windows: use `$env:USERPROFILE`, venv at `\Scripts\python.exe`
   - Unix: use `$HOME`, venv at `/bin/python`

3. Run setup script appropriate for OS:
   - Windows: run `.\install.ps1` from the plugin directory
   - Unix: run `bash install.sh` from the plugin directory

4. Tell the user to restart Claude Code when done.

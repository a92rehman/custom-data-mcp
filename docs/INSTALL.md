# Install Taleemabad Data MCP

One-time setup. Takes ~2 minutes.

## Prerequisites

- Python 3.11+
- [Claude Code](https://claude.ai/code) installed
- Service account key file (`niete-bq-prod-*.json`) — ask the data team if you don't have it

## Step 1: Install

**macOS / Linux:**
```bash
python3 -m venv ~/.claude/taleemabad-venv
~/.claude/taleemabad-venv/bin/pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Your Name" --credentials /path/to/niete-bq-prod-key.json
```

**Windows (PowerShell):**
```powershell
python -m venv "$env:USERPROFILE\.claude\taleemabad-venv"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp setup --user "Your Name" --credentials "C:\path\to\niete-bq-prod-key.json"
```

## Step 2: Connect a project

Go to any project where you want to use the data MCP and run:

**macOS / Linux:**
```bash
cd your-project
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp init
```

**Windows (PowerShell):**
```powershell
cd your-project
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp init
```

This creates `.mcp.json` in the project. Add it to `.gitignore` if you don't want it committed.

## Step 3: Verify

Open Claude Code in the project:
```bash
claude
```

Run `/mcp` — you should see `taleemabad-data · ✔ connected`.

Ask a question:
> How many active teachers are in ICT/Islamabad?

## Update

```bash
# macOS / Linux
~/.claude/taleemabad-venv/bin/pip install --upgrade "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Your Name" --credentials /path/to/key.json

# Windows
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install --upgrade "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp setup --user "Your Name" --credentials "C:\path\to\key.json"
```

## Uninstall

```bash
# macOS / Linux
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp uninstall
rm -rf ~/.claude/taleemabad-venv

# Windows
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp uninstall
Remove-Item "$env:USERPROFILE\.claude\taleemabad-venv" -Recurse -Force
```

Delete `.mcp.json` from any projects where you ran `init`.

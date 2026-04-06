# Install Taleemabad Data MCP

One-time setup. Takes ~2 minutes.

## Prerequisites

- Python 3.11+
- [Claude Code](https://claude.ai/code) installed
- Service account key file (`niete-bq-prod-*.json`) — ask the data team if you don't have it

## Step 1: Create environment and install

**macOS / Linux:**
```bash
python3 -m venv ~/.claude/taleemabad-venv
~/.claude/taleemabad-venv/bin/pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

**Windows (PowerShell):**
```powershell
python -m venv "$env:USERPROFILE\.claude\taleemabad-venv"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

## Step 2: Run setup

**macOS / Linux:**
```bash
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Your Name" --credentials /path/to/niete-bq-prod-key.json
```

**Windows (PowerShell):**
```powershell
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp setup --user "Your Name" --credentials "C:\path\to\niete-bq-prod-key.json"
```

## Step 3: Add MCP config to your project

Copy the `.mcp.json` file to any project where you want to use the data MCP:

**macOS / Linux:**
```bash
cd your-project
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "HOME_DIR/.claude/taleemabad-venv/bin/python",
      "args": ["-m", "taleemabad_data_mcp", "serve"],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/niete-bq-prod-key.json",
        "TALEEMABAD_USER": "Your Name",
        "TALEEMABAD_HOSTNAME": "your-machine"
      }
    }
  }
}
EOF
```
Replace `HOME_DIR` with your home directory (e.g., `/Users/yourname`).

**Windows:** Create `.mcp.json` in your project folder with:
```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "C:\\Users\\YOUR_USERNAME\\.claude\\taleemabad-venv\\Scripts\\python.exe",
      "args": ["-m", "taleemabad_data_mcp", "serve"],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb",
        "GOOGLE_APPLICATION_CREDENTIALS": "C:\\path\\to\\niete-bq-prod-key.json",
        "TALEEMABAD_USER": "Your Name",
        "TALEEMABAD_HOSTNAME": "your-machine"
      }
    }
  }
}
```

## Step 4: Verify

Open Claude Code in the project:
```bash
claude
```

Run `/mcp` — you should see `taleemabad-data · ✔ connected`.

Ask a question:
> How many active teachers are in ICT/Islamabad?

Claude will clarify, follow the governance rules, and execute the query.

## Update

Re-run Step 1 to get the latest version:

**macOS / Linux:**
```bash
~/.claude/taleemabad-venv/bin/pip install --upgrade "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

**Windows:**
```powershell
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install --upgrade "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

Rules update automatically — re-run Step 2 to refresh them.

## Uninstall

**macOS / Linux:**
```bash
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp uninstall
rm -rf ~/.claude/taleemabad-venv
```

**Windows:**
```powershell
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp uninstall
Remove-Item "$env:USERPROFILE\.claude\taleemabad-venv" -Recurse -Force
```

Also delete `.mcp.json` from any projects where you added it.

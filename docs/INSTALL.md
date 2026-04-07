# Install Taleemabad Data MCP

One-time setup. Takes ~2 minutes.

## What You Need

1. **Python 3.11+** — check with `python --version` in your terminal
2. **Claude Code** — install from https://claude.ai/code
3. **Service account key file** (`niete-bq-prod-*.json`) — ask the data team if you don't have it

## Setup (Windows)

Open **PowerShell** and run these commands one by one.

**IMPORTANT:** Replace `"Your Name"` with your actual name and `"C:\path\to\key.json"` with the actual path to your service account key file.

```powershell
# Step 1: Create Python environment (run once)
python -m venv "$env:USERPROFILE\.claude\taleemabad-venv"
```

```powershell
# Step 2: Install the package from GitHub
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

```powershell
# Step 3: Run setup (replace Your Name and path to key)
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp setup --user "Your Name" --credentials "C:\path\to\niete-bq-prod-key.json"
```

```powershell
# Step 4: Go to your project folder and connect it
cd C:\path\to\your-project
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp init
```

```powershell
# Step 5: Open Claude Code and verify
claude
# Then type: /mcp
# You should see: taleemabad-data · connected
```

> **Do NOT run `taleemabad-data-mcp` directly.** Always use the full path starting with `& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\..."`. The command is installed inside a dedicated Python environment, not on your system PATH.

## Setup (macOS / Linux)

Open **Terminal** and run these commands one by one.

```bash
# Step 1: Create Python environment
python3 -m venv ~/.claude/taleemabad-venv
```

```bash
# Step 2: Install the package
~/.claude/taleemabad-venv/bin/pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

```bash
# Step 3: Run setup (replace Your Name and path to key)
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp setup --user "Your Name" --credentials /path/to/niete-bq-prod-key.json
```

```bash
# Step 4: Go to your project and connect it
cd your-project
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp init
```

```bash
# Step 5: Open Claude Code and verify
claude
# Then type: /mcp
# You should see: taleemabad-data · connected
```

## Try It

After setup, ask a question in Claude Code:

> How many active PRIMARY teachers are in ICT/Islamabad?

> What is the LP adoption rate this week?

> Show me FICO Section B scores by school.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `'taleemabad-data-mcp' is not recognized` | Don't run the command directly. Use the full path: `& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp ...` |
| `python: command not found` | Install Python 3.11+ from https://python.org and make sure "Add to PATH" is checked during install |
| `/mcp` shows `taleemabad-data · not connected` | Re-run setup (Step 3) and make sure the credentials path is correct |
| `pip install` fails with permission error | Make sure you're using the venv pip, not system pip (the full path with `taleemabad-venv` in it) |
| Setup says "Already running from the installed environment" | This is fine — it means the package is already installed |

## Update

When the data team releases an update, you do NOT need to re-enter your name or credentials. Just two commands:

**Windows:**
```powershell
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\pip.exe" install --force-reinstall "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp upgrade
```

**macOS / Linux:**
```bash
~/.claude/taleemabad-venv/bin/pip install --force-reinstall "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp upgrade
```

The `upgrade` command reads your saved credentials from the first setup — no need to pass `--user` or `--credentials` again.

After upgrading, restart Claude Code and run `/mcp` to see the new version number.

## Uninstall

**Windows:**
```powershell
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp uninstall
Remove-Item "$env:USERPROFILE\.claude\taleemabad-venv" -Recurse -Force
```

**macOS / Linux:**
```bash
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp uninstall
rm -rf ~/.claude/taleemabad-venv
```

Also delete `.mcp.json` from any projects where you ran `init`.

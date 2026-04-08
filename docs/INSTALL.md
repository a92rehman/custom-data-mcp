# Install Taleemabad Data MCP

## Installing as a Claude Code Plugin

The recommended installation method for team members is the one-command plugin installer.
This installs the plugin globally in Claude Code and auto-updates rules on every session start.

### Unix (macOS/Linux)

```bash
curl -sLO https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.sh
chmod +x install.sh && ./install.sh
```

### Windows (PowerShell)

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Orenda-Project/taleemabad-data-mcp/main/plugin/install.ps1" -OutFile install.ps1
.\install.ps1
```

### Prerequisites

- Python 3.11+, Git, Node.js 18+ (for analytics MCP), GCP service account JSON, Claude Code

### Migrating from Manual Setup

If you previously installed via the manual setup (rules in `~/.claude/rules/taleemabad/`):

1. Run the install script above — it detects the old setup and offers to migrate
2. If not auto-removed: `rm -rf ~/.claude/rules/taleemabad/`
3. Edit `~/.claude/settings.json` — remove the `taleemabad-data` key from `mcpServers`
4. Restart Claude Code
5. Verify: ask "what version of taleemabad data am I running?"

### Pinning a Version

To prevent auto-updates:

```bash
export TALEEMABAD_PIN_VERSION=v1.0.0
```

---

## Manual Setup

One-time setup. Takes ~2 minutes.

## What You Need

1. **Python 3.11+** — check with `python --version` in your terminal
2. **Git** — check with `git --version` (needed to install from GitHub)
3. **Claude Code** — install from https://claude.ai/code
4. **Service account key file** (`niete-bq-prod-*.json`) — ask the data team if you don't have it

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
# Step 5: Restart Claude Code, then verify
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
# Step 5: Restart Claude Code, then verify
claude
# Then type: /mcp
# You should see: taleemabad-data · connected
```

## Try It

After setup, ask a question in Claude Code:

> How many active PRIMARY teachers are in ICT/Islamabad?

> What is the LP adoption rate this week?

> Show me FICO Section B scores by school.

## Check Version

**Windows:**
```powershell
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp version
```

**macOS / Linux:**
```bash
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp version
```

Or ask Claude Code: **"What version of the data MCP am I running?"**

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `'taleemabad-data-mcp' is not recognized` | Don't run the command directly. Use the full path: `& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp ...` |
| `python: command not found` | Install Python 3.11+ from https://python.org — make sure "Add to PATH" is checked during install |
| `git: command not found` | Install Git from https://git-scm.com/downloads |
| `/mcp` shows `taleemabad-data · failed` | The server crashed on startup. Run upgrade to get the latest fix: see Update section below. If it still fails, re-run setup (Step 3) with correct credentials path. |
| `/mcp` shows `taleemabad-data · not connected` | Re-run setup (Step 3) and make sure the credentials path is correct. Then restart Claude Code. |
| `pip install` fails with permission error | Make sure you're using the venv pip, not system pip (the full path with `taleemabad-venv` in it) |
| `pip install` fails with `error: subprocess-exited-with-error` | You may be missing Git. Install it from https://git-scm.com/downloads and try again. |
| Setup says "Already running from the installed environment" | This is fine — it means the package is already installed |
| MCP connected but queries fail with `Forbidden` | The service account key does not have BigQuery permissions. Ask the data team for the correct key file. |

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

After upgrading, **restart Claude Code** and run `/mcp` to verify the connection.

Check the new version:
```powershell
& "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -m taleemabad_data_mcp version
```

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

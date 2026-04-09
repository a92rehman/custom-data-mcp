# /taleemabad-setup

Set up the Taleemabad Data MCP server. This command runs the Python setup script which handles everything deterministically.

## Prerequisites
- `niete-bq-prod-48ae5260d1ea.json` (GCP service account key) must be in the current project directory
- Python 3.11+ must be installed
- Git must be installed (for pip install from GitHub)

## Steps

### Step 1: Check prerequisites
Verify the credentials file exists in the current directory:
```
python -c "import os; print('OK' if os.path.exists('niete-bq-prod-48ae5260d1ea.json') else 'MISSING')"
```

If MISSING, tell the user: "Copy `niete-bq-prod-48ae5260d1ea.json` (from the data team) into this project directory, then re-run /taleemabad-setup."
Stop.

### Step 2: Ask for name
Ask: "What is your name? (used for audit logs)"
Save as `user_name`.

### Step 3: Run the setup script
Run this single command (substitute the actual name):

On Windows:
```
python -m taleemabad_data_mcp setup --user "<user_name>"
```

On macOS/Linux:
```
python3 -m taleemabad_data_mcp setup --user "<user_name>"
```

**IMPORTANT:** If `python -m taleemabad_data_mcp` fails with "No module named taleemabad_data_mcp", the package needs to be installed first. Run:
```
pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```
Then retry the setup command.

The setup script will:
1. Create `~/.claude/taleemabad-venv/` and install the package
2. Copy governance rules to `~/.claude/rules/taleemabad/`
3. Write `.mcp.json` to the current project directory
4. Save your name for future `/taleemabad-init` use

### Step 4: Done
Tell the user:
```
Setup complete!

Restart Claude Code (close and reopen, or Ctrl+R).
Then run /mcp to verify:
  - taleemabad-data · connected
  - bigquery-analytics · connected

For other projects: copy niete-bq-prod-48ae5260d1ea.json there, then run /taleemabad-init
```

## Error handling

| Error | Fix |
|-------|-----|
| "No module named taleemabad_data_mcp" | Run `pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"` |
| "GCP credentials file not found" | Copy `niete-bq-prod-48ae5260d1ea.json` to project directory |
| "Python not found" | Install Python 3.11+ from python.org |
| pip install fails (auth) | User needs GitHub access to Orenda-Project org |

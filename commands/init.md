# /taleemabad-init

Add the Taleemabad Data MCP to the current project. Requires `/taleemabad-setup` to have been run once before.

## Prerequisites
- `/taleemabad-setup` has been run at least once (creates the venv and saves your name)
- `niete-bq-prod-48ae5260d1ea.json` must be in the current project directory

## Steps

### Step 1: Check prerequisites
Verify the credentials file exists:
```
python -c "import os; print('OK' if os.path.exists('niete-bq-prod-48ae5260d1ea.json') else 'MISSING')"
```

If MISSING, tell the user: "Copy `niete-bq-prod-48ae5260d1ea.json` into this project directory first."
Stop.

### Step 2: Run init
On Windows:
```
~/.claude/taleemabad-venv/Scripts/python.exe -m taleemabad_data_mcp init
```

On macOS/Linux:
```
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp init
```

**IMPORTANT:** Use the venv python, not the system python. The package is installed in the venv.

If the venv doesn't exist, tell the user: "Run `/taleemabad-setup` first."

### Step 3: Done
Tell the user:
```
Done! Restart Claude Code to connect.
Run /mcp to verify both MCPs are connected.
```

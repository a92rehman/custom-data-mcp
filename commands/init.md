# /taleemabad-init

Add the Taleemabad Data MCP to the current project. Reads credentials saved during /taleemabad-setup.

Perform all steps via Bash tool without asking the user to run any commands themselves.

## Steps

### Step 1: Read saved config
Run:
```
python -c "import os; p=os.path.expanduser('~/.claude/taleemabad-data-mcp.env'); print(open(p).read()) if os.path.exists(p) else print('NOT_FOUND')"
```

Parse `TALEEMABAD_USER` and `GOOGLE_APPLICATION_CREDENTIALS` from the output.

If NOT_FOUND, tell the user: "No saved config found. Run `/taleemabad-setup` first to configure your credentials."
Stop.

### Step 2: Verify venv exists
Run:
```
python -c "import os, platform, pathlib; p = pathlib.Path.home() / '.claude' / 'taleemabad-venv' / ('Scripts/python.exe' if platform.system()=='Windows' else 'bin/python'); print('OK' if p.exists() else 'NOT_FOUND')"
```

If NOT_FOUND, tell the user: "Taleemabad venv not found. Run `/taleemabad-setup` first to install the package."
Stop.

### Step 3: Check if .mcp.json already exists
Run: `python -c "import os; print('EXISTS' if os.path.exists('.mcp.json') else 'NOT_FOUND')"`

If EXISTS, ask: "This project already has .mcp.json. Overwrite it? (y/n)"
If no, stop.

### Step 4: Write .mcp.json

```python
import json, pathlib, platform

user_name = "<NAME_FROM_STEP_1>"
credentials_path = r"<CREDENTIALS_FROM_STEP_1>"

home = pathlib.Path.home()
if platform.system() == "Windows":
    python_path = str(home / ".claude" / "taleemabad-venv" / "Scripts" / "python.exe")
    parts = pathlib.Path(python_path).parts
    drive = parts[0][0].lower()
    python_bash = "/" + drive + "/" + "/".join(parts[1:])
else:
    python_bash = str(home / ".claude" / "taleemabad-venv" / "bin" / "python")

mcp = {
    "mcpServers": {
        "taleemabad-data": {
            "command": python_bash,
            "args": ["-m", "taleemabad_data_mcp", "serve"],
            "env": {
                "BIGQUERY_PROJECT": "niete-bq-prod",
                "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
                "GOOGLE_APPLICATION_CREDENTIALS": credentials_path,
                "TALEEMABAD_USER": user_name,
            }
        },
        "bigquery-analytics": {
            "command": "npx",
            "args": [
                "-y", "@ergut/mcp-bigquery-server@latest",
                "--project-id", "niete-bq-prod",
                "--key-file", credentials_path
            ]
        }
    }
}

pathlib.Path(".mcp.json").write_text(json.dumps(mcp, indent=2) + "\n", encoding="utf-8")
print(".mcp.json created.")
```

Run this as a `python -c "..."` Bash call with the actual values substituted.

### Step 5: Warn about .gitignore
Check if `.gitignore` exists and contains `.mcp.json`:
```
python -c "import os; gi = open('.gitignore').read() if os.path.exists('.gitignore') else ''; print('COVERED' if '.mcp.json' in gi else 'NOT_COVERED')"
```

If NOT_COVERED, tell the user:
> ".mcp.json contains your credentials path. Add `.mcp.json` to your `.gitignore` to avoid committing it."

### Step 6: Done
Tell the user:
```
Done! Restart Claude Code to connect.

After restart, run /mcp to verify:
  - taleemabad-data (governed queries)
  - bigquery-analytics (raw BigQuery access)

Then try: "How many primary teachers are in ICT Islamabad?"
```

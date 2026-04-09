# /taleemabad-init

Add the Taleemabad Data MCP to the current project. Reads credentials saved during /taleemabad-setup.

Perform all steps via Bash tool without asking the user to run any commands themselves.

## Steps

### Step 1: Read saved config
Run:
```
python -c "import os; p=os.path.expanduser('~/.claude/taleemabad-data-mcp.env'); print(open(p).read()) if os.path.exists(p) else print('NOT_FOUND')"
```

Parse `TALEEMABAD_USER`, `GOOGLE_APPLICATION_CREDENTIALS`, and `UV_COMMAND` from the output.

If NOT_FOUND, tell the user: "No saved config found. Run `/taleemabad-setup` first to configure your credentials."
Stop.

If `UV_COMMAND` is missing from the env file, detect it:
```
python -c "import shutil, os, platform, pathlib; p = shutil.which('uv'); print(p if p else (str(pathlib.Path.home() / '.claude' / ('uv.exe' if platform.system()=='Windows' else 'uv')) if (pathlib.Path.home() / '.claude' / ('uv.exe' if platform.system()=='Windows' else 'uv')).exists() else 'NOT_FOUND'))"
```
If NOT_FOUND, tell the user: "uv is not installed. Run `/taleemabad-setup` to install it."

### Step 2: Read plugin version
Run:
```
python -c "import glob, os; files = glob.glob(os.path.expanduser('~/.claude/plugins/cache/Orenda-Project/taleemabad-data/*/.current-version')); print(open(files[0]).read().strip()) if files else print('NOT_FOUND')"
```

If NOT_FOUND, fall back to reading the version from the package:
```
python -c "import importlib.metadata; print('v' + importlib.metadata.version('taleemabad-data-mcp'))"
```

If still NOT_FOUND, use `v0.6.3` as default.

### Step 3: Check if .mcp.json already exists
Run: `python -c "import os; print('EXISTS' if os.path.exists('.mcp.json') else 'NOT_FOUND')"`

If EXISTS, ask: "This project already has .mcp.json. Overwrite it? (y/n)"
If no, stop.

### Step 4: Write .mcp.json
Write the MCP config to the current project directory:

```python
import json, pathlib

version = "<VERSION_FROM_STEP_2>"  # e.g. v0.6.3
user_name = "<NAME_FROM_STEP_1>"
credentials_path = r"<CREDENTIALS_FROM_STEP_1>"
uv_command = "<UV_COMMAND_FROM_STEP_1>"  # "uv" or absolute path

mcp = {
    "mcpServers": {
        "taleemabad-data": {
            "command": uv_command,
            "args": [
                "run",
                "--with", f"git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@{version}",
                "--python", "3.11",
                "python", "-m", "taleemabad_data_mcp", "serve"
            ],
            "env": {
                "BIGQUERY_PROJECT": "niete-bq-prod",
                "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
                "GOOGLE_APPLICATION_CREDENTIALS": credentials_path,
                "TALEEMABAD_USER": user_name,
            }
        },
        "bigquery-analytics": {
            "command": "npx",
            "args": ["-y", "@ergut/bigquery-mcp@latest"],
            "env": {
                "GOOGLE_APPLICATION_CREDENTIALS": credentials_path,
                "BIGQUERY_PROJECT": "niete-bq-prod"
            }
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

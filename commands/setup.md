# /taleemabad-setup

Set up the Taleemabad Data MCP server on this computer. Perform all steps via Bash tool without asking the user to run any commands themselves.

## Steps

### Step 1: Detect OS
Run: `python -c "import platform; print(platform.system())"`
Save the OS (Windows/Darwin/Linux).

### Step 2: Check for saved config
Run: `python -c "import os; p=os.path.expanduser('~/.claude/taleemabad-data-mcp.env'); print(open(p).read()) if os.path.exists(p) else print('NOT_FOUND')"`

If saved config found, parse TALEEMABAD_USER and GOOGLE_APPLICATION_CREDENTIALS from it.
Show the saved values and ask: "Found saved config — Name: [name], Credentials: [path]. Use these? (y/n)"
If yes, skip Steps 3 and 4. If no, proceed to Step 3.

### Step 3: Ask for name
Ask: "What is your name? (used for audit logs)"
Save as user_name.

### Step 4: Check for credentials file
First check if `niete-bq-prod-48ae5260d1ea.json` exists in the current project directory:
```
python -c "import os; print('EXISTS' if os.path.exists('niete-bq-prod-48ae5260d1ea.json') else 'NOT_FOUND')"
```

If EXISTS: use `./niete-bq-prod-48ae5260d1ea.json` as the credentials path. Tell user: "Found GCP credentials in project directory."

If NOT_FOUND: ask the user: "GCP credentials file not found in this directory. Please copy `niete-bq-prod-48ae5260d1ea.json` (from the data team) into this project directory and re-run /taleemabad-setup."
Stop.

Save `credentials_path = "./niete-bq-prod-48ae5260d1ea.json"` — always use relative path so .mcp.json is portable.

### Step 5: Create venv and install package
Tell the user: "Installing Taleemabad Data MCP (this may take 1-2 minutes)..."

**Create the venv:**
```
python -m venv ~/.claude/taleemabad-venv --clear
```

**Install the package:**

On Windows:
```
~/.claude/taleemabad-venv/Scripts/pip.exe install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

On macOS/Linux:
```
~/.claude/taleemabad-venv/bin/pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

If install fails with authentication error, tell the user: "Git access to Orenda-Project org is required. Ask IT to add your GitHub account to the Orenda-Project organization, then re-run /taleemabad-setup."

**Verify the install:**

On Windows:
```
~/.claude/taleemabad-venv/Scripts/python.exe -m taleemabad_data_mcp version
```

On macOS/Linux:
```
~/.claude/taleemabad-venv/bin/python -m taleemabad_data_mcp version
```

Show the version output.

### Step 6: Write .mcp.json to current project
Determine the python path for .mcp.json (must be bash-compatible on Windows):

```python
import json, pathlib, platform

user_name = "<NAME>"
credentials_path = r"<CREDENTIALS_PATH>"

home = pathlib.Path.home()
if platform.system() == "Windows":
    python_path = str(home / ".claude" / "taleemabad-venv" / "Scripts" / "python.exe")
    # Convert to bash path: C:\Users\name\... -> /c/Users/name/...
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

### Step 7: Save env file
Save name and credentials for future use by `/taleemabad-init`:
```python
import pathlib
env_path = pathlib.Path.home() / ".claude" / "taleemabad-data-mcp.env"
env_path.write_text(
    f"TALEEMABAD_USER=<name>\n"
    f"GOOGLE_APPLICATION_CREDENTIALS=<path>\n",
    encoding="utf-8"
)
print("Config saved.")
```

### Step 8: Install governance rules
Copy the governance rules from the plugin cache to `~/.claude/rules/taleemabad/`:

```python
import shutil, pathlib, glob

plugin_dirs = glob.glob(str(pathlib.Path.home() / ".claude" / "plugins" / "cache" / "Orenda-Project" / "taleemabad-data" / "*" / "rules"))
if not plugin_dirs:
    print("WARNING: No rules found in plugin cache")
else:
    src = pathlib.Path(plugin_dirs[0])
    dest = pathlib.Path.home() / ".claude" / "rules" / "taleemabad"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"Governance rules installed to {dest}")
```

### Step 9: Warn about .gitignore
Check if the current project's `.gitignore` contains `.mcp.json`:
```
python -c "import os; gi = open('.gitignore').read() if os.path.exists('.gitignore') else ''; print('COVERED' if '.mcp.json' in gi else 'NOT_COVERED')"
```

If NOT_COVERED, tell the user:
> ".mcp.json contains your credentials path. Consider adding `.mcp.json` to your `.gitignore`."

### Step 10: Done
Tell the user:
```
Setup complete!

To activate: Restart Claude Code (close and reopen, or press Ctrl+R).

After restart, run /mcp to verify:
  - taleemabad-data (governed queries)
  - bigquery-analytics (raw BigQuery access)

Then try: "How many primary teachers are in ICT Islamabad?"

For other projects, run /taleemabad-init to add the MCP there too.
```

## Error handling summary

| Scenario | Action |
|----------|--------|
| Plugin not installed | Tell user to run `claude plugin marketplace add` + `claude plugin install` first |
| venv creation fails | Check Python 3.11+ is installed |
| pip install fails (auth) | Tell user to ask IT for GitHub org access |
| pip install fails (other) | Show error output, suggest checking network |
| Credentials file not found | Re-ask, do not write config |

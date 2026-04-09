# /taleemabad-setup

Set up the Taleemabad Data MCP server on this computer. Perform all steps via Bash tool without asking the user to run any commands themselves.

## Steps

### Step 1: Detect OS and architecture
Run: `python -c "import platform; print(platform.system(), platform.machine())"`
Save the OS (Windows/Darwin/Linux) and architecture (x86_64/arm64/aarch64).

### Step 2: Read installed version
Run: `python -c "import glob, os; files = glob.glob(os.path.expanduser('~/.claude/plugins/cache/Orenda-Project/taleemabad-data/*/.current-version')); print(open(files[0]).read().strip()) if files else print('NOT_FOUND')"`
Save the version string (e.g. `v0.6.3`).

If NOT_FOUND, tell the user: "Plugin not found. Run these two commands first, then re-run /taleemabad-setup:
```
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```"
Stop if not found.

### Step 3: Find or download uv

**First check if uv is already on PATH:**
```
python -c "import shutil; p = shutil.which('uv'); print(p if p else 'NOT_FOUND')"
```

If found on PATH, save `uv_command = "uv"` (use the PATH-based command).

If NOT on PATH, check if already downloaded to `~/.claude/`:
```
python -c "import os, platform, pathlib; p = pathlib.Path.home() / '.claude' / ('uv.exe' if platform.system()=='Windows' else 'uv'); print(p if p.exists() else 'NOT_FOUND')"
```

If found at `~/.claude/`, save `uv_command` as a **bash-compatible path**:
- On **Windows**, convert `C:\Users\name\.claude\uv.exe` to `/c/Users/name/.claude/uv.exe`
- On **macOS/Linux**, use the path as-is (e.g. `/Users/name/.claude/uv`)

To convert on Windows, run:
```
python -c "import pathlib; p = pathlib.Path(r'<WINDOWS_PATH>'); parts = p.parts; drive = parts[0][0].lower(); print('/' + drive + '/' + '/'.join(parts[1:]))"
```

If neither found, download it:

**Windows (x86_64):**
```python
import urllib.request, zipfile, os, pathlib
url = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
dest = pathlib.Path.home() / ".claude"
dest.mkdir(exist_ok=True)
zip_path = dest / "uv.zip"
print("Downloading uv (~10MB)...")
urllib.request.urlretrieve(url, zip_path)
with zipfile.ZipFile(zip_path) as z:
    for name in z.namelist():
        if name.endswith("uv.exe") and "/" not in name.replace("uv.exe",""):
            z.extract(name, dest)
            import shutil; shutil.move(str(dest / name), str(dest / "uv.exe"))
            break
zip_path.unlink()
print("uv downloaded to", dest / "uv.exe")
```

**Mac ARM (aarch64/arm64):** URL = `https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz`
**Mac Intel (x86_64):** URL = `https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-apple-darwin.tar.gz`
**Linux x86_64:** URL = `https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz`

For tar.gz files (Mac/Linux), extract with:
```python
import urllib.request, tarfile, os, pathlib, stat
dest = pathlib.Path.home() / ".claude"
dest.mkdir(exist_ok=True)
tgz_path = dest / "uv.tar.gz"
urllib.request.urlretrieve(url, tgz_path)
with tarfile.open(tgz_path) as t:
    for m in t.getmembers():
        if m.name.endswith("/uv") or m.name == "uv":
            m.name = "uv"
            t.extract(m, dest)
            break
tgz_path.unlink()
uv = dest / "uv"
uv.chmod(uv.stat().st_mode | stat.S_IEXEC)
print("uv downloaded to", uv)
```

After download, save `uv_command = <absolute path to downloaded uv>`.
Verify by running: `<uv_command> version` and show the output.

If download fails, tell the user: "Could not download uv automatically. Install uv from https://docs.astral.sh/uv/getting-started/installation/ and re-run /taleemabad-setup."

### Step 4: Check for old venv
Run: `python -c "import os; print(os.path.exists(os.path.expanduser('~/.claude/taleemabad-venv')))"`
If True: Tell the user "Found old Python environment at ~/.claude/taleemabad-venv — this is no longer needed." Ask: "Delete it to free up space? (y/n)"
If yes: `python -c "import shutil, os; shutil.rmtree(os.path.expanduser('~/.claude/taleemabad-venv')); print('Removed.')"`

### Step 5: Check for saved config
Run: `python -c "import os; p=os.path.expanduser('~/.claude/taleemabad-data-mcp.env'); print(open(p).read()) if os.path.exists(p) else print('NOT_FOUND')"`

If saved config found, parse TALEEMABAD_USER and GOOGLE_APPLICATION_CREDENTIALS from it.
Show the saved values and ask: "Found saved config — Name: [name], Credentials: [path]. Use these? (y/n)"
If yes, skip Steps 6 and 7. If no, proceed to Step 6.

### Step 6: Ask for name
Ask: "What is your name? (used for audit logs)"
Save as user_name.

### Step 7: Ask for credentials path
Ask: "Paste the full path to your GCP service account JSON file."

Validate the file exists:
```
python -c "import os; print('EXISTS' if os.path.exists(r'<path>') else 'NOT_FOUND')"
```

If NOT_FOUND, ask again with: "File not found at that path. Please check and paste the correct path."
Do not proceed until the file exists.

### Step 8: Write .mcp.json to current project
Write the MCP config to the **current project directory** (not settings.json):

```python
import json, pathlib

version = "<VERSION_FROM_STEP_2>"  # e.g. v0.6.3
user_name = "<NAME_FROM_STEP_6>"
credentials_path = r"<PATH_FROM_STEP_7>"
uv_command = "<UV_COMMAND_FROM_STEP_3>"  # "uv" if on PATH, or absolute path

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
            "args": ["-y", "@ergut/mcp-bigquery-server@latest"],
            "env": {
                "GOOGLE_APPLICATION_CREDENTIALS": credentials_path,
                "BIGQUERY_PROJECT": "niete-bq-prod"
            }
        }
    }
}

pathlib.Path(".mcp.json").write_text(json.dumps(mcp, indent=2) + "\n", encoding="utf-8")
print(".mcp.json created in current project.")
```

Run this as a `python -c "..."` Bash call with the actual values substituted. Do NOT use shell variables — embed the actual values directly in the Python string.

**IMPORTANT:** Use the `uv_command` value from Step 3:
- If uv was found on PATH: use `"uv"`
- If uv was downloaded to ~/.claude/: use the absolute path

### Step 9: Save env file
Save name, credentials, and uv command for future use by `/taleemabad-init`:
```python
import pathlib
env_path = pathlib.Path.home() / ".claude" / "taleemabad-data-mcp.env"
env_path.write_text(
    f"TALEEMABAD_USER=<name>\n"
    f"GOOGLE_APPLICATION_CREDENTIALS=<path>\n"
    f"UV_COMMAND=<uv_command>\n",
    encoding="utf-8"
)
print("Config saved.")
```

### Step 10: Warn about .gitignore
Check if the current project's `.gitignore` contains `.mcp.json`:
```
python -c "import os; gi = open('.gitignore').read() if os.path.exists('.gitignore') else ''; print('COVERED' if '.mcp.json' in gi else 'NOT_COVERED')"
```

If NOT_COVERED, tell the user:
> ".mcp.json contains your credentials path. Consider adding `.mcp.json` to your `.gitignore`."

### Step 11: Pre-warm uv cache
Tell the user: "Downloading data package (first-time setup, ~30-60 seconds)..."

Run: `<uv_command> run --with "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@<VERSION>" --python 3.11 python -m taleemabad_data_mcp version`

Use the same `uv_command` from Step 3.

If this fails with an authentication error, tell the user: "Git access to Orenda-Project org is required. Ask IT to add your GitHub account to the Orenda-Project organization, then re-run /taleemabad-setup."

If it succeeds, show the version output.

### Step 12: Done
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
| Plugin not installed | Tell user to run `claude plugin install taleemabad-data@Orenda-Project` first |
| uv download fails | Give manual install instructions |
| Credentials file not found | Re-ask, do not write config |
| Pre-warm auth error | Tell user to ask IT for GitHub org access |

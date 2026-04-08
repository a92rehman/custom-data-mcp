# Fast Setup via uv Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 15-minute Python venv + pip install setup flow with a uv-based approach that completes in under 2 minutes.

**Architecture:** The `/taleemabad-setup` slash command is rewritten so Claude downloads the `uv` binary (a self-contained ~10MB exe), asks the user 2 questions, writes `~/.claude/settings.json` safely using Python's json module, and pre-warms the package cache — all via Claude's Bash tool. No shell scripts, no venv, no pip. The `cli.py` `_mcp_server_config()` function is updated to emit the new uv-based command for users who install via pip.

**Tech Stack:** Python (json, urllib, platform, shutil), uv binary (Astral), Claude Code slash command (commands/setup.md), pytest

---

## File Structure

| File | Role |
|------|------|
| `commands/setup.md` | Slash command instructions — completely rewritten |
| `src/taleemabad_data_mcp/cli.py` | `_uv_path()` added; `_mcp_server_config()` updated; `_load_settings()` hardened |
| `install.ps1` | Replaced with deprecation notice + redirect |
| `install.sh` | Replaced with deprecation notice + redirect |
| `.mcp.json` | Template updated to show uv-based command |
| `tests/test_cli.py` | Existing assertion on line 59 updated; new tests for `_uv_path()` and `_mcp_server_config()` added |

---

## Task 1: Add `_uv_path()` helper and update `_mcp_server_config()` in cli.py

**Files:**
- Modify: `src/taleemabad_data_mcp/cli.py:30-86`
- Modify: `tests/test_cli.py`

**Context:** `_mcp_server_config()` currently builds a command pointing at a venv Python binary. It needs to point at the `uv` binary instead and use a git URL via `--with`. `_uv_path()` returns the platform-correct path to `~/.claude/uv.exe` (Windows) or `~/.claude/uv` (Unix). The existing test at line 59 asserts the old args format and must be updated too.

- [ ] **Step 1: Add imports and new test functions to test_cli.py**

Open `tests/test_cli.py`. The first line of imports is:
```python
from taleemabad_data_mcp.cli import _bundled_rules_dir, main
```

Replace it with:
```python
from taleemabad_data_mcp.cli import _bundled_rules_dir, _uv_path, _mcp_server_config, main
```

Then add these four test functions at the END of the file (after all existing tests):

```python
def test_uv_path_windows(monkeypatch):
    monkeypatch.setattr("taleemabad_data_mcp.cli.sys.platform", "win32")
    result = _uv_path()
    assert result.name == "uv.exe"
    assert ".claude" in str(result)


def test_uv_path_unix(monkeypatch):
    monkeypatch.setattr("taleemabad_data_mcp.cli.sys.platform", "linux")
    result = _uv_path()
    assert result.name == "uv"
    assert ".claude" in str(result)


def test_mcp_server_config_uses_uv():
    config = _mcp_server_config("creds.json", "TestUser")
    assert "uv" in config["command"].lower()
    assert config["args"][0] == "run"
    assert any("taleemabad-data-mcp" in a for a in config["args"])
    assert config["env"]["GOOGLE_APPLICATION_CREDENTIALS"] == "creds.json"
    assert config["env"]["TALEEMABAD_USER"] == "TestUser"
    assert "TALEEMABAD_HOSTNAME" not in config["env"]


def test_mcp_server_config_git_url_format():
    config = _mcp_server_config("creds.json", "TestUser")
    with_args = [a for a in config["args"] if "taleemabad" in a]
    assert len(with_args) == 1
    assert with_args[0].startswith("git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v")
```

- [ ] **Step 2: Update the existing broken assertion in test_setup_copies_rules_and_config**

In `tests/test_cli.py`, find line 59 (inside `test_setup_copies_rules_and_config`):
```python
    assert server_config["args"] == ["-m", "taleemabad_data_mcp", "serve"]
```

Replace with:
```python
    # New uv-based command: args start with "run"
    assert server_config["args"][0] == "run"
    assert any("taleemabad-data-mcp" in a for a in server_config["args"])
    assert server_config["args"][-1] == "serve"
```

Also update the monkeypatch in `_mock_patches()` — it patches `_venv_python` but the new `_mcp_server_config` uses `_uv_path` instead. Add this line at the end of `_mock_patches()`:

```python
    monkeypatch.setattr("taleemabad_data_mcp.cli._uv_path", lambda: claude_dir / "fake-uv")
```

- [ ] **Step 3: Run the new tests to verify they fail**

```bash
cd "E:/AI Projects/Taleemabad-Data-MCP"
uv run pytest tests/test_cli.py::test_uv_path_windows tests/test_cli.py::test_uv_path_unix tests/test_cli.py::test_mcp_server_config_uses_uv tests/test_cli.py::test_mcp_server_config_git_url_format -v
```

Expected: 4 FAILED — `_uv_path` not yet defined in cli.py.

- [ ] **Step 4: Add `_uv_path()` to cli.py**

In `src/taleemabad_data_mcp/cli.py`, add this function after the `_venv_python()` function (around line 41):

```python
def _uv_path() -> Path:
    """Return ~/.claude/uv.exe (Windows) or ~/.claude/uv (Unix)."""
    if sys.platform == "win32":
        return _claude_dir() / "uv.exe"
    return _claude_dir() / "uv"
```

- [ ] **Step 5: Update `_mcp_server_config()` in cli.py**

Replace the existing `_mcp_server_config` function (lines 73-86) with:

```python
def _mcp_server_config(credentials: str, user_name: str) -> dict:
    """Build the MCP server configuration entry using uv run --with."""
    from taleemabad_data_mcp import __version__
    uv = str(_uv_path())
    git_ref = f"git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v{__version__}"
    return {
        "command": uv,
        "args": [
            "run",
            "--with", git_ref,
            "--python", "3.11",
            "python", "-m", "taleemabad_data_mcp", "serve",
        ],
        "env": {
            "BIGQUERY_PROJECT": "niete-bq-prod",
            "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
            "GOOGLE_APPLICATION_CREDENTIALS": credentials,
            "TALEEMABAD_USER": user_name,
        },
    }
```

- [ ] **Step 6: Harden `_load_settings()` against corrupt JSON**

Find `_load_settings()` in `cli.py` (around line 58):

```python
def _load_settings() -> dict:
    """Load existing settings.json or return empty dict."""
    path = _settings_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}
```

Replace with:

```python
def _load_settings() -> dict:
    """Load existing settings.json or return empty dict."""
    path = _settings_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {}
```

- [ ] **Step 7: Run the four new tests — verify they pass**

```bash
uv run pytest tests/test_cli.py::test_uv_path_windows tests/test_cli.py::test_uv_path_unix tests/test_cli.py::test_mcp_server_config_uses_uv tests/test_cli.py::test_mcp_server_config_git_url_format -v
```

Expected: 4 PASSED.

- [ ] **Step 8: Run full test suite — verify no regressions**

```bash
uv run pytest -v
```

Expected: all tests pass. If `test_setup_copies_rules_and_config` still fails, check that Step 2 (assertion update + `_uv_path` monkeypatch) was applied correctly.

- [ ] **Step 9: Commit**

```bash
git add src/taleemabad_data_mcp/cli.py tests/test_cli.py
git commit -m "feat: add _uv_path(), update _mcp_server_config() to use uv run --with git URL"
```

---

## Task 2: Update `.mcp.json` template

**Files:**
- Modify: `.mcp.json`

**Context:** The repo's `.mcp.json` is a human-readable reference showing the shape of the config. It should show the uv-based command and remove `TALEEMABAD_HOSTNAME` (undefined, not used).

- [ ] **Step 1: Replace the content of `.mcp.json`**

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "UV_PATH",
      "args": [
        "run",
        "--with", "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@VERSION",
        "--python", "3.11",
        "python", "-m", "taleemabad_data_mcp", "serve"
      ],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "SETUP_REQUIRED",
        "BIGQUERY_MAX_BYTES": "1073741824",
        "TALEEMABAD_USER": "SETUP_REQUIRED",
        "LOG_LEVEL": "INFO"
      }
    },
    "bigquery-analytics": {
      "command": "npx",
      "args": ["-y", "@ergut/bigquery-mcp@latest"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "SETUP_REQUIRED",
        "BIGQUERY_PROJECT": "niete-bq-prod"
      }
    }
  }
}
```

`UV_PATH` and `VERSION` are human-readable placeholders. The real values are written to `~/.claude/settings.json` by `/taleemabad-setup`.

- [ ] **Step 2: Verify JSON is valid**

```bash
python -c "import json; json.load(open('.mcp.json')); print('valid')"
```

Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .mcp.json
git commit -m "docs: update .mcp.json template to show uv-based command"
```

---

## Task 3: Rewrite `commands/setup.md` slash command

**Files:**
- Modify: `commands/setup.md`

**Context:** This is the most important file. It tells Claude exactly what to do when a user types `/taleemabad-setup`. All file operations use Python one-liners via Bash — no shell scripts, no `Read-Host`, no encoding issues. The pre-warm step uses a Python subprocess call (not raw shell syntax) so Windows paths with backslashes are handled correctly.

Key correctness requirements:
- Use `monkeypatch.setattr("taleemabad_data_mcp.cli.sys.platform", ...)` style — patch attribute not whole module
- Use `os.path.expanduser()` for tilde expansion — not string replace
- Version fallback reads from installed package, not hardcoded string
- Pre-warm uses Python subprocess, not raw `<UV_PATH>` shell syntax
- settings.json merge includes `isinstance(settings, dict)` guard

- [ ] **Step 1: Replace the entire content of `commands/setup.md`**

```markdown
---
name: taleemabad-setup
description: One-time setup for Taleemabad Data plugin — downloads uv, configures credentials, writes MCP config
---

Fast setup for the Taleemabad Data plugin. Completes in under 2 minutes with no Python or venv required.

## What this does
1. Downloads the `uv` binary (~10MB) to `~/.claude/`
2. Asks your name and GCP credentials path
3. Writes the MCP server config to `~/.claude/settings.json`
4. Pre-warms the package cache so MCP starts instantly after restart

## Instructions for Claude

Follow these steps IN ORDER. Run each Bash command exactly as written.

### Step 1: Detect OS and architecture

Run:
```bash
python -c "import platform, sys; print(platform.system(), platform.machine(), sys.platform)"
```

Save the three values (e.g., `Windows AMD64 win32`). You will use them in Step 2.

### Step 2: Download uv (skip if already present)

Run this single Python one-liner. It detects the OS, downloads the correct uv binary, extracts it, and places it at `~/.claude/uv.exe` (Windows) or `~/.claude/uv` (Mac/Linux). If uv is already present it exits immediately.

```bash
python -c "
import os, sys, platform, urllib.request, tempfile, zipfile, tarfile, shutil

home = os.path.expanduser('~')
uv_name = 'uv.exe' if sys.platform == 'win32' else 'uv'
uv_dest = os.path.join(home, '.claude', uv_name)

if os.path.exists(uv_dest):
    print('uv already present at', uv_dest)
    exit(0)

system = platform.system()
machine = platform.machine().lower()

if system == 'Windows':
    url = 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip'
    archive = 'uv.zip'
elif system == 'Darwin':
    if 'arm' in machine or 'aarch' in machine:
        url = 'https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz'
    else:
        url = 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-apple-darwin.tar.gz'
    archive = 'uv.tar.gz'
else:
    url = 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz'
    archive = 'uv.tar.gz'

tmp = tempfile.mkdtemp()
archive_path = os.path.join(tmp, archive)
print('Downloading uv from', url, '...')
urllib.request.urlretrieve(url, archive_path)

if archive.endswith('.zip'):
    with zipfile.ZipFile(archive_path) as z:
        for name in z.namelist():
            if name.endswith('uv.exe') or name == 'uv.exe':
                z.extract(name, tmp)
                extracted = os.path.join(tmp, name)
                os.makedirs(os.path.dirname(uv_dest), exist_ok=True)
                shutil.move(extracted, uv_dest)
                break
else:
    with tarfile.open(archive_path) as t:
        for member in t.getmembers():
            if member.name.endswith('/uv') or member.name == 'uv':
                f = t.extractfile(member)
                os.makedirs(os.path.dirname(uv_dest), exist_ok=True)
                with open(uv_dest, 'wb') as out:
                    out.write(f.read())
                break
    os.chmod(uv_dest, 0o755)

shutil.rmtree(tmp, ignore_errors=True)
print('uv installed at', uv_dest)
"
```

If you see an error, tell the user: "uv download failed. Check your internet connection and try again. If the problem persists, ask IT to download uv manually from github.com/astral-sh/uv/releases and save it to ~/.claude/uv.exe (Windows) or ~/.claude/uv (Mac/Linux)."

### Step 3: Read the installed plugin version

Run:
```bash
python -c "
import glob, os, sys
pattern = os.path.expanduser('~/.claude/plugins/cache/Orenda-Project/taleemabad-data/*/.current-version')
matches = glob.glob(pattern)
if matches:
    version = open(matches[0]).read().strip()
    print(version)
else:
    try:
        import taleemabad_data_mcp
        print('v' + taleemabad_data_mcp.__version__)
    except ImportError:
        print('VERSION_UNKNOWN')
"
```

Save the version string (e.g., `v0.6.0`). If you see `VERSION_UNKNOWN`, stop and tell the user: "Plugin not found in cache. Please re-run `claude plugin install taleemabad-data@Orenda-Project` and try again."

### Step 4: Check for saved credentials (upgrade path)

Run:
```bash
python -c "
import os
env_path = os.path.expanduser('~/.claude/taleemabad-data-mcp.env')
if os.path.exists(env_path):
    data = {}
    for line in open(env_path).read().strip().splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            data[k.strip()] = v.strip()
    print('USER:', data.get('TALEEMABAD_USER', ''))
    print('CREDS:', data.get('GOOGLE_APPLICATION_CREDENTIALS', ''))
else:
    print('NO_SAVED_CONFIG')
"
```

- If output shows saved `USER` and `CREDS`: show those values to the user and ask "Use these saved values? (y/n)"
  - If yes: use those values for `user_name` and `credentials_path`, skip Steps 5 and 6
  - If no: proceed to Steps 5 and 6
- If `NO_SAVED_CONFIG`: proceed to Steps 5 and 6

### Step 5: Ask for name

Ask the user: **"What is your name? (used for audit logs)"**

Wait for the response. Save it as `user_name`.

### Step 6: Ask for credentials path

Ask the user: **"Paste the full path to your GCP service account JSON file."**

Wait for the response. Then validate using `os.path.expanduser()` (correct tilde handling, works on all platforms):

```bash
python -c "
import os, sys
path = os.path.expanduser('PATH_FROM_USER'.strip())
if os.path.exists(path):
    print('VALID:', path)
else:
    print('NOT_FOUND:', path)
    sys.exit(1)
"
```

Replace `PATH_FROM_USER` with exactly what the user typed (inside the single quotes).

- If output starts with `VALID:`: save the path after `VALID: ` as `credentials_path`
- If output starts with `NOT_FOUND:` or exit code is 1: tell the user "File not found. Please check the path and try again." Then re-ask Step 6.

### Step 7: Offer old venv cleanup

Run:
```bash
python -c "
import os
venv = os.path.expanduser('~/.claude/taleemabad-venv')
print('EXISTS' if os.path.exists(venv) else 'NOT_EXISTS')
"
```

If `EXISTS`:
- Tell the user: "Found old Python environment at ~/.claude/taleemabad-venv — this is no longer needed. Delete it to free up space? (y/n)"
- If yes: run `python -c "import shutil, os; shutil.rmtree(os.path.expanduser('~/.claude/taleemabad-venv'))"`
- If no: continue

### Step 8: Write settings.json (safe merge)

Construct and run the following Python one-liner. Before running, substitute the four placeholder values with the real values collected in previous steps:

- `USER_NAME_HERE` → value from Step 5 (or saved value from Step 4)
- `CREDENTIALS_PATH_HERE` → value from Step 6 (or saved value from Step 4) — use the `VALID: ...` resolved path
- `UV_PATH_HERE` → full path to uv binary (e.g., `C:\Users\Ali\.claude\uv.exe` on Windows, `/home/ali/.claude/uv` on Linux)
- `VERSION_HERE` → version string from Step 3 (e.g., `v0.6.0`)

```bash
python -c "
import json, os, sys, shutil

settings_path = os.path.expanduser('~/.claude/settings.json')
uv_path = 'UV_PATH_HERE'
version = 'VERSION_HERE'
credentials = 'CREDENTIALS_PATH_HERE'
user_name = 'USER_NAME_HERE'
git_url = 'git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@' + version

settings = {}
if os.path.exists(settings_path):
    try:
        with open(settings_path, encoding='utf-8') as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            settings = loaded
    except (json.JSONDecodeError, OSError):
        shutil.copy2(settings_path, settings_path + '.bak')
        print('Warning: corrupt settings.json backed up to', settings_path + '.bak')

settings.setdefault('mcpServers', {})['taleemabad-data'] = {
    'command': uv_path,
    'args': [
        'run',
        '--with', git_url,
        '--python', '3.11',
        'python', '-m', 'taleemabad_data_mcp', 'serve',
    ],
    'env': {
        'BIGQUERY_PROJECT': 'niete-bq-prod',
        'BIGQUERY_DATASETS': 'RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit',
        'GOOGLE_APPLICATION_CREDENTIALS': credentials,
        'BIGQUERY_MAX_BYTES': '1073741824',
        'TALEEMABAD_USER': user_name,
        'LOG_LEVEL': 'INFO',
    },
}

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2)
print('settings.json updated at', settings_path)
"
```

**Important:** `json.dump` handles Windows backslashes in paths correctly — do not manually escape them.

### Step 9: Save credentials to env file

```bash
python -c "
import os
env_path = os.path.expanduser('~/.claude/taleemabad-data-mcp.env')
user_name = 'USER_NAME_HERE'
credentials = 'CREDENTIALS_PATH_HERE'
content = 'TALEEMABAD_USER=' + user_name + '\nGOOGLE_APPLICATION_CREDENTIALS=' + credentials + '\n'
with open(env_path, 'w', encoding='utf-8') as f:
    f.write(content)
try:
    os.chmod(env_path, 0o600)
except Exception:
    pass
print('Credentials saved to', env_path)
"
```

Replace `USER_NAME_HERE` and `CREDENTIALS_PATH_HERE` with the actual values.

### Step 10: Pre-warm uv cache

Tell the user: **"Downloading data package for first use (~30 seconds)..."**

This step requires git access to the Orenda-Project GitHub org. This is the same access used by `claude plugin install` — so if that worked, this will work too.

Run using Python subprocess (handles Windows paths safely):

```bash
python -c "
import subprocess, os, sys

home = os.path.expanduser('~')
uv_name = 'uv.exe' if sys.platform == 'win32' else 'uv'
uv_path = os.path.join(home, '.claude', uv_name)
version = 'VERSION_HERE'
git_url = 'git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@' + version

result = subprocess.run(
    [uv_path, 'run', '--with', git_url, '--python', '3.11',
     'python', '-m', 'taleemabad_data_mcp', 'version'],
    capture_output=True, text=True
)
if result.returncode == 0:
    print('Pre-warm complete:', result.stdout.strip())
else:
    print('Pre-warm failed (non-blocking):', result.stderr[-500:])
    sys.exit(1)
"
```

Replace `VERSION_HERE` with the version from Step 3.

- If output starts with `Pre-warm complete:` — continue to Step 11
- If output starts with `Pre-warm failed` and mentions authentication — tell user: "GitHub authentication required. Ask IT to ensure git is configured with access to the Orenda-Project org, then re-run /taleemabad-setup."
- If output starts with `Pre-warm failed` for any other reason — tell user: "Package download failed. MCP will download itself on first use (~30 seconds after restart). You can still restart Claude Code now."

### Step 11: Done

Tell the user:

```
Setup complete!

  uv binary: ~/.claude/uv.exe
  MCP server: configured in ~/.claude/settings.json
  Package: pre-downloaded and cached

Please restart Claude Code now. After restarting, ask
"what version of taleemabad data am I running?" to verify.
```
```

- [ ] **Step 2: Verify the file saved correctly**

```bash
head -5 "E:/AI Projects/Taleemabad-Data-MCP/commands/setup.md"
```

Expected: shows frontmatter `---` and `name: taleemabad-setup`.

- [ ] **Step 3: Commit**

```bash
git add commands/setup.md
git commit -m "feat: rewrite /taleemabad-setup to use uv — no venv, no shell scripts"
```

---

## Task 4: Simplify install.ps1 and install.sh to deprecation notices

**Files:**
- Modify: `install.ps1`
- Modify: `install.sh`

**Context:** These scripts are retired. They should print a clear redirect message and exit cleanly.

- [ ] **Step 1: Replace install.ps1**

Replace the entire content of `install.ps1` with:

```powershell
# Taleemabad Data Plugin — Installer (deprecated)
# Setup is now handled via the Claude Code slash command.
#
# To install:
#   1. claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
#   2. claude plugin install taleemabad-data@Orenda-Project
#   3. Open Claude Code and run: /taleemabad-setup

Write-Host ""
Write-Host "This installer is no longer used." -ForegroundColor Yellow
Write-Host ""
Write-Host "To install the Taleemabad Data plugin:" -ForegroundColor Cyan
Write-Host "  1. In PowerShell:"
Write-Host "       claude plugin marketplace add Orenda-Project/taleemabad-data-mcp"
Write-Host "       claude plugin install taleemabad-data@Orenda-Project"
Write-Host "  2. Open Claude Code and type: /taleemabad-setup"
Write-Host ""
```

- [ ] **Step 2: Replace install.sh**

Replace the entire content of `install.sh` with:

```bash
#!/usr/bin/env bash
# Taleemabad Data Plugin — Installer (deprecated)
# Setup is now handled via the Claude Code slash command.
#
# To install:
#   1. claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
#   2. claude plugin install taleemabad-data@Orenda-Project
#   3. Open Claude Code and run: /taleemabad-setup

echo ""
echo "This installer is no longer used."
echo ""
echo "To install the Taleemabad Data plugin:"
echo "  1. In terminal:"
echo "       claude plugin marketplace add Orenda-Project/taleemabad-data-mcp"
echo "       claude plugin install taleemabad-data@Orenda-Project"
echo "  2. Open Claude Code and type: /taleemabad-setup"
echo ""
```

- [ ] **Step 3: Commit**

```bash
git add install.ps1 install.sh
git commit -m "chore: deprecate install scripts — setup now via /taleemabad-setup"
```

---

## Task 5: Bump version and push

**Files:** `src/taleemabad_data_mcp/__init__.py`, `pyproject.toml`, `.current-version`, `.claude-plugin/plugin.json`

**Context:** This is a new feature (new setup flow). Use minor bump per the project versioning rules.

- [ ] **Step 1: Check current version**

```bash
python -m taleemabad_data_mcp version
```

Note the current version before bumping.

- [ ] **Step 2: Run minor bump**

```bash
python -m taleemabad_data_mcp bump --minor
```

Expected output: `Version bumped: X.Y.Z -> X.(Y+1).0`

- [ ] **Step 3: Commit the version bump**

```bash
git add -A
git commit -m "chore: bump version to vX.Y+1.0"
```

(Use the actual new version number in the commit message.)

- [ ] **Step 4: Push and tag**

```bash
git push origin master && git push origin master:main
git tag vX.Y+1.0
git push origin vX.Y+1.0
```

(Use the actual new version number.)

---

## Task 6: Smoke test the new setup flow

**Context:** Manual end-to-end verification. Run after all code is committed and pushed.

- [ ] **Step 1: Re-install the plugin to get the latest version**

```bash
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project
```

- [ ] **Step 2: Run /taleemabad-setup in Claude Code chat**

Type `/taleemabad-setup` and follow the prompts. Measure total time.

Expected flow:
1. uv download (or skip if present) — ~5-10 seconds
2. Version detected from plugin cache
3. Saved config check
4. Name prompt
5. Credentials path prompt + validation
6. Old venv cleanup offer (if applicable)
7. settings.json write (instant)
8. Pre-warm: "Downloading data package..." — ~20-40 seconds
9. "Setup complete! Restart Claude Code."

- [ ] **Step 3: Verify settings.json was written correctly**

```bash
python -c "
import json, os
s = json.load(open(os.path.expanduser('~/.claude/settings.json')))
cfg = s['mcpServers']['taleemabad-data']
print('command ends with uv:', cfg['command'].endswith('uv.exe') or cfg['command'].endswith('uv'))
print('first arg is run:', cfg['args'][0] == 'run')
print('git url in args:', any('taleemabad-data-mcp' in a for a in cfg['args']))
print('user set:', bool(cfg['env']['TALEEMABAD_USER']))
print('creds file exists:', os.path.exists(cfg['env']['GOOGLE_APPLICATION_CREDENTIALS']))
"
```

Expected: all five lines print `True` or a non-empty value.

- [ ] **Step 4: Restart Claude Code and verify MCP**

After restart, ask: `what version of taleemabad data am I running?`

Expected: Claude uses the `get_version` MCP tool and responds with the current version — confirming MCP started successfully and instantly.

- [ ] **Step 5: Record timing**

Total time from typing `/taleemabad-setup` to "Setup complete!" message should be under 2 minutes (excluding the restart itself).

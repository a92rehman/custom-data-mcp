# Fast Plugin Setup via uv — Design Spec

**Goal:** Reduce plugin setup time from 15 minutes to under 2 minutes by replacing the Python venv + pip install flow with `uv run --with`, a self-contained binary that downloads and caches the package on first use.

**Architecture:** `uv` is a single executable (~10MB) that acts like `npx` for Python — it downloads the package, caches it, and runs it, with no venv or Python installation required. Setup becomes: download `uv`, ask two questions, write config. Done.

**Tech Stack:** uv (Astral), Claude Code plugin slash command (Bash tool), Python json module for safe settings.json merging

---

## Problem Statement

Current setup flow takes 10-15 minutes because:
1. `install.ps1` clones the repo a second time (already cloned by `claude plugin install`)
2. `pip install git+https://github.com/...` downloads source, resolves deps, builds — 3-5 minutes
3. Creating a venv adds another 30-60 seconds
4. Interactive prompts (`Read-Host`) break in Claude Code's Bash tool
5. UTF-8 characters in `.ps1` cause PowerShell encoding errors
6. Old venv not auto-upgraded — users silently run stale versions

---

## Execution Path Decision

**Chosen path: Claude performs all setup steps directly via Bash tool — no shell scripts invoked.**

Rationale: the shell script path (`install.ps1` / `install.sh`) is the source of all current bugs (encoding issues, interactive prompts, double clone). The `cli.py` `setup` command depends on a venv that no longer exists in this design. Both are retired for fresh installs.

The `cli.py` `_mcp_server_config()` function is updated to emit the new uv-based command (used by the `upgrade` and `init` CLI commands for users who install via pip, not plugin). The slash command path writes `settings.json` directly using Python's `json` module via Bash.

`install.ps1` and `install.sh` are simplified to print a deprecation notice and redirect users to `/taleemabad-setup`.

---

## Design

### 1. uv Binary Download

On setup, Claude downloads `uv` to `~/.claude/uv.exe` (Windows) or `~/.claude/uv` (Mac/Linux).

**OS + Architecture matrix:**

| OS | Architecture | Download URL |
|----|-------------|-------------|
| Windows | x86_64 (all modern PCs) | `https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip` |
| Mac | ARM (M1/M2/M3) | `https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz` |
| Mac | Intel | `https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-apple-darwin.tar.gz` |
| Linux | x86_64 | `https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz` |

Claude detects OS via `import platform; platform.system()` and architecture via `platform.machine()`.

If `~/.claude/uv.exe` (Windows) or `~/.claude/uv` (Mac/Linux) already exists, skip download.

After download, extract the binary from the zip/tar and place it at the target path. On Mac/Linux, `chmod +x` the binary.

### 2. Package Source — Git URL (not PyPI)

The package is **not published to PyPI**. It is installed from the private GitHub repo using a git URL.

The `--with` argument uses git URL format with a version tag:

```
git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.5.1
```

The setup command reads the current version from `.current-version` in the installed plugin directory:
```
~/.claude/plugins/cache/Orenda-Project/taleemabad-data/0.5.1/.current-version
```

This file contains `v0.5.1`. The setup command reads it to pin the exact version.

Full MCP server command after setup:
```json
"command": "/home/ali/.claude/uv",
"args": [
  "run",
  "--with", "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.5.1",
  "--python", "3.11",
  "python", "-m", "taleemabad_data_mcp", "serve"
]
```

### 3. settings.json Merge — Python json Module

Claude writes `~/.claude/settings.json` using Python's `json` module via Bash. This ensures:
- Proper JSON serialization (no manual escaping of Windows backslashes)
- Non-destructive merge (only the `taleemabad-data` key is overwritten; all other MCP servers preserved)

Algorithm:
```python
import json, os, platform

settings_path = os.path.expanduser("~/.claude/settings.json")
settings = {}
if os.path.exists(settings_path):
    with open(settings_path) as f:
        settings = json.load(f)

uv_path = os.path.expanduser("~/.claude/uv.exe" if platform.system() == "Windows" else "~/.claude/uv")

settings.setdefault("mcpServers", {})["taleemabad-data"] = {
    "command": uv_path,
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
}

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
```

This runs as a single `python -c "..."` Bash call. Windows paths with backslashes are handled correctly by `json.dump`.

### 4. Simplified Setup Slash Command (`/taleemabad-setup`)

The `commands/setup.md` file instructs Claude to perform these steps via Bash:

1. **Detect OS and architecture** — `python -c "import platform; print(platform.system(), platform.machine())"`
2. **Read version** — from `~/.claude/plugins/cache/Orenda-Project/taleemabad-data/*/current-version` (glob for installed version)
3. **Download uv** if not already present — use `curl` (Mac/Linux) or `Invoke-WebRequest` via `python -c` with `urllib.request`
4. **Ask name** — "What is your name? (used for audit logs)"
5. **Ask credentials path** — "Paste the full path to your GCP service account JSON file"
6. **Validate** — check credentials file exists before writing anything
7. **Write settings.json** — Python one-liner using json module (safe merge, proper escaping)
8. **Save env file** — `~/.claude/taleemabad-data-mcp.env` with name + credentials for upgrades
9. **Pre-warm uv cache** — run `uv run --with git+... python -m taleemabad_data_mcp version` so the package downloads NOW, not on first MCP start
10. **Tell user to restart Claude Code**

Step 9 (pre-warm) is critical: it downloads the package during setup so the first MCP server start is instant. User sees a progress message: "Downloading data package (~30 seconds)..." — honest and visible.

### 5. Upgrade Path

Re-running `/taleemabad-setup`:
- Reads saved name + credentials from `~/.claude/taleemabad-data-mcp.env`
- Skips asking name and credentials (shows saved values, asks to confirm)
- Reads new version from the updated plugin cache directory
- Rewrites the `--with` arg in `settings.json` with new version
- Pre-warms new version cache

### 6. Existing Venv Migration

If `~/.claude/taleemabad-venv` exists when `/taleemabad-setup` runs:
- Tell user: "Found old Python environment at ~/.claude/taleemabad-venv — this is no longer needed."
- Ask: "Delete it to free up space? (y/n)"
- If yes: `shutil.rmtree(venv_path)` via Python one-liner

---

## Employee Experience

```
# PowerShell — ~45 seconds total
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project

# Claude Code chat — ~90 seconds total
/taleemabad-setup
  Claude: "What is your name?" → Ali
  Claude: "Path to credentials JSON?" → C:\Users\Ali\Downloads\niete-key.json
  Claude: "Downloading uv..." (5 seconds)
  Claude: "Downloading data package..." (30 seconds — pre-warm)
  Claude: "Done. Restart Claude Code."

# After restart: MCP tools available immediately (cache already warm)
```

**Total visible wait: under 2 minutes. MCP available instantly after restart.**

---

## Files to Change

| File | Change |
|------|--------|
| `commands/setup.md` | Rewrite: Claude does all steps via Bash, no shell scripts, pre-warms cache |
| `install.ps1` | Replace with deprecation notice + redirect to `/taleemabad-setup` |
| `install.sh` | Same for Mac/Linux |
| `.mcp.json` | Update template to show uv-based command with placeholder values (remove `TALEEMABAD_HOSTNAME`) |
| `src/taleemabad_data_mcp/cli.py` | Update `_mcp_server_config()` to emit uv git-URL command |

## Files NOT Changed

- `src/taleemabad_data_mcp/server.py` — MCP server logic unchanged
- `.claude-plugin/plugin.json` — plugin manifest unchanged
- All governance rules — unchanged

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| uv download fails (no internet) | Tell user: "Download uv manually from github.com/astral-sh/uv/releases and save to ~/.claude/uv.exe, then re-run /taleemabad-setup" |
| Credentials file not found | Re-ask immediately with clear message — do not write any config until valid |
| Pre-warm fails (private repo auth) | Tell user git must have access to Orenda-Project org — check with IT |
| Upgrade: saved env missing | Skip confirmation, ask both questions fresh |
| Old venv present | Offer to delete, do not auto-delete |
| Intel Mac detected | Use `uv-x86_64-apple-darwin.tar.gz` (not ARM build) |
| settings.json parse error (corrupt) | Back up original, start fresh with only taleemabad-data key |

---

## Out of Scope

- Publishing to PyPI (would simplify `--with` arg but requires public package)
- Distributing `uv.exe` in the repo (avoids 10MB binary in git)
- Supporting Python versions below 3.11
- Offline/air-gapped installs
- MDM/bulk deployment (separate initiative)

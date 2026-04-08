# Fast Plugin Setup via uv — Design Spec

**Goal:** Reduce plugin setup time from 15 minutes to under 2 minutes by replacing the Python venv + pip install flow with `uv run --with`, a self-contained binary that downloads and caches the package on first use.

**Architecture:** `uv` is a single executable (~10MB) that acts like `npx` for Python — it downloads the package, caches it, and runs it, with no venv or Python installation required. Setup becomes: download `uv`, ask two questions, write config. Done.

**Tech Stack:** uv (Astral), PowerShell (Windows), bash (Mac/Linux), Claude Code plugin slash command

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

## Design

### 1. uv Binary Download

On setup, download `uv` to `~/.claude/uv.exe` (Windows) or `~/.claude/uv` (Mac/Linux).

- Source: `https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip` (Windows)
- Source: `https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz` (Linux)
- Source: `https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz` (Mac ARM)
- If already present, skip download (idempotent)
- No Python required — `uv` is fully self-contained

### 2. New MCP Server Command

Replace the venv-based command in `~/.claude/settings.json`:

**Before:**
```json
"command": "C:\\Users\\Ali\\.claude\\taleemabad-venv\\Scripts\\python.exe",
"args": ["-m", "taleemabad_data_mcp", "serve"]
```

**After:**
```json
"command": "C:\\Users\\Ali\\.claude\\uv.exe",
"args": ["run", "--with", "taleemabad-data-mcp==0.5.1", "--python", "3.11", "python", "-m", "taleemabad_data_mcp", "serve"]
```

`uv` downloads the package on first use (~30s, silent), then caches it. All subsequent MCP server starts are instant (cached).

### 3. Simplified Setup Slash Command (`/taleemabad-setup`)

The `commands/setup.md` file instructs Claude to:

1. **Download uv** — run the appropriate download command for the OS, save to `~/.claude/uv` or `~/.claude/uv.exe`
2. **Ask name** — "What is your name? (used for audit logs)"
3. **Ask credentials path** — "Paste the full path to your GCP service account JSON file"
4. **Validate credentials file exists** — check path before writing config
5. **Write `~/.claude/settings.json`** — merge MCP entry using `uv run --with` command
6. **Save `~/.claude/taleemabad-data-mcp.env`** — store name + credentials for future upgrades
7. **Tell user to restart Claude Code**

No shell scripts invoked. Claude performs all steps directly using Bash tool. This eliminates the encoding problem entirely.

### 4. `.mcp.json` Template Update

The repo's `.mcp.json` template updates to document-only (not used at install time — Claude writes `settings.json` directly):

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "UV_PATH",
      "args": ["run", "--with", "taleemabad-data-mcp==VERSION", "--python", "3.11",
               "python", "-m", "taleemabad_data_mcp", "serve"],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "CREDENTIALS_PATH",
        "TALEEMABAD_USER": "USER_NAME",
        "TALEEMABAD_HOSTNAME": "HOSTNAME"
      }
    }
  }
}
```

### 5. Upgrade Path

Re-running `/taleemabad-setup` or a future `/taleemabad-upgrade` command:
- Reads saved name + credentials from `~/.claude/taleemabad-data-mcp.env`
- Updates the version pin in the `--with` arg in `settings.json`
- No venv to recreate, no pip reinstall — edit one value

---

## Employee Experience

```
# PowerShell — ~45 seconds total
claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
claude plugin install taleemabad-data@Orenda-Project

# Claude Code chat — ~30 seconds
/taleemabad-setup
  Claude: "What is your name?"       → Ali
  Claude: "Path to credentials JSON?" → C:\Users\Ali\Downloads\niete-key.json
  Claude: "Done. Restart Claude Code."

# First MCP server start — ~30 seconds (background, user doesn't wait)
uv downloads taleemabad-data-mcp silently and caches it.

# All subsequent starts: instant (uv cache hit)
```

**Total visible wait: under 2 minutes.**

---

## Files to Change

| File | Change |
|------|--------|
| `commands/setup.md` | Rewrite: Claude downloads uv, asks 2 questions, writes settings.json directly — no shell scripts |
| `install.ps1` | Simplify to legacy fallback only (remove venv/pip logic) |
| `install.sh` | Same for Mac/Linux |
| `.mcp.json` | Update template to show uv-based command with placeholder values |
| `src/taleemabad_data_mcp/cli.py` | Update `_mcp_server_config()` to emit uv command instead of venv python |

## Files NOT Changed

- `src/taleemabad_data_mcp/server.py` — MCP server logic unchanged
- `.claude-plugin/plugin.json` — plugin manifest unchanged
- All governance rules — unchanged

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| uv download fails (no internet) | Tell user to download manually from github.com/astral-sh/uv/releases |
| Credentials file not found | Re-ask with clear error message before writing any config |
| First MCP start slow | Expected — tell user "first start takes ~30 seconds, then instant" |
| Upgrade: saved env missing | Fall back to asking both questions again |

---

## Out of Scope

- Distributing `uv.exe` in the repo (avoids 10MB binary in git; download at setup time instead)
- Supporting Python versions below 3.11
- Offline/air-gapped installs
- MDM/bulk deployment (separate initiative)

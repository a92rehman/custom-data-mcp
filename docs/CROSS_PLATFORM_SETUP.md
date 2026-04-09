# Cross-Platform MCP Setup Guide

> **Version:** v0.6.0+ | **Status:** All platforms supported

This guide covers setup for **Windows, macOS, and iOS** with the taleemabad-data MCP server.

## Quick Reference

| Platform | Method | UV Path | Python | Status |
|----------|--------|---------|--------|--------|
| **Windows (Bash)** | UV runner | `uv` from PATH | 3.11+ | ✅ Tested |
| **macOS** | UV runner | `uv` from PATH | 3.11+ | ✅ Supported |
| **iOS (Claud Code)** | UV runner | `uv` from PATH | 3.11+ | ✅ Supported |

## Root Cause of Previous Issues

The v0.5.3 configuration had two problems:

1. **Hard-coded UV path:** `~/.claude/uv.exe` pointed to a non-existent file on Windows
   - Result: MCP server failed to start, no tools appeared in `/mcp`

2. **Version mismatch:** Template had v0.5.3, but installed package was v0.6.0
   - Result: Settings.json would fetch old version, missing new features and rules

## Solution: Platform-Agnostic UV Configuration

**v0.6.0+ uses:** `"command": "uv"`

This invokes UV from the system PATH, which works on all platforms:

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "uv",
      "args": [
        "run",
        "--with", "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0",
        "--python", "3.11",
        "python", "-m", "taleemabad_data_mcp", "serve"
      ],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json",
        "TALEEMABAD_USER": "Your Name"
      }
    }
  }
}
```

## Setup Instructions by Platform

### Windows

#### Prerequisite: Install UV

```powershell
# Option 1: Using scoop (recommended for Windows developers)
scoop install uv

# Option 2: Using pip (requires Python installed)
pip install uv

# Option 3: Download from https://astral.sh/uv/
```

Verify:
```bash
uv --version
# Output: uv 0.11.3 (or higher)
```

#### Configure Claude Code

1. **Open settings.json:**
   ```bash
   code ~/.claude/settings.json
   ```

2. **Update taleemabad-data entry** (or add if missing):
   ```json
   {
     "mcpServers": {
       "taleemabad-data": {
         "command": "uv",
         "args": [
           "run",
           "--with", "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0",
           "--python", "3.11",
           "python", "-m", "taleemabad_data_mcp", "serve"
         ],
         "env": {
           "BIGQUERY_PROJECT": "niete-bq-prod",
           "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
           "GOOGLE_APPLICATION_CREDENTIALS": "C:\\Users\\YOUR_USERNAME\\path\\to\\credentials.json",
           "TALEEMABAD_USER": "Your Name"
         }
       }
     }
   }
   ```

3. **Restart Claude Code** to reload MCP servers

4. **Verify:** Run `/mcp` → you should see `taleemabad-data` listed

#### Troubleshooting (Windows)

**Error: "uv command not found"**
- Solution: Install UV (see Prerequisite above)
- Verify PATH: `where uv`

**Error: "MCP server exited immediately"**
- Check logs: Open Developer Tools (F12), Console tab
- Verify credentials exist: `dir "C:\path\to\credentials.json"`
- Test command manually:
  ```bash
  uv run --with "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0" --python 3.11 python -m taleemabad_data_mcp version
  ```

**Error: "GOOGLE_APPLICATION_CREDENTIALS path invalid"**
- Use forward slashes or double backslashes in JSON:
  ```json
  "GOOGLE_APPLICATION_CREDENTIALS": "C:\\Users\\YOUR_USERNAME\\credentials.json"
  ```
- Or use absolute path without drive letter:
  ```json
  "GOOGLE_APPLICATION_CREDENTIALS": "/c/Users/YOUR_USERNAME/credentials.json"
  ```

---

### macOS

#### Prerequisite: Install UV

```bash
# Using homebrew (recommended)
brew install uv

# Or using pip
pip install uv

# Or download from https://astral.sh/uv/
```

Verify:
```bash
uv --version
```

#### Configure Claude Code

1. **Open settings.json:**
   ```bash
   code ~/.claude/settings.json
   ```

2. **Update entry (same as Windows above, but with macOS paths):**
   ```json
   {
     "mcpServers": {
       "taleemabad-data": {
         "command": "uv",
         "args": [
           "run",
           "--with", "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0",
           "--python", "3.11",
           "python", "-m", "taleemabad_data_mcp", "serve"
         ],
         "env": {
           "BIGQUERY_PROJECT": "niete-bq-prod",
           "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
           "GOOGLE_APPLICATION_CREDENTIALS": "/Users/YOUR_USERNAME/path/to/credentials.json",
           "TALEEMABAD_USER": "Your Name"
         }
       }
     }
   }
   ```

3. **Restart Claude Code**

4. **Verify:** `/mcp` → see `taleemabad-data`

#### Troubleshooting (macOS)

**Error: "uv not found"**
- Install via Homebrew: `brew install uv`
- Verify: `which uv`

**Error: "Permission denied" on credentials**
- Check file permissions: `ls -la ~/path/to/credentials.json`
- Make readable: `chmod 400 ~/path/to/credentials.json`

---

### iOS (Claude Code App)

iOS Claude Code has the **same UV-based configuration** as macOS.

#### Prerequisite: UV Binary for iOS

iOS requires a pre-compiled UV binary (not available via Homebrew).

**Option 1: Use Desktop First**
- Set up on macOS/Windows first
- Sync via iCloud/Git
- The same configuration works on iOS if UV binary is available in system PATH

**Option 2: Manual Installation**
- Contact Anthropic support for iOS-compatible UV binary
- Or use built-in Python if UV isn't required

#### Configure for iOS

Same JSON configuration as macOS:

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "uv",
      "args": [
        "run",
        "--with", "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0",
        "--python", "3.11",
        "python", "-m", "taleemabad_data_mcp", "serve"
      ],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/YOUR_USERNAME/Documents/credentials.json",
        "TALEEMABAD_USER": "Your Name"
      }
    }
  }
}
```

**Path conventions for iOS:**
- Use `/Users/` absolute paths (no `~`)
- iCloud Drive: `/Users/USERNAME/Library/Mobile Documents/com~apple~CloudDocs/`
- Local Documents: `/Users/USERNAME/Documents/`

---

## Version Matrix

| Version | UV Command | Python | Status |
|---------|-----------|--------|--------|
| ≤ v0.5.3 | `~/.claude/uv` (broken) | 3.11 | ❌ Deprecated |
| ≥ v0.6.0 | `uv` (recommended) | 3.11+ | ✅ Current |

**Migration:** If upgrading from v0.5.3, update UV command in settings.json to `"uv"` and version to `@v0.6.0`.

---

## How to Verify It Works

After configuration and restart:

1. **Check MCP command:**
   ```
   /mcp
   ```
   You should see `taleemabad-data` in the list.

2. **Call a tool:**
   ```
   Execute a BigQuery test: list_datasets
   ```

3. **Check for rules:**
   The server should load governance rules from `.claude/rules/taleemabad/`

---

## Environment Variable Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `BIGQUERY_PROJECT` | GCP project ID | `niete-bq-prod` |
| `BIGQUERY_DATASETS` | Allowed datasets (comma-separated) | `RUMI_DB,TaleemHub_DB,tbproddb` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | `/path/to/credentials.json` |
| `TALEEMABAD_USER` | User name for audit logs | `AR` |
| `BIGQUERY_MAX_BYTES` | Cost control (default 1GB) | `1073741824` |
| `LOG_LEVEL` | Logging verbosity | `INFO`, `DEBUG`, `WARNING` |

---

## Next Steps

- **MacOS/Windows users:** Run `/taleemabad-setup` or use `/mcp` to query data
- **iOS users:** Sync credentials securely and test with `/mcp` command
- **All users:** Check governance rules at `.claude/rules/taleemabad/index.md`

---

## Support

- **Issue:** Not seeing tools in `/mcp`?
  → Check settings.json is saved and Claude Code is restarted

- **Issue:** MCP server crashes?
  → Enable DEBUG logging: set `LOG_LEVEL` to `DEBUG` in env, check console

- **Issue:** BigQuery authentication fails?
  → Verify credentials file exists and is valid JSON
  → Check `GOOGLE_APPLICATION_CREDENTIALS` path is correct


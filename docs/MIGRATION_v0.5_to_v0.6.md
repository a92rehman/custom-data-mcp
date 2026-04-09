# Migration Guide: v0.5.x → v0.6.0+

## What Changed

**Critical Fix:** MCP server configuration now works on all platforms (Windows, macOS, iOS).

### The Problem (v0.5.3)

```json
"command": "~/.claude/uv.exe"  // ❌ Doesn't exist on Windows
```

Result: MCP server failed to start, `/mcp` showed no tools.

### The Solution (v0.6.0+)

```json
"command": "uv"  // ✅ Uses PATH (works everywhere)
```

---

## Migration Steps

### Step 1: Identify Your Config Location

- **Main settings file:** `~/.claude/settings.json`
- **Project-local config:** `.mcp.json` (in your project)

### Step 2: Update settings.json

Open `~/.claude/settings.json` and find the taleemabad-data section:

**BEFORE (v0.5.3):**
```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "C:\\Users\\ZBOOK\\.claude\\uv.exe",
      "args": [
        "run",
        "--with",
        "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.5.3",
        "--python",
        "3.11",
        "python",
        "-m",
        "taleemabad_data_mcp",
        "serve"
      ],
      ...
    }
  }
}
```

**AFTER (v0.6.0+):**
```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0",
        "--python",
        "3.11",
        "python",
        "-m",
        "taleemabad_data_mcp",
        "serve"
      ],
      ...
    }
  }
}
```

**Two changes:**
1. `"command": "C:\\Users\\ZBOOK\\.claude\\uv.exe"` → `"command": "uv"`
2. `@v0.5.3` → `@v0.6.0`

### Step 3: Verify UV is Installed

```bash
# Check if UV is available
uv --version

# If not found, install it:
# Windows:  scoop install uv  OR  pip install uv
# macOS:    brew install uv   OR  pip install uv
# iOS:      Contact support or use system Python
```

### Step 4: Restart Claude Code

Close and reopen Claude Code, or reload MCP servers:
- **VS Code:** Command Palette → "Claude Code: Restart MCP Server"
- **Desktop/Web:** Close and reopen

### Step 5: Verify Success

Run this command in Claude Code:

```
/mcp
```

You should see `taleemabad-data` in the list (not `error` or `unavailable`).

---

## What About My .mcp.json?

If you have a **project-local .mcp.json**, update it the same way:

```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "uv",  // ← Changed
      "args": [
        "run",
        "--with",
        "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0",  // ← Updated version
        "--python",
        "3.11",
        "python",
        "-m",
        "taleemabad_data_mcp",
        "serve"
      ],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/credentials.json",
        "TALEEMABAD_USER": "Your Name"
      }
    }
  }
}
```

---

## Troubleshooting

### "uv: command not found"

Install UV:
```bash
# Windows
scoop install uv
# or
pip install uv

# macOS
brew install uv
# or
pip install uv
```

### "MCP server still not loading"

1. **Clear cache:** Restart Claude Code completely
2. **Check logs:** Open Developer Tools (F12), Console tab
3. **Test manually:**
   ```bash
   uv run --with "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0" --python 3.11 python -m taleemabad_data_mcp version
   ```

### "Old version still loading"

The global `~/.claude/settings.json` takes precedence over `.mcp.json`.
- Update `~/.claude/settings.json` first
- Both files must have matching versions (@v0.6.0)

---

## Platform-Specific Notes

### Windows (Git Bash / WSL)
- Use `uv` from PATH (no absolute path needed)
- Credentials path can use forward slashes: `C:/Users/USERNAME/credentials.json`

### macOS
- `uv` from Homebrew is automatically in PATH
- Use absolute paths: `/Users/USERNAME/credentials.json`

### iOS
- Same config as macOS
- Requires UV binary (contact support if needed)
- Use absolute paths without `~`

---

## Version Compatibility

| Version | Command | Status | Notes |
|---------|---------|--------|-------|
| v0.5.0 - v0.5.3 | Hard-coded path | ❌ Broken | Don't use |
| v0.6.0+ | `uv` from PATH | ✅ Fixed | Recommended |

---

## Questions?

- **Docs:** See `docs/CROSS_PLATFORM_SETUP.md` for detailed setup by platform
- **Issue:** Open issue on GitHub with output from `/mcp` and logs
- **Support:** Mention your platform (Windows/macOS/iOS) in issue


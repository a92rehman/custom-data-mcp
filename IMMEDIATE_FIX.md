# Immediate Fix - MCP Not Loading

**Your Situation:** v0.6.0 installed but tools don't appear in `/mcp`

## What Happened

- `.mcp.json` template had v0.5.3, v0.6.0 is now installed → version mismatch
- Settings.json pointed to `C:\Users\ZBOOK\.claude\uv.exe` which doesn't exist → MCP startup fails

## Quick Fix (5 minutes)

### Step 1: Update settings.json

Edit `C:\Users\ZBOOK\.claude\settings.json` and find the `taleemabad-data` section.

**Change this:**
```json
"command": "C:\\Users\\ZBOOK\\.claude\\uv.exe",
"args": [
  "run",
  "--with",
  "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.5.3",
  ...
]
```

**To this:**
```json
"command": "uv",
"args": [
  "run",
  "--with",
  "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0",
  ...
]
```

Two changes:
1. Remove absolute path, use just `"uv"`
2. Change `@v0.5.3` → `@v0.6.0`

### Step 2: Verify UV is Available

```bash
uv --version
# Should print: uv 0.11.3 (or higher)
```

If `uv: command not found`, install it:
```bash
# Windows: Use scoop or pip
scoop install uv
# or
pip install uv
```

### Step 3: Restart Claude Code

Close Claude Code completely and reopen it.

### Step 4: Verify Fix

Run this in Claude Code:
```
/mcp
```

You should see:
```
taleemabad-data · connected
```

(Not "error", not "unavailable", not missing from list)

---

## If It Still Doesn't Work

1. **Check logs:**
   - Open Developer Tools (F12)
   - Go to Console tab
   - Look for MCP-related errors

2. **Test manually:**
   ```bash
   uv run --with "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v0.6.0" --python 3.11 python -m taleemabad_data_mcp version
   ```
   Should print: `taleemabad-data-mcp v0.6.0`

3. **If that fails:**
   - Check credentials exist: `ls "E:\AI Projects\MCP Testing 2\niete-bq-prod-48ae5260d1ea.json"`
   - Check GCP project access: `gcloud auth login`
   - Check Python: `python --version` (should be 3.11+)

---

## Why This Happened

The previous setup used a path that doesn't exist (`~/.claude/uv.exe`). The fix uses `uv` from your system PATH, which works on all platforms.

---

## What This Enables

Once `/mcp` shows `taleemabad-data`, you can:

- Query teacher data: *"How many PRIMARY teachers in ICT/Islamabad?"*
- Ask about lesson plans: *"What's the LP completion rate this week?"*
- Get observation scores: *"Show me FICO Section B scores by school"*
- Check training progress: *"How many teachers passed Level 2 training?"*

All queries are automatically audited and governed by rules in `.claude/rules/taleemabad/`

---

## Documentation

- **Full setup guide:** `docs/CROSS_PLATFORM_SETUP.md` (Windows, macOS, iOS)
- **Migration guide:** `docs/MIGRATION_v0.5_to_v0.6.md` (from v0.5.3)
- **Debug details:** `DEBUG_SUMMARY.md` (root cause analysis)


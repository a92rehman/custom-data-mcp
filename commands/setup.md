# /taleemabad-setup

Set up your name for audit logging and sync governance rules. The MCP server is configured automatically by the plugin.

## Prerequisites
- Plugin must be installed: `claude plugin install taleemabad-data@Orenda-Project`
- `niete-bq-prod-48ae5260d1ea.json` (GCP service account key) should be in each project directory you want to use

## Steps

### Step 1: Ask for name
Ask: "What is your name? (used for audit logs)"
Save as `user_name`.

### Step 2: Run setup
On Windows:
```
python -m taleemabad_data_mcp setup --user "<user_name>"
```

On macOS/Linux:
```
python3 -m taleemabad_data_mcp setup --user "<user_name>"
```

**IMPORTANT:** If `python -m taleemabad_data_mcp` fails with "No module named taleemabad_data_mcp", install the package first:
```
pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"
```

### Step 3: Done
Tell the user:
```
Setup complete!

Restart Claude Code (close and reopen, or Ctrl+R).
Then run /mcp to verify:
  - taleemabad-data · connected

Make sure niete-bq-prod-48ae5260d1ea.json is in your project directory.
```

## Error handling

| Error | Fix |
|-------|-----|
| "No module named taleemabad_data_mcp" | Run `pip install "git+https://github.com/Orenda-Project/taleemabad-data-mcp"` |
| MCP server shows "credentials not found" | Copy `niete-bq-prod-48ae5260d1ea.json` to project directory |

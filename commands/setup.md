# /taleemabad-setup

Set up your work email and team token for the Taleemabad Data MCP. The MCP server runs remotely — no local dependencies needed.

## Prerequisites
- Plugin must be installed: `claude plugin install taleemabad-data@Orenda-Project`
- You need your **work email** (must be @taleemabad.com, @niete.edu.pk, or @niete.pk)

## Steps

### Step 1: Ask for email
Ask: "What is your work email? (must be @taleemabad.com, @niete.edu.pk, or @niete.pk)"
Save as `user_email`.

Validate the domain:
- Must end with `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`
- If invalid, tell user: "Please use your work email. Allowed domains: @taleemabad.com, @niete.edu.pk, @niete.pk"

### Step 2: Run setup

On Windows:
```
python -m taleemabad_data_mcp setup --email "<user_email>"
```

On macOS/Linux:
```
python3 -m taleemabad_data_mcp setup --email "<user_email>"
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

No credentials file or Python installation needed — the MCP server runs remotely.
```

## Error handling

| Error | Fix |
|-------|-----|
| "Unauthorized: invalid or missing API token" | Check token with admin, re-run /taleemabad-setup |
| "Setup required" | Run /taleemabad-setup to enter email and token |
| "Unauthorized domain" | Use your work email (@taleemabad.com, @niete.edu.pk, or @niete.pk) |
| MCP server not connecting | Check internet connection, run /mcp to see status |

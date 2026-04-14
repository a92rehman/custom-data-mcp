# /taleemabad-setup

Set up your work email and team token for the Taleemabad Data MCP. The MCP server runs remotely — no local dependencies needed.

## Prerequisites
- Plugin must be installed: `claude plugin install taleemabad-data@Orenda-Project`
- You need your **work email** (must be @taleemabad.com, @niete.edu.pk, or @niete.pk)
- You need the **team token** (ask your admin or check the team onboarding channel)

## Steps

### Step 1: Ask for email
Ask: "What is your work email? (must be @taleemabad.com, @niete.edu.pk, or @niete.pk)"
Save as `user_email`.

Validate the domain:
- Must end with `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`
- If invalid, tell user: "Please use your work email. Allowed domains: @taleemabad.com, @niete.edu.pk, @niete.pk"

### Step 2: Ask for team token
Ask: "Please paste your team token (provided by your admin):"
Save as `api_token`.

### Step 3: Save configuration
Write the following to `~/.claude/taleemabad-data-mcp.env`:
```
TALEEMABAD_USER=<user_email>
TALEEMABAD_API_TOKEN=<api_token>
```

On Windows:
```
python -c "from pathlib import Path; p = Path.home() / '.claude' / 'taleemabad-data-mcp.env'; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('TALEEMABAD_USER=<user_email>\nTALEEMABAD_API_TOKEN=<api_token>\n')"
```

On macOS/Linux:
```
mkdir -p ~/.claude && echo -e "TALEEMABAD_USER=<user_email>\nTALEEMABAD_API_TOKEN=<api_token>" > ~/.claude/taleemabad-data-mcp.env
```

### Step 4: Done
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

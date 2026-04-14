# /taleemabad-setup

Set up your work email for the Taleemabad Data MCP. The MCP server runs remotely.

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

### Step 2: Save configuration
Write the following to `~/.claude/taleemabad-data-mcp.env`:
```
TALEEMABAD_USER=<user_email>
```

On Windows:
```
python -c "from pathlib import Path; p = Path.home() / '.claude' / 'taleemabad-data-mcp.env'; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('TALEEMABAD_USER=<user_email>\n')"
```

On macOS/Linux:
```
mkdir -p ~/.claude && echo "TALEEMABAD_USER=<user_email>" > ~/.claude/taleemabad-data-mcp.env
```

### Step 3: Done
Tell the user:
```
Setup complete!

Restart Claude Code (close and reopen, or Ctrl+R).
Then run /mcp to verify:
  - taleemabad-data · connected
```

## Error handling

| Error | Fix |
|-------|-----|
| "Setup required" | Run /taleemabad-setup to enter your email |
| "Unauthorized domain" | Use your work email (@taleemabad.com, @niete.edu.pk, or @niete.pk) |
| MCP server not connecting | Check internet connection, run /mcp to see status |

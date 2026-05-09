# /taleemabad-setup

Set up your work email for the Taleemabad Data MCP. The MCP server runs remotely.

## Prerequisites
- Plugin must be installed: `claude plugin install taleemabad-data@a92rehman`
- You need your **work email** (must be @taleemabad.com, @niete.edu.pk, or @niete.pk)

## Steps

### Step 1: Ask for email
Ask: "What is your work email? (must be @taleemabad.com, @niete.edu.pk, or @niete.pk)"
Save as `user_email`.

Validate the domain:
- Must end with `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`
- If invalid, tell user: "Please use your work email. Allowed domains: @taleemabad.com, @niete.edu.pk, @niete.pk"

### Step 2: Save configuration

Save email to the env file (used by local stdio server):

On Windows:
```
python -c "from pathlib import Path; p = Path.home() / '.claude' / 'custom-data-mcp.env'; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('TALEEMABAD_USER=<user_email>\n')"
```

On macOS/Linux:
```
mkdir -p ~/.claude && echo "TALEEMABAD_USER=<user_email>" > ~/.claude/custom-data-mcp.env
```

### Step 3: Set system environment variable

Set `TALEEMABAD_USER` as a persistent OS environment variable so Claude Code can expand `${TALEEMABAD_USER}` in MCP headers.

On Windows (PowerShell — sets for the current user permanently):
```
[System.Environment]::SetEnvironmentVariable('TALEEMABAD_USER', '<user_email>', 'User')
```

On macOS/Linux (add to shell profile):
```
echo 'export TALEEMABAD_USER="<user_email>"' >> ~/.bashrc
echo 'export TALEEMABAD_USER="<user_email>"' >> ~/.zshrc
```

### Step 4: Done
Tell the user:
```
Setup complete!

Close your terminal AND Claude Code completely, then reopen both.
This is needed so the TALEEMABAD_USER environment variable takes effect.

Then run /mcp to verify:
  - taleemabad-data · connected
```

## Error handling

| Error | Fix |
|-------|-----|
| "Setup required" | Run /taleemabad-setup to enter your email |
| "Unauthorized domain" | Use your work email (@taleemabad.com, @niete.edu.pk, or @niete.pk) |
| "${TALEEMABAD_USER}" literal in errors | The env var wasn't set. Re-run setup, then restart terminal + Claude Code |
| MCP server not connecting | Check internet connection, run /mcp to see status |

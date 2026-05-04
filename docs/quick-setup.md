# Taleemabad Data MCP — Quick Setup

## What You Need First

1. **Claude Code** installed and authenticated (run `claude` in terminal if not done yet)
2. **GitHub access** to the [Orenda-Project](https://github.com/Orenda-Project) organization (ask IT if you don't have it)
3. **Work email** ending with `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`

## Setup Instructions

Open Claude Code in your terminal, then **copy and paste this entire block** into the chat:

---

```
Install the Taleemabad Data MCP plugin for me. Here's what to do:

1. Run this command in the terminal: claude plugin marketplace add Orenda-Project/taleemabad-data-mcp
2. Then run: claude plugin install taleemabad-data@Orenda-Project
3. After both succeed, ask me for my work email (must be @taleemabad.com, @niete.edu.pk, or @niete.pk)
4. Run the setup command with my email: /taleemabad-setup
5. After setup completes, verify the connection by running: /mcp
6. Tell me if taleemabad-data shows as connected

If any step fails, tell me what went wrong and how to fix it. If it says "git access required" I need to ask IT for GitHub access to Orenda-Project.
```

---

That's it. Claude Code will handle the rest and ask you for your email during setup.

## After Setup

Once connected, just ask questions in plain English:

- *"How many active PRIMARY teachers are in ICT?"*
- *"What's the LP adoption rate this month?"*
- *"Show me FICO Section B scores for Q1 2026"*

## Something Not Working?

Close and reopen Claude Code — the plugin automatically detects and fixes common issues (missing config, stale rules, connection problems) on every session start. If the problem persists, try reinstalling: `claude plugin update taleemabad-data@Orenda-Project`.

## Need Help?

**Abdurrehman Siddique** can help with prerequisites (Node.js, Claude Code, Anthropic subscription, GitHub access) and any installation issues.

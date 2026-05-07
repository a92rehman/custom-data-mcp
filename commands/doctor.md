# /taleemabad-doctor

Run system health checks and auto-fix common Taleemabad Data MCP issues.

## What it does

Dispatches the `system-doctor` agent to:
1. Check MCP server connectivity
2. Verify user identity (env file, env var)
3. Verify governance rules are synced and up to date
4. Check plugin installation and version
5. Detect and fix session-start hook issues

## Steps

### Step 1: Dispatch system-doctor

Dispatch the `system-doctor` agent with this prompt:

> Run a full system health check. Check all symptoms in the matrix: connection_failed, user_env_missing, user_env_unexpanded, rules_path_missing, rules_stale, plugin_not_installed, plugin_outdated, mcp_handshake_fail, hook_crashed. Report findings and auto-fix what you can.

### Step 2: Present results

Show the user the system-doctor's health report summary:
- How many checks passed
- What was auto-fixed (with ticket IDs)
- What needs user action
- What was escalated to GitHub

### Step 3: Recommendations

If any issues remain unresolved, provide clear next steps:
- For `user_env_missing`: "Run `/taleemabad-setup` to configure your email"
- For `plugin_not_installed`: "Run `claude plugin install taleemabad-data@Orenda-Project`"
- For `plugin_outdated`: "Run `claude plugin update taleemabad-data@Orenda-Project`"
- For escalated issues: "A GitHub issue has been filed at <URL>. The data team will investigate."

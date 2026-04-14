# Remote MCP Deployment on Railway

**Date:** 2026-04-14
**Status:** DRAFT
**Author:** Claude Code + User

---

## Problem

The current plugin requires users to:
1. Have Python and `uv` installed locally
2. Copy a GCP credentials JSON file to their project directory
3. Run the MCP server locally via `uv run`

This creates friction. Users struggle with dependency setup, and credential distribution is manual. The goal is **install plugin → enter email → start querying**.

## Solution

Deploy the MCP server to Railway as a remote HTTP endpoint. The plugin switches from running a local MCP server to connecting to a remote URL. GCP credentials live on Railway. Users need nothing installed locally except Claude Code.

## Architecture

```
User's Machine                              Railway
┌──────────────────────────┐     HTTPS     ┌──────────────────────┐
│ Claude Code               │─────────────▶│ MCP Server           │
│  ├─ Plugin                │              │  ├─ FastMCP (HTTP)    │
│  │   ├─ agents/           │              │  ├─ BigQuery client   │
│  │   ├─ rules/            │              │  ├─ Audit logger      │
│  │   ├─ commands/         │              │  ├─ Cost estimator    │
│  │   ├─ hooks/            │              │  └─ Feedback logger   │
│  │   └─ .mcp.json (URL)  │              └──────────────────────┘
│  └─ ~/.claude/ (email)    │
└──────────────────────────┘               ┌──────────────────────┐
                                    Browser│ Streamlit Dashboard   │
                               ───────────▶│ (separate service)   │
                                           └──────────────────────┘
```

### Two Railway Services (same repo)

| Service | Purpose | URL |
|---------|---------|-----|
| **mcp-server** | Remote MCP endpoint | `https://taleemabad-mcp.up.railway.app/mcp` |
| **dashboard** | Observability UI (existing) | `https://taleemabad-dashboard.up.railway.app` |

Both deploy from the same Git repo. Railway natively supports multiple services per project.

## What Changes

### 1. MCP Server Transport

**Current:** `mcp.run()` → stdio transport (local only)

**New:** `mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)` → HTTP transport

FastMCP has built-in streamable-http support. Minimal code change in `cli.py`:

```python
@main.command()
def serve():
    """Run the MCP server."""
    from taleemabad_data_mcp.server import mcp
    mcp.run()  # stdio (local plugin)

@main.command()
def serve_remote():
    """Run the MCP server with HTTP transport for Railway."""
    import os
    from taleemabad_data_mcp.server import mcp
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
```

### Per-Request User Extraction

The current server reads `user_name` once at startup from an env file. For remote multi-user mode, user identity must be extracted **per-request** from the `X-Taleemabad-User` HTTP header.

**Approach:** FastMCP's streamable-http transport supports middleware/auth hooks. We add an authentication middleware that:
1. Reads `X-Taleemabad-User` header from each incoming request
2. Validates the email domain
3. Injects `user_email` into the request context (available to all tool handlers via `ctx`)
4. Rejects requests with missing/invalid headers

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("taleemabad-data", lifespan=app_lifespan)

ALLOWED_DOMAINS = {"taleemabad.com", "niete.edu.pk", "niete.pk"}

async def auth_middleware(request, call_next):
    """Extract and validate user email from request header."""
    email = request.headers.get("x-taleemabad-user", "")
    if not email or email.split("@")[-1] not in ALLOWED_DOMAINS:
        raise ValueError("Valid work email required. Run /taleemabad-setup first.")
    # Store in request state for tool handlers
    request.state.user_email = email
    request.state.user_name = email.split("@")[0]
    return await call_next(request)
```

The exact middleware API depends on FastMCP's HTTP transport implementation. During implementation, we'll verify the correct hook point (ASGI middleware, FastMCP auth handler, or Starlette middleware).

**Tool handlers** access the per-request user via the context object passed to each tool function, replacing the static lifespan-level `user_name`. The `AuditLogger` methods accept user identity as a parameter rather than reading from lifespan context.

### Concurrency

`google.cloud.bigquery.Client` is thread-safe and connection-pooled. Multiple concurrent users are supported without changes. The BigQuery client singleton created in lifespan is shared across all requests safely.

### Health Check

A `/health` endpoint is included for Railway health monitoring:

```python
@mcp.custom_route("/health", methods=["GET"])
async def health():
    """Health check for Railway."""
    return {"status": "ok", "version": __version__}
```

If FastMCP doesn't support custom routes natively, we wrap the app in a Starlette/ASGI middleware that handles `/health` before passing to FastMCP.

### 2. Plugin .mcp.json

**Current:**
```json
{
  "mcpServers": {
    "taleemabad-data": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "python", "-m", "taleemabad_data_mcp", "serve"],
      "env": {
        "BIGQUERY_PROJECT": "niete-bq-prod",
        "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
        "GOOGLE_APPLICATION_CREDENTIALS": "./niete-bq-prod-48ae5260d1ea.json",
        "TALEEMABAD_USER": "${TALEEMABAD_USER}"
      }
    }
  }
}
```

**New:**
```json
{
  "mcpServers": {
    "taleemabad-data": {
      "type": "url",
      "url": "https://taleemabad-mcp.up.railway.app/mcp",
      "headers": {
        "X-Taleemabad-User": "${TALEEMABAD_USER}"
      }
    }
  }
}
```

No local command, no env vars with credentials. Just a URL.

### 3. Email-Based User Identity

**Setup command** (`/taleemabad-setup`) changes from asking for name to asking for email:

- Prompt: "Enter your work email:"
- Validation: must end with `@taleemabad.com`, `@niete.edu.pk`, or `@niete.pk`
- Display name: extracted from email prefix (e.g., `ahwaz@taleemabad.com` → `ahwaz`)
- Stored in: `~/.claude/taleemabad-data-mcp.env` as `TALEEMABAD_USER=ahwaz@taleemabad.com`

**Server-side:** The `X-Taleemabad-User` header carries the email. The server:
- Validates the domain (rejects unknown domains)
- Extracts display name for audit logs
- Logs full email in audit entries

### 4. Railway Configuration (MCP Service)

**Railway service start command:** `bash railway_start_mcp.sh`

Configured via Railway service settings (each service has its own start command). No separate Procfile needed — the existing `Procfile` stays for the dashboard service.

**Environment variables on Railway:**
- `BIGQUERY_PROJECT=niete-bq-prod`
- `BIGQUERY_DATASETS=RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit`
- `GOOGLE_CREDENTIALS_JSON=<full JSON content>` (written to file at startup)
- `PORT` (auto-set by Railway)

**railway_start_mcp.sh:**
```bash
#!/bin/bash
set -e

# Write GCP credentials from env var
echo "$GOOGLE_CREDENTIALS_JSON" > /tmp/gcp-credentials.json
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-credentials.json

# Add src to Python path
python -c "import site; open(site.getsitepackages()[0]+'/app.pth','w').write('/app/src')"

# Start MCP server
python -m taleemabad_data_mcp serve-remote
```

## What Doesn't Change

- **8 of 9 MCP tools** — execute_query, list_datasets, get_table_schema, check_table_freshness, submit_feedback, get_version, preview_table, describe_data (unchanged)
- **`save_query_results` adaptation** — In remote mode, this tool returns file content as a base64-encoded string instead of writing to the server filesystem (Railway's filesystem is ephemeral). The agent receives the content and can present it to the user or save it locally.
- **Audit logging** — BigQuery writes to `mcp_audit.activity_log` remain primary. The local JSON Lines fallback (`~/.claude/taleemabad-logs/activity.jsonl`) is skipped in remote mode since Railway's filesystem is ephemeral — BigQuery is the only audit destination.
- **Cost guardrails** — same `maximum_bytes_billed` enforcement
- **Feedback system** — agent-driven, calls `submit_feedback` tool
- **Domain classification** — same auto-tagging
- **Agents** — `data-analyst.md` and `data-admin.md` stay in plugin, run locally in Claude Code
- **Rules** — governance rules stay in plugin, synced to `~/.claude/rules/`
- **Commands/hooks** — stay in plugin
- **Dashboard** — stays on its current Railway service, no changes

## User Experience

### Before (current)
1. `claude plugin marketplace add Orenda-Project/taleemabad-data-mcp`
2. `claude plugin install taleemabad-data@Orenda-Project`
3. Copy `niete-bq-prod-48ae5260d1ea.json` to project directory
4. Ensure Python + uv are installed
5. `/taleemabad-setup` → enter name
6. Start querying

### After (new)
1. `claude plugin marketplace add Orenda-Project/taleemabad-data-mcp`
2. `claude plugin install taleemabad-data@Orenda-Project`
3. `/taleemabad-setup` → enter work email + paste team token (shared once by admin)
4. Start querying

Steps 3-4 from "before" (credentials file + Python/uv) are eliminated entirely. The team token is a one-time share — same token for everyone, provided in the team onboarding channel.

## Email Validation

### Allowed Domains
- `@taleemabad.com`
- `@niete.edu.pk`
- `@niete.pk`

### Validation Flow
```
User enters: ahwaz@taleemabad.com
  ├─ Domain check: taleemabad.com ✓
  ├─ Extract name: "ahwaz"
  ├─ Save to ~/.claude/taleemabad-data-mcp.env
  └─ Done

User enters: random@gmail.com
  ├─ Domain check: gmail.com ✗
  └─ Error: "Please use your work email (@taleemabad.com, @niete.edu.pk, or @niete.pk)"
```

### Server-Side Validation
The MCP server also validates the `X-Taleemabad-User` header:
- Missing header → reject with "Setup required" message
- Invalid domain → reject with "Unauthorized domain"
- Valid → extract name, proceed, log in audit

## Audit Log Enhancement

Current audit entry fields remain. The existing `user_name` field is repurposed to store the full email. Two new fields are added:
- `user_email`: full email (e.g., `ahwaz@taleemabad.com`) — replaces the old free-text `user_name`
- `user_domain`: organization domain (e.g., `taleemabad.com`) — new field

The `AuditLogEntry` model in `models/audit.py` is updated with these fields. The BigQuery audit table schema in `audit_logger.py` (`_ensure_audit_table`) is extended — BigQuery supports adding nullable columns to existing tables without migration.

This enables:
- Per-user query history
- Per-organization usage breakdown
- Usage dashboards filtered by team

## Security Considerations

- **Transport:** HTTPS (Railway provides TLS automatically)
- **Authentication:** Two layers:
  1. **Shared bearer token** — A `TALEEMABAD_API_TOKEN` environment variable on Railway. The plugin sends it via `Authorization: Bearer <token>` header. This prevents unauthorized access even if someone discovers the URL. The token is set during `/taleemabad-setup` (provided by admin) and stored in `~/.claude/taleemabad-data-mcp.env`.
  2. **Email domain validation** — After token check, validates email domain for identity.
- **Authorization:** All authenticated users have same access level (governed by rules, not per-user permissions)
- **Credentials:** GCP service account key lives only on Railway, never on user machines
- **Audit:** Every request logged with user email, query, cost, timestamp
- **Trust model:** Internal team tool. Bearer token + email domain validation. Token can be rotated if compromised.
- **Spoofing risk:** Email is self-reported but token-gated. An attacker needs both the token AND a valid email domain. Acceptable for internal use.

**Updated `.mcp.json` with auth:**
```json
{
  "mcpServers": {
    "taleemabad-data": {
      "type": "url",
      "url": "https://taleemabad-mcp.up.railway.app/mcp",
      "headers": {
        "X-Taleemabad-User": "${TALEEMABAD_USER}",
        "Authorization": "Bearer ${TALEEMABAD_API_TOKEN}"
      }
    }
  }
}
```

## Files to Create/Modify

### New Files
- `railway_start_mcp.sh` — startup script for MCP Railway service

### Modified Files
- `src/taleemabad_data_mcp/cli.py` — add `serve-remote` command
- `src/taleemabad_data_mcp/server.py` — add auth middleware, per-request user extraction, health check, adapt `save_query_results` for remote mode
- `src/taleemabad_data_mcp/engine/audit_logger.py` — add `user_email`/`user_domain` fields, skip local fallback in remote mode
- `src/taleemabad_data_mcp/models/audit.py` — add `user_email` and `user_domain` to `AuditLogEntry`
- `.mcp.json` — switch to URL-based remote config with auth header
- `commands/setup.md` — change from name to email prompt with domain validation, add token setup step
- `requirements.txt` — add `uvicorn` if needed by FastMCP HTTP transport
- `pyproject.toml` — add uvicorn to base dependencies

### Railway Configuration
- Create second Railway service pointing to same repo
- Set start command: `bash railway_start_mcp.sh`
- Set environment variables (BIGQUERY_PROJECT, BIGQUERY_DATASETS, GOOGLE_CREDENTIALS_JSON)

## Testing Plan

1. **Local HTTP test:** Run `serve-remote` locally, connect Claude Code to `http://localhost:8000/mcp`
2. **Email validation:** Test valid/invalid emails in setup command
3. **Header propagation:** Verify `X-Taleemabad-User` reaches server and appears in audit logs
4. **All 9 tools:** Verify each tool works over HTTP transport
5. **Railway deployment:** Deploy, verify public URL works
6. **End-to-end:** Fresh plugin install → setup → query → verify audit log

## Rollback Plan

If remote deployment has issues:
- Plugin `.mcp.json` can switch back to `command`-based local mode
- Add both configs and use an environment variable to toggle
- Users who have Python/uv/credentials can fall back to local mode

## Request Timeout Considerations

BigQuery queries can take 30+ seconds. Railway's default request timeout varies by plan. For long-running queries:
- Configure Railway service timeout to 120s (via Railway dashboard)
- FastMCP's streamable-http transport handles long-lived connections
- The `maximum_bytes_billed` guardrail already limits query size, which indirectly limits duration

## Future Enhancements (not in scope)

- Per-user rate limiting
- Per-user API keys (if team grows beyond shared token model)
- WebSocket transport for lower latency
- Operational metrics dashboard (HTTP request latency, error rates, connection counts)

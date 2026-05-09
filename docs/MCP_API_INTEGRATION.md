# Custom Data MCP — API Integration Guide

**Base URL:** `https://mcp-server-production-337f.up.railway.app`

---

## Overview

The Custom Data MCP server provides governed access to BigQuery datasets across all regions (ICT, Rawalpindi, Moawin/Akhuwat, MySchool). It runs on Railway and exposes tools via the MCP protocol (JSON-RPC 2.0 over HTTP).

**No API keys or credentials are needed on the client side.** BigQuery authentication is handled server-side.

---

## Connection Methods

### 1. Claude Code (Recommended for AI workflows)

Add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "custom-data": {
      "type": "url",
      "url": "https://mcp-server-production-337f.up.railway.app/mcp"
    }
  }
}
```

Or add to user settings at `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "custom-data": {
      "type": "url",
      "url": "https://mcp-server-production-337f.up.railway.app/mcp"
    }
  }
}
```

### 2. REST/HTTP (For Flask, Python scripts, dashboards, etc.)

All requests use **JSON-RPC 2.0** format, sent as `POST` to a single endpoint:

```
POST https://mcp-server-production-337f.up.railway.app/mcp
Content-Type: application/json
```

---

## Health Check

Verify the server is running:

```bash
curl https://mcp-server-production-337f.up.railway.app/health
```

**Response:**
```json
{"status": "ok", "version": "0.17.15"}
```

---

## Available Tools

| Tool | Purpose |
|------|---------|
| `get_version` | Server version, user, project, available datasets |
| `execute_query` | Run SQL against BigQuery (with cost guardrails) |
| `list_datasets` | Browse all accessible BigQuery datasets and tables |
| `get_table_schema` | Get columns and types for a specific table |
| `check_table_freshness` | Check when a table was last modified |
| `preview_table` | Quick peek at table rows (max 50) |
| `describe_data` | Descriptive statistics on query results |
| `save_query_results` | Export query results to CSV or JSON |
| `submit_feedback` | Log thumbs up/down on a query result |

---

## curl Examples

### List available tools

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Get server version

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_version",
      "arguments": {}
    }
  }'
```

### List all datasets

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_datasets",
      "arguments": {}
    }
  }'
```

### Get table schema

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_table_schema",
      "arguments": {
        "dataset": "tbproddb",
        "table": "users_user"
      }
    }
  }'
```

### Check table freshness

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "check_table_freshness",
      "arguments": {
        "dataset": "tbproddb",
        "table": "analytics_events"
      }
    }
  }'
```

### Execute a query

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "execute_query",
      "arguments": {
        "sql": "SELECT COUNT(*) as total_teachers FROM tbproddb.users_user WHERE is_active = '\''true'\'' AND organization_id = 1 LIMIT 1",
        "question": "How many active teachers in ICT?"
      }
    }
  }'
```

### Dry run (estimate cost without executing)

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "execute_query",
      "arguments": {
        "sql": "SELECT * FROM tbproddb.analytics_events WHERE sent_at >= DATE('\''2026-04-01'\'') LIMIT 100",
        "question": "Preview recent events",
        "dry_run": true
      }
    }
  }'
```

### Preview table rows

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "preview_table",
      "arguments": {
        "dataset": "tbproddb",
        "table": "coaching_observation",
        "limit": 5
      }
    }
  }'
```

### Describe data (statistics)

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "describe_data",
      "arguments": {
        "sql": "SELECT overall_percentage, gender FROM tbproddb.fico_kpis LIMIT 100",
        "question": "Describe ACR score distribution"
      }
    }
  }'
```

### Save query results (returns file content in remote mode)

```bash
curl -X POST https://mcp-server-production-337f.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "save_query_results",
      "arguments": {
        "sql": "SELECT teacher_name, overall_percentage FROM tbproddb.fico_kpis LIMIT 10",
        "question": "Export top teacher scores",
        "format": "csv"
      }
    }
  }'
```

---

## Python Integration Example

```python
import requests

MCP_URL = "https://mcp-server-production-337f.up.railway.app/mcp"

def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool and return the response."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    response = requests.post(MCP_URL, json=payload)
    response.raise_for_status()
    return response.json()


# Example: Get server version
result = call_mcp_tool("get_version", {})
print(result)

# Example: Execute a query
result = call_mcp_tool("execute_query", {
    "sql": "SELECT COUNT(*) as cnt FROM tbproddb.users_user WHERE is_active = 'true'",
    "question": "Total active users",
})
print(result)

# Example: Get table schema
result = call_mcp_tool("get_table_schema", {
    "dataset": "tbproddb",
    "table": "coaching_observation",
})
print(result)

# Example: Check freshness
result = call_mcp_tool("check_table_freshness", {
    "dataset": "tbproddb",
    "table": "analytics_events",
})
print(result)
```

---

## Tool Parameter Reference

### execute_query

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | SQL query to execute |
| `question` | string | No | User's original question (for audit logging) |
| `dry_run` | boolean | No | If true, only estimate cost (default: false) |

**Cost guardrails:** Queries are capped at 500 MB billed bytes by default. Use `dry_run: true` to check estimated cost before executing expensive queries.

**Returns:** JSON array of up to 100 result rows, or cost estimate if dry_run.

### list_datasets

No parameters. Returns all accessible BigQuery datasets and their tables.

### get_table_schema

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dataset` | string | Yes | BigQuery dataset name (e.g., `tbproddb`) |
| `table` | string | Yes | Table name (e.g., `users_user`) |

### check_table_freshness

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dataset` | string | Yes | BigQuery dataset name |
| `table` | string | Yes | Table name |

### preview_table

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dataset` | string | Yes | BigQuery dataset name |
| `table` | string | Yes | Table name |
| `limit` | integer | No | Max rows (default: 10, max: 50) |
| `partition_filter` | string | No | WHERE condition (e.g., `sent_at >= DATE('2026-01-01')`) |

### describe_data

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | SQL query to execute |
| `question` | string | No | User's original question |

### save_query_results

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | SQL query to execute |
| `question` | string | No | User's original question |
| `format` | string | No | `csv` or `json` (default: `csv`) |

### submit_feedback

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_id` | string | Yes | Audit log event ID of the query |
| `rating` | string | Yes | `up` or `down` |
| `comment` | string | No | Free-text feedback |

---

## Available Datasets

| Dataset | Region | Description |
|---------|--------|-------------|
| `tbproddb` | ICT/Islamabad | 466 tables — teachers, coaching, training, events, FICO |
| `RUMI_DB` | Rawalpindi | 70 tables — AI coaching, lesson plans, reading assessments |
| `TaleemHub_DB` | Rawalpindi | 60 tables — teacher roster, mentoring visits, ASER |
| `Muawin_Akhuwat_db` | Moawin/Akhuwat | ~50 tables — teachers, attendance, student scores |
| `Zavia_db` | Moawin/Akhuwat | ~57 tables — AI coaching, lesson plans, reading assessments |
| `MySchool_db` | School Management | 59 tables — staff, students, infrastructure |
| `odk` | Impact Studies | 52 tables — ASER endline/baseline assessments |

---

## Response Format

All responses follow JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "... tool output here ..."
      }
    ]
  }
}
```

The actual tool output is in `result.content[0].text` as a string. For `execute_query`, this string contains JSON-formatted query results.

---

## Error Handling

- **Query syntax errors:** Returned as `Query failed: BadRequest: ...`
- **Table not found:** Returned as `Query failed: NotFound: ...`
- **Cost limit exceeded:** Query is blocked before execution
- **Server down:** HTTP 5xx — check `/health` endpoint

---

## Notes

- All queries are audit-logged with timestamps, cost, and domain classification
- Maximum 100 rows returned per `execute_query` call
- Banned table: `analytics_analyticsevent` (unpartitioned, 68.6 GB) — use `analytics_events` instead
- The `question` parameter on `execute_query` is optional but recommended for audit trail
- In remote mode, `save_query_results` returns file content as a string (no server-side file storage)

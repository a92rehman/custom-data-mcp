# FastMCP Research Report: Building a Data Governance MCP Server

**Date:** 2026-04-04
**SDK Version Analyzed:** MCP Python SDK v1.27.0 (released April 2, 2026)
**Protocol Version:** 2025-06-18

---

## Table of Contents

1. [SDK Overview and Project Structure](#1-sdk-overview-and-project-structure)
2. [Core API: Tools, Resources, and Prompts](#2-core-api-tools-resources-and-prompts)
3. [Transport Patterns](#3-transport-patterns)
4. [Lifespan and Dependency Injection](#4-lifespan-and-dependency-injection)
5. [Error Handling Patterns](#5-error-handling-patterns)
6. [Input Validation](#6-input-validation)
7. [Logging and Observability](#7-logging-and-observability)
8. [Testing MCP Servers](#8-testing-mcp-servers)
9. [Configuration and Secrets Management](#9-configuration-and-secrets-management)
10. [Real-World BigQuery MCP Server Analysis](#10-real-world-bigquery-mcp-server-analysis)
11. [7 Mistakes to Avoid](#11-seven-mistakes-to-avoid)
12. [Recommended Architecture for Data Governance MCP Server](#12-recommended-architecture-for-data-governance-mcp-server)
13. [pyproject.toml Reference](#13-pyprojecttoml-reference)
14. [Key Decisions and Recommendations](#14-key-decisions-and-recommendations)
15. [Citations](#15-citations)

---

## 1. SDK Overview and Project Structure

### The MCP Python SDK

The official Python SDK (`mcp` package on PyPI) is maintained by Anthropic at
`modelcontextprotocol/python-sdk` on GitHub (22.5k+ stars, 3.3k+ forks, 842+ commits).
It is the canonical way to build MCP servers in Python.

**Installation:**

```bash
# Recommended: using uv
uv add "mcp[cli]"

# Alternative: pip
pip install "mcp[cli]"
```

The `[cli]` extra includes the MCP Inspector for debugging and the `mcp` CLI tool.

### Recommended Project Structure

```
my-mcp-server/
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       ├── __main__.py          # Entry point: python -m my_mcp_server
│       ├── server.py            # FastMCP instance and tool/resource/prompt definitions
│       ├── config.py            # Configuration management (env vars, settings)
│       ├── tools/               # Tool implementations organized by domain
│       │   ├── __init__.py
│       │   ├── query_tools.py
│       │   ├── schema_tools.py
│       │   └── governance_tools.py
│       ├── resources/           # Resource definitions
│       │   └── __init__.py
│       └── prompts/             # Prompt templates
│           └── __init__.py
├── tests/
│   ├── conftest.py              # Shared fixtures (mcp_client fixture)
│   ├── test_tools.py
│   ├── test_resources.py
│   └── test_integration.py
├── pyproject.toml
├── .env.example
└── README.md
```

The `src/` layout is recommended to prevent import issues during development and
follows standard Python packaging conventions.

---

## 2. Core API: Tools, Resources, and Prompts

### FastMCP Server Initialization

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "DataGovernance",
    json_response=True,  # Return JSON-formatted responses
)
```

### Tools (Executable Functions)

Tools are the primary mechanism for LLMs to perform actions. FastMCP auto-generates
JSON schemas from Python type hints and docstrings.

```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations

READ_ONLY = ToolAnnotations(readOnlyHint=True)
MUTATING = ToolAnnotations(readOnlyHint=False, destructiveHint=True)

@mcp.tool(annotations=READ_ONLY)
async def query_table(
    project_id: str,
    dataset: str,
    table: str,
    sql: str,
    ctx: Context,
) -> str:
    """Execute a read-only SQL query against a BigQuery table.

    Args:
        project_id: GCP project ID (e.g., 'my-project-123')
        dataset: BigQuery dataset name
        table: Table name to query
        sql: SQL query to execute (SELECT only)
    """
    await ctx.info(f"Executing query on {project_id}.{dataset}.{table}")
    await ctx.report_progress(progress=0, total=100)
    # ... execute query ...
    await ctx.report_progress(progress=100, total=100)
    return results
```

### Resources (Data Sources)

Resources expose data that clients can read. They support URI templates for
parameterized access.

```python
@mcp.resource("governance://policies/{policy_name}")
def get_policy(policy_name: str) -> str:
    """Retrieve a data governance policy document."""
    return load_policy(policy_name)

@mcp.resource("schema://bigquery/{project}/{dataset}/{table}")
async def get_table_schema(project: str, dataset: str, table: str) -> str:
    """Get the schema definition for a BigQuery table."""
    client = bigquery.Client(project=project)
    table_ref = client.get_table(f"{project}.{dataset}.{table}")
    return json.dumps([
        {"name": f.name, "type": f.field_type, "description": f.description}
        for f in table_ref.schema
    ], indent=2)
```

### Prompts (Reusable Templates)

Prompts provide pre-written interaction templates that help users accomplish tasks.

```python
@mcp.prompt()
def data_quality_check(dataset: str, table: str) -> str:
    """Generate a prompt for performing a data quality assessment."""
    return f"""Analyze the data quality of {dataset}.{table}. Check for:
    1. Null values in required columns
    2. Data type consistency
    3. Referential integrity
    4. Freshness (last update timestamp)
    5. Row count anomalies vs. historical patterns

    Use the query_table and describe_table tools to investigate."""
```

### Structured Output with Pydantic

Tools can return Pydantic models for structured, schema-validated output:

```python
from pydantic import BaseModel

class TableInfo(BaseModel):
    project: str
    dataset: str
    table: str
    row_count: int
    size_bytes: int
    last_modified: str
    columns: list[dict]

@mcp.tool(annotations=READ_ONLY)
async def describe_table(project: str, dataset: str, table: str) -> TableInfo:
    """Get detailed metadata about a BigQuery table."""
    # FastMCP automatically generates JSON schema from TableInfo
    ...
```

---

## 3. Transport Patterns

### Transport Comparison

| Feature | stdio | Streamable HTTP | SSE (Deprecated) |
|---------|-------|----------------|-------------------|
| **Use case** | Local CLI tools, Claude Desktop | Remote servers, multi-client | Legacy only |
| **Scaling** | Single process, single client | Horizontal, multi-client | Limited |
| **Authentication** | Process-level | HTTP headers, OAuth, JWT | HTTP headers |
| **Long-running ops** | Supported via protocol | SSE streaming + heartbeats | SSE streaming |
| **Deployment** | Local machine only | Cloud, edge, containers | Cloud |
| **Network** | No network overhead | Standard HTTP | HTTP |

### When to Use Which

**stdio** -- Use for local development, Claude Desktop integration, and single-user tools.
This is the simplest transport and the default for `mcp.run()`.

```python
# For Claude Desktop / Claude Code integration
mcp.run(transport="stdio")
```

**Streamable HTTP** -- Use for production deployments, multi-user access, remote servers,
and when you need authentication. This is the recommended transport for production.

```python
# For production deployment
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

**SSE** -- Deprecated as of protocol version 2025-03-26. Do not use for new implementations.

### Handling Long-Running Queries (Critical for BigQuery)

BigQuery queries can take seconds to minutes. Use the Context object's progress
reporting combined with Streamable HTTP's SSE streaming:

```python
@mcp.tool(annotations=READ_ONLY)
async def run_bigquery_job(sql: str, ctx: Context) -> str:
    """Execute a BigQuery SQL query with progress tracking."""
    client = bigquery.Client()

    # Start the query job
    query_job = client.query(sql)
    await ctx.info(f"Query job started: {query_job.job_id}")
    await ctx.report_progress(progress=0, total=100)

    # Poll for completion with progress updates
    import asyncio
    while not query_job.done():
        await asyncio.sleep(2)
        # BigQuery doesn't give granular progress, but we can signal activity
        await ctx.info(f"Job {query_job.job_id} still running...")
        await ctx.report_progress(progress=50, total=100)

    if query_job.errors:
        await ctx.error(f"Query failed: {query_job.errors}")
        return f"ERROR: {query_job.errors}"

    results = query_job.result()
    await ctx.report_progress(progress=100, total=100)
    return format_results(results)
```

### Authentication with Streamable HTTP

The MCP specification recommends OAuth for production authentication. The SDK
supports session IDs via `Mcp-Session-Id` headers and standard HTTP auth:

```python
# Server-side: Mount with authentication middleware
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

mcp = FastMCP("DataGovernance")

# When running as streamable-http, configure auth at the ASGI level
# or use the built-in OAuth discovery endpoints
mcp.run(
    transport="streamable-http",
    host="0.0.0.0",
    port=8000,
)
```

For local/internal use, API key authentication via environment variables is common:

```json
{
  "mcpServers": {
    "data-governance": {
      "command": "uvx",
      "args": ["taleemabad-data-mcp"],
      "env": {
        "BIGQUERY_PROJECT": "my-project",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json"
      }
    }
  }
}
```

---

## 4. Lifespan and Dependency Injection

### Lifespan Pattern (Server-Wide Resources)

Use the lifespan pattern to manage expensive resources like database connections,
BigQuery clients, and caches that should persist across requests:

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
from google.cloud import bigquery

@dataclass
class AppContext:
    bq_client: bigquery.Client
    project_id: str
    allowed_datasets: list[str]

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize and clean up server-wide resources."""
    project_id = os.environ["BIGQUERY_PROJECT"]
    key_file = os.environ.get("BIGQUERY_KEY_FILE")

    if key_file:
        bq_client = bigquery.Client.from_service_account_json(key_file)
    else:
        bq_client = bigquery.Client(project=project_id)

    allowed_datasets = os.environ.get("BIGQUERY_DATASETS", "").split(",")

    try:
        yield AppContext(
            bq_client=bq_client,
            project_id=project_id,
            allowed_datasets=allowed_datasets,
        )
    finally:
        bq_client.close()

mcp = FastMCP("DataGovernance", lifespan=app_lifespan)
```

### Accessing Lifespan Context in Tools

```python
@mcp.tool(annotations=READ_ONLY)
async def list_datasets(ctx: Context) -> list[str]:
    """List all accessible BigQuery datasets."""
    app: AppContext = ctx.request_context.lifespan_context
    datasets = list(app.bq_client.list_datasets(app.project_id))
    return [ds.dataset_id for ds in datasets]
```

### Session State (Per-Client State)

For state that should persist across multiple requests within a single client session:

```python
@mcp.tool()
async def set_active_dataset(dataset: str, ctx: Context) -> str:
    """Set the active dataset for subsequent queries."""
    await ctx.set_state("active_dataset", dataset)
    return f"Active dataset set to: {dataset}"

@mcp.tool(annotations=READ_ONLY)
async def query_active_dataset(sql: str, ctx: Context) -> str:
    """Query the currently active dataset."""
    dataset = await ctx.get_state("active_dataset")
    if not dataset:
        return "ERROR: No active dataset set. Use set_active_dataset first."
    # ... run query against the active dataset
```

---

## 5. Error Handling Patterns

### Principle: Surface Full Errors to the LLM

Generic error messages cause expensive retry loops. The LLM needs detailed error
information to self-correct.

```python
@mcp.tool(annotations=READ_ONLY)
async def execute_query(sql: str, ctx: Context) -> str:
    """Execute a SQL query against BigQuery."""
    app: AppContext = ctx.request_context.lifespan_context
    try:
        query_job = app.bq_client.query(sql)
        results = query_job.result()
        return format_results(results)

    except google.api_core.exceptions.BadRequest as e:
        # Surface the FULL error message -- do not truncate
        await ctx.error(f"BigQuery SQL error: {e}")
        return (
            f"SQL Error: {e.message}\n\n"
            f"The query had a syntax or semantic error. "
            f"Please review the SQL and try again. "
            f"Common issues: incorrect column names, missing backticks "
            f"around reserved words, or wrong table references."
        )

    except google.api_core.exceptions.Forbidden as e:
        await ctx.error(f"Permission denied: {e}")
        return (
            f"Permission Denied: You do not have access to the requested "
            f"resource. Ensure the service account has bigquery.dataViewer "
            f"and bigquery.jobUser roles."
        )

    except google.api_core.exceptions.NotFound as e:
        await ctx.error(f"Resource not found: {e}")
        return (
            f"Not Found: {e.message}\n"
            f"Use list_datasets and list_tables to discover available resources."
        )

    except Exception as e:
        await ctx.error(f"Unexpected error: {type(e).__name__}: {e}")
        return f"Unexpected error: {type(e).__name__}: {e}"
```

### Using isError for Tool Results

For advanced control, return `CallToolResult` directly to signal errors at the
protocol level:

```python
from mcp.types import CallToolResult, TextContent

@mcp.tool(annotations=READ_ONLY)
async def strict_query(sql: str) -> CallToolResult:
    """Execute a query with protocol-level error signaling."""
    try:
        result = execute(sql)
        return CallToolResult(
            content=[TextContent(type="text", text=result)],
            isError=False,
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=str(e))],
            isError=True,
        )
```

---

## 6. Input Validation

### Pydantic Field Annotations

Use `Annotated` with Pydantic `Field` for self-documenting, validated parameters:

```python
from typing import Annotated
from pydantic import Field

ProjectId = Annotated[str, Field(
    description="Google Cloud project ID",
    pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
    examples=["my-project-123"],
)]

DatasetId = Annotated[str, Field(
    description="BigQuery dataset identifier",
    pattern=r"^[a-zA-Z_][a-zA-Z0-9_]{0,1023}$",
    examples=["analytics_prod"],
)]

SqlQuery = Annotated[str, Field(
    description="SQL query to execute. Must be a SELECT statement.",
    min_length=1,
    max_length=100_000,
)]

@mcp.tool(annotations=READ_ONLY)
async def query_table(
    project: ProjectId,
    dataset: DatasetId,
    sql: SqlQuery,
    max_rows: Annotated[int, Field(
        description="Maximum rows to return",
        ge=1,
        le=10_000,
        default=1000,
    )] = 1000,
) -> str:
    """Execute a read-only query against a BigQuery table."""
    ...
```

### SQL Injection Prevention

LLM-generated strings must be treated as untrusted user input:

```python
import re

FORBIDDEN_SQL_PATTERNS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b",
    r"\bUPDATE\b", r"\bCREATE\b", r"\bALTER\b",
    r"\bTRUNCATE\b", r"\bMERGE\b",
]

def validate_read_only_sql(sql: str) -> str:
    """Validate that SQL is read-only."""
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        raise ValueError("Only SELECT and WITH (CTE) queries are allowed.")
    for pattern in FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, sql_upper):
            raise ValueError(f"Forbidden SQL operation detected: {pattern}")
    return sql
```

---

## 7. Logging and Observability

### STDIO Logging Constraint

**Critical:** For stdio transport, never write to stdout. It will corrupt JSON-RPC
messages. Use stderr or the MCP logging protocol instead.

```python
import sys
import logging

# Configure Python logging to stderr
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("data-governance-mcp")
```

### MCP Protocol Logging (Client-Visible)

Use the Context object to send log messages visible to the MCP client/host:

```python
@mcp.tool()
async def audit_table(table: str, ctx: Context) -> str:
    """Run a data governance audit on a table."""
    await ctx.info(f"Starting audit of {table}")
    await ctx.debug("Checking column-level policies...")
    # ...
    await ctx.warning("3 columns lack descriptions")
    # ...
    await ctx.info(f"Audit complete for {table}")
    return audit_report
```

### Structured Logging for Production

```python
import structlog

logger = structlog.get_logger()

@mcp.tool(annotations=READ_ONLY)
async def query_with_audit(sql: str, ctx: Context) -> str:
    """Execute query with structured audit logging."""
    logger.info(
        "query_executed",
        sql=sql[:200],  # Truncate for log safety
        request_id=ctx.request_id,
        client_id=ctx.client_id,
        session_id=ctx.session_id,
    )
    ...
```

---

## 8. Testing MCP Servers

### Setup

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "inline-snapshot",
]
```

### In-Memory Client Testing (Recommended Pattern)

FastMCP supports testing without subprocess overhead using an in-memory client:

```python
# tests/conftest.py
import pytest
from mcp.client import Client
from my_mcp_server.server import mcp  # Import your FastMCP instance

@pytest.fixture
async def mcp_client():
    """Create an in-memory MCP client connected to the server."""
    async with Client(transport=mcp) as client:
        yield client
```

### Tool Tests

```python
# tests/test_tools.py
import pytest

async def test_list_datasets(mcp_client):
    """Test that list_datasets returns expected datasets."""
    result = await mcp_client.call_tool("list_datasets", {})
    assert result is not None
    # Use inline-snapshot for complex assertions
    # Run: pytest --inline-snapshot=fix,create
    assert result == snapshot(...)

async def test_query_with_invalid_sql(mcp_client):
    """Test that invalid SQL returns a helpful error."""
    result = await mcp_client.call_tool("execute_query", {
        "sql": "DROP TABLE users"
    })
    assert "Forbidden SQL operation" in str(result)

@pytest.mark.parametrize("sql,expected_error", [
    ("DELETE FROM table", "Forbidden SQL operation"),
    ("INSERT INTO table VALUES (1)", "Forbidden SQL operation"),
    ("", "min_length"),
])
async def test_sql_validation(sql, expected_error, mcp_client):
    result = await mcp_client.call_tool("execute_query", {"sql": sql})
    assert expected_error in str(result)
```

### Tool Discovery Tests

```python
async def test_tool_listing(mcp_client):
    """Verify all expected tools are registered."""
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert "list_datasets" in tool_names
    assert "describe_table" in tool_names
    assert "execute_query" in tool_names

async def test_tool_annotations(mcp_client):
    """Verify read-only tools are properly annotated."""
    tools = await mcp_client.list_tools()
    query_tool = next(t for t in tools if t.name == "execute_query")
    assert query_tool.annotations.readOnlyHint is True
```

### Testing with Mocked BigQuery

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_bq_client():
    with patch("my_mcp_server.tools.query_tools.bigquery.Client") as mock:
        client = mock.return_value
        client.query.return_value.result.return_value = [
            {"id": 1, "name": "test"}
        ]
        yield client

async def test_query_with_mock(mcp_client, mock_bq_client):
    result = await mcp_client.call_tool("execute_query", {
        "sql": "SELECT * FROM dataset.table LIMIT 10"
    })
    assert "test" in str(result)
    mock_bq_client.query.assert_called_once()
```

---

## 9. Configuration and Secrets Management

### Environment Variables (Dominant Pattern)

Every real-world MCP server examined uses environment variables as the primary
configuration mechanism. This aligns with how MCP hosts pass configuration:

```python
# src/my_mcp_server/config.py
import os
from dataclasses import dataclass, field

@dataclass
class ServerConfig:
    """Server configuration from environment variables."""
    # Required
    bigquery_project: str = field(
        default_factory=lambda: os.environ["BIGQUERY_PROJECT"]
    )
    bigquery_location: str = field(
        default_factory=lambda: os.environ.get("BIGQUERY_LOCATION", "US")
    )

    # Optional
    bigquery_datasets: list[str] = field(default_factory=lambda: [
        ds.strip()
        for ds in os.environ.get("BIGQUERY_DATASETS", "").split(",")
        if ds.strip()
    ])
    bigquery_key_file: str | None = field(
        default_factory=lambda: os.environ.get("BIGQUERY_KEY_FILE")
    )
    bigquery_timeout: int = field(
        default_factory=lambda: int(os.environ.get("BIGQUERY_TIMEOUT", "300"))
    )
    max_rows: int = field(
        default_factory=lambda: int(os.environ.get("MAX_ROWS", "10000"))
    )
    max_bytes_billed: int = field(
        default_factory=lambda: int(
            os.environ.get("MAX_BYTES_BILLED", str(1024**3))  # 1 GB default
        )
    )
```

### Pydantic Settings Alternative

For more complex validation:

```python
from pydantic_settings import BaseSettings

class ServerConfig(BaseSettings):
    bigquery_project: str
    bigquery_location: str = "US"
    bigquery_datasets: list[str] = []
    bigquery_key_file: str | None = None
    bigquery_timeout: int = 300
    max_rows: int = 10_000
    max_bytes_billed: int = 1024**3

    model_config = {"env_prefix": "BIGQUERY_", "env_file": ".env"}
```

### Client Configuration (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "data-governance": {
      "command": "uvx",
      "args": ["taleemabad-data-mcp"],
      "env": {
        "BIGQUERY_PROJECT": "taleemabad-prod",
        "BIGQUERY_LOCATION": "US",
        "BIGQUERY_DATASETS": "analytics,curriculum,assessments",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json"
      }
    }
  }
}
```

### Secrets Handling

- **NEVER** store credentials in plaintext in code or config files
- Use `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to a service account JSON file
- For local development, use `gcloud auth application-default login`
- For production, use workload identity federation or mounted secrets
- Include `.env` and `*-credentials.json` in `.gitignore`

---

## 10. Real-World BigQuery MCP Server Analysis

### Surveyed Projects

| Project | Language | Stars | Key Pattern |
|---------|----------|-------|-------------|
| LucasHild/mcp-server-bigquery | Python | Notable | 3 tools: execute-query, list-tables, describe-table |
| ergut/mcp-bigquery-server | TypeScript | Notable | Read-only, 1GB query limit, Smithery install |
| pvoo/bigquery-mcp | Python | Notable | Vector search, context-optimized |
| caron14/mcp-bigquery | Python | Active (v0.5.0) | SQL validation, dry-run, dependency analysis |
| aicayzer/bigquery-mcp | Python | Notable | Multi-project, Docker support |

### Common Patterns Across BigQuery MCP Servers

1. **Three core tools minimum:** `list_tables`, `describe_table`, `execute_query`
2. **Read-only by default:** All servers enforce SELECT-only queries
3. **Query size limits:** Typically 1GB `max_bytes_billed` to prevent runaway costs
4. **Dual auth paths:** Service account JSON file OR Application Default Credentials
5. **Env var configuration:** Every server uses env vars, some also support CLI args
6. **Dataset filtering:** Allow restricting access to specific datasets via config
7. **Timeout configuration:** Query timeouts to prevent hanging connections

### Key Insight from caron14/mcp-bigquery (v0.5.0)

This server goes beyond basic querying to include SQL validation and dry-run analysis
-- exactly the kind of "governance" tooling relevant to our project. It exposes 8 tools
including schema discovery and dependency analysis, demonstrating that MCP servers
can provide sophisticated data governance capabilities.

---

## 11. Seven Mistakes to Avoid

Based on analysis from BigData Boutique's comprehensive guide [7]:

1. **Not marking mutating operations** -- Always use `ToolAnnotations` to declare
   `readOnlyHint=True` or `destructiveHint=True`. This lets clients auto-approve
   safe operations and prompt for dangerous ones.

2. **Exposing raw API primitives** -- Design tools around agent goals, not API
   endpoints. Instead of a raw `search(gaql_query)`, provide `get_campaigns(status, date_range)`.

3. **Missing safe defaults** -- Default to the safest option. For data governance,
   default to dry-run mode, read-only access, and limited row counts.

4. **Poor tool documentation** -- Use `Annotated[str, Field(description=..., examples=...)]`
   for every parameter. The LLM only sees the schema and description.

5. **Swallowing error messages** -- Surface full error bodies to the LLM. Generic
   "Bad Request" errors cause expensive retry loops.

6. **Wasteful token usage** -- Return CSV for tabular data (40-60% token savings).
   Offer JSON only when structured processing is needed.

7. **Ignoring security fundamentals** -- Validate all inputs at boundaries. Treat all
   LLM-generated strings as untrusted. Never store credentials in plaintext.

---

## 12. Recommended Architecture for Data Governance MCP Server

### Architecture Overview

```
                    +--------------------------+
                    |     MCP Host (Claude)    |
                    |      MCP Client          |
                    +-------------|------------+
                                  | stdio or streamable-http
                    +-------------|------------+
                    |  Data Governance MCP     |
                    |       Server             |
                    |                          |
                    |  +--------------------+  |
                    |  |   FastMCP Core     |  |
                    |  +--------------------+  |
                    |  |   Lifespan Mgmt    |  |
                    |  |   (BQ Client,      |  |
                    |  |    Config, Cache)   |  |
                    |  +--------------------+  |
                    |                          |
                    |  Tools:                  |
                    |  - list_datasets         |
                    |  - list_tables           |
                    |  - describe_table        |
                    |  - execute_query         |
                    |  - validate_sql          |
                    |  - check_data_quality    |
                    |  - get_column_lineage    |
                    |  - get_access_policies   |
                    |                          |
                    |  Resources:              |
                    |  - governance://policies  |
                    |  - schema://...          |
                    |                          |
                    |  Prompts:                |
                    |  - data_quality_check    |
                    |  - migration_review      |
                    +-------------|------------+
                                  |
                    +-------------|------------+
                    |    Google BigQuery       |
                    +--------------------------+
```

### Recommended Tool Set

```python
# Discovery tools (READ_ONLY)
@mcp.tool(annotations=READ_ONLY)
async def list_datasets(ctx: Context) -> str: ...

@mcp.tool(annotations=READ_ONLY)
async def list_tables(dataset: DatasetId, ctx: Context) -> str: ...

@mcp.tool(annotations=READ_ONLY)
async def describe_table(dataset: DatasetId, table: str, ctx: Context) -> str: ...

# Query tools (READ_ONLY)
@mcp.tool(annotations=READ_ONLY)
async def execute_query(sql: SqlQuery, ctx: Context) -> str: ...

@mcp.tool(annotations=READ_ONLY)
async def dry_run_query(sql: SqlQuery, ctx: Context) -> str: ...

# Governance tools (READ_ONLY)
@mcp.tool(annotations=READ_ONLY)
async def check_data_quality(dataset: DatasetId, table: str, ctx: Context) -> str: ...

@mcp.tool(annotations=READ_ONLY)
async def get_column_lineage(dataset: DatasetId, table: str, ctx: Context) -> str: ...

@mcp.tool(annotations=READ_ONLY)
async def get_access_policies(dataset: DatasetId, ctx: Context) -> str: ...

@mcp.tool(annotations=READ_ONLY)
async def validate_sql(sql: SqlQuery, ctx: Context) -> str: ...
```

### Entry Point

```python
# src/taleemabad_data_mcp/__main__.py
from .server import mcp

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

---

## 13. pyproject.toml Reference

```toml
[project]
name = "taleemabad-data-mcp"
version = "0.1.0"
description = "Data Governance MCP Server for Taleemabad BigQuery"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.26.0",
    "google-cloud-bigquery>=3.25.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "structlog>=24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "inline-snapshot>=0.13",
    "ruff>=0.6",
]

[project.scripts]
taleemabad-data-mcp = "taleemabad_data_mcp:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100
```

---

## 14. Key Decisions and Recommendations

### Decision 1: Transport -- Use stdio for initial release

**Rationale:** All BigQuery MCP servers in the wild use stdio. Claude Desktop and
Claude Code both support stdio natively. Streamable HTTP adds complexity (auth,
sessions, deployment) that is not needed for a single-user data governance tool.
Can migrate to Streamable HTTP later if multi-user access is needed.

### Decision 2: Configuration -- Environment variables with Pydantic Settings

**Rationale:** This is the universal pattern across all MCP servers examined. Env vars
integrate cleanly with `claude_desktop_config.json`'s `env` field. Pydantic Settings
adds type validation and `.env` file support.

### Decision 3: Authentication -- Google Application Default Credentials + service account option

**Rationale:** Support both `gcloud auth application-default login` for development and
`GOOGLE_APPLICATION_CREDENTIALS` / `BIGQUERY_KEY_FILE` for production. This matches
the pattern used by every BigQuery MCP server.

### Decision 4: Query Safety -- Read-only with dry-run and byte limits

**Rationale:** Enforce SELECT-only queries, provide `dry_run_query` for cost estimation,
and set `max_bytes_billed` (default 1 GB) to prevent runaway costs. This is the
universal safety pattern across BigQuery MCP servers.

### Decision 5: Response Format -- CSV for tabular data, JSON for metadata

**Rationale:** CSV reduces token usage by 40-60% for tabular query results. Use JSON
for structured metadata (schemas, policies, lineage).

### Decision 6: Testing -- In-memory client with pytest

**Rationale:** FastMCP's in-memory client testing eliminates subprocess overhead and
is the officially recommended pattern. Combine with pytest-asyncio and inline-snapshot.

### Decision 7: Tool Design -- Outcome-oriented, not API-wrapper

**Rationale:** Design tools around what the LLM/user wants to accomplish (e.g.,
"check data quality for this table") rather than raw API operations (e.g.,
"execute arbitrary SQL"). Include helper context in tool descriptions and error
messages to guide the LLM.

### Decision 8: Error Strategy -- Full error propagation with guidance

**Rationale:** Surface complete BigQuery error messages plus actionable guidance
(e.g., "Column X not found. Use describe_table to see available columns.").
This reduces retry loops and token waste.

---

## 15. Citations

[1] Anthropic. "Model Context Protocol Python SDK." GitHub, v1.27.0, April 2026.
    https://github.com/modelcontextprotocol/python-sdk

[2] Anthropic. "Model Context Protocol Introduction." modelcontextprotocol.io, 2026.
    https://modelcontextprotocol.io/introduction

[3] Anthropic. "Build an MCP Server." modelcontextprotocol.io, 2026.
    https://modelcontextprotocol.io/docs/develop/build-server

[4] Anthropic. "MCP Architecture Overview." modelcontextprotocol.io, 2026.
    https://modelcontextprotocol.io/docs/learn/architecture

[5] LucasHild. "mcp-server-bigquery." GitHub, 2025.
    https://github.com/LucasHild/mcp-server-bigquery

[6] ergut. "mcp-bigquery-server." GitHub, 2025.
    https://github.com/ergut/mcp-bigquery-server

[7] BigData Boutique. "Building MCP Servers with FastMCP: 7 Mistakes to Avoid." 2025.
    https://bigdataboutique.com/blog/building-mcp-servers-with-fastmcp-7-mistakes-to-avoid

[8] FastMCP Documentation. "Testing your FastMCP Server." gofastmcp.com, 2026.
    https://gofastmcp.com/servers/testing

[9] FastMCP Documentation. "MCP Context." gofastmcp.com, 2026.
    https://gofastmcp.com/servers/context

[10] MCPcat. "Build StreamableHTTP MCP Servers - Production Guide." mcpcat.io, 2026.
     https://mcpcat.io/guides/building-streamablehttp-mcp-server/

[11] caron14. "mcp-bigquery - MCP Server for BigQuery." GitHub, v0.5.0, 2026.
     https://github.com/caron14/mcp-bigquery

[12] pvoo. "bigquery-mcp - Practical MCP server for large BigQuery datasets." GitHub, 2025.
     https://github.com/pvoo/bigquery-mcp

[13] PyPI. "mcp 1.27.0." Python Package Index, April 2, 2026.
     https://pypi.org/project/mcp/

[14] Anthropic. "MCP Transports Specification." modelcontextprotocol.io, 2025-03-26.
     https://modelcontextprotocol.io/specification/2025-03-26/basic/transports

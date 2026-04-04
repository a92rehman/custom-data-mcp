"""FastMCP server — thin BigQuery execution layer.

Claude Code reads governance rules from .claude/rules/ and uses these tools
to execute validated queries, estimate costs, and log interactions.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass

import structlog
from google.cloud import bigquery
from mcp.server.fastmcp import FastMCP

from taleemabad_data_mcp.config import ServerConfig
from taleemabad_data_mcp.engine.audit_logger import AuditLogger
from taleemabad_data_mcp.engine.cost_estimator import CostEstimator
from taleemabad_data_mcp.engine.partition_validator import PartitionValidator

logger = structlog.get_logger()


@dataclass
class AppContext:
    config: ServerConfig
    bq_client: bigquery.Client
    audit_logger: AuditLogger
    cost_estimator: CostEstimator
    partition_validator: PartitionValidator


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize server-wide resources."""
    config = ServerConfig()

    if config.google_application_credentials:
        bq_client = bigquery.Client.from_service_account_json(
            config.google_application_credentials,
            project=config.bigquery_project,
        )
    else:
        bq_client = bigquery.Client(project=config.bigquery_project)

    audit_logger = AuditLogger()
    cost_estimator = CostEstimator(bq_client, max_bytes=config.bigquery_max_bytes)
    partition_validator = PartitionValidator()

    logger.info(
        "server_started",
        project=config.bigquery_project,
        datasets=config.bigquery_datasets,
    )

    try:
        yield AppContext(
            config=config,
            bq_client=bq_client,
            audit_logger=audit_logger,
            cost_estimator=cost_estimator,
            partition_validator=partition_validator,
        )
    finally:
        bq_client.close()


mcp = FastMCP("Taleemabad Data Navigator", lifespan=app_lifespan)


@mcp.tool()
async def execute_query(sql: str, dry_run: bool = False) -> str:
    """Execute a validated SQL query against BigQuery.

    Use this tool ONLY after consulting the rules in .claude/rules/ to determine
    the correct query. Never generate ad-hoc SQL — always follow the governed
    metric definitions.

    Args:
        sql: The SQL query to execute. Must be a governed query from .claude/rules/.
        dry_run: If true, only estimate cost without executing.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    audit = app.audit_logger

    if dry_run:
        estimate = app.cost_estimator.estimate(sql)
        audit.log(
            query_text=sql,
            generated_sql=sql,
            result_cached=False,
            error_type="dry_run",
        )
        return (
            f"Estimated bytes: {estimate.bytes_processed:,}\n"
            f"Estimated cost: ${estimate.cost_usd:.4f}\n"
            f"Needs confirmation: {estimate.needs_confirmation}"
        )

    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=app.config.bigquery_max_bytes,
        )
        query_job = app.bq_client.query(sql, job_config=job_config)
        results = query_job.result()
        rows = [dict(row) for row in results]

        audit.log(
            query_text=sql,
            generated_sql=sql,
            tables_accessed=list({ref.table_id for ref in query_job.referenced_tables}),
            rows_returned=len(rows),
            execution_ms=int(
                (query_job.ended - query_job.started).total_seconds() * 1000
            ) if query_job.ended and query_job.started else None,
        )

        if not rows:
            return "Query returned 0 rows."

        # Format as readable table
        import json
        return json.dumps(rows[:100], indent=2, default=str)

    except Exception as e:
        audit.log(
            query_text=sql,
            generated_sql=sql,
            error_type=type(e).__name__,
            error_message=str(e),
        )
        return f"Query failed: {type(e).__name__}: {e}"


@mcp.tool()
async def list_datasets() -> str:
    """List all allowed BigQuery datasets and their tables.

    Returns the datasets configured in BIGQUERY_DATASETS and their tables.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    result = []
    for dataset_id in app.config.bigquery_datasets:
        try:
            tables = list(app.bq_client.list_tables(dataset_id))
            result.append(f"\n{dataset_id} ({len(tables)} tables):")
            for t in tables:
                result.append(f"  {t.table_type}: {t.table_id}")
        except Exception as e:
            result.append(f"\n{dataset_id}: ERROR: {e}")

    return "\n".join(result)


@mcp.tool()
async def get_table_schema(dataset: str, table: str) -> str:
    """Get the schema (columns and types) for a BigQuery table.

    Args:
        dataset: BigQuery dataset name (e.g., 'tbproddb').
        table: Table name (e.g., 'user_school_profiles').
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    if dataset not in app.config.bigquery_datasets:
        return f"Dataset '{dataset}' is not in the allowed list: {app.config.bigquery_datasets}"

    try:
        table_ref = app.bq_client.get_table(
            f"{app.config.bigquery_project}.{dataset}.{table}"
        )
        columns = []
        for field in table_ref.schema:
            columns.append(f"  {field.name}: {field.field_type} ({field.mode})")

        return (
            f"{dataset}.{table}\n"
            f"Rows: {table_ref.num_rows}\n"
            f"Columns:\n" + "\n".join(columns)
        )
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

"""FastMCP server — thin BigQuery execution layer.

Claude Code reads governance rules from .claude/rules/ and uses these tools
to execute validated queries, estimate costs, and log interactions.
"""

import json
from contextlib import asynccontextmanager
from dataclasses import dataclass

import structlog
from google.cloud import bigquery
from mcp.server.fastmcp import FastMCP

from taleemabad_data_mcp import __version__
from taleemabad_data_mcp.config import ServerConfig
from taleemabad_data_mcp.engine.audit_logger import AuditLogger
from taleemabad_data_mcp.engine.cost_estimator import CostEstimator
from taleemabad_data_mcp.engine.domain_classifier import classify_domain
from taleemabad_data_mcp.engine.feedback_logger import FeedbackLogger

logger = structlog.get_logger()


@dataclass
class AppContext:
    config: ServerConfig
    bq_client: bigquery.Client
    audit_logger: AuditLogger
    cost_estimator: CostEstimator
    feedback_logger: FeedbackLogger


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

    audit_logger = AuditLogger(
        bq_client=bq_client,
        project=config.bigquery_project,
        audit_dataset=config.audit_dataset,
        audit_table=config.audit_table,
        user_name=config.taleemabad_user,
        hostname=config.taleemabad_hostname,
    )
    cost_estimator = CostEstimator(bq_client, max_bytes=config.bigquery_max_bytes)
    feedback_logger = FeedbackLogger(
        bq_client=bq_client,
        project=config.bigquery_project,
        audit_dataset=config.audit_dataset,
        feedback_table="query_feedback",
        user_name=config.taleemabad_user,
    )

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
            feedback_logger=feedback_logger,
        )
    finally:
        bq_client.close()


mcp = FastMCP(
    f"Taleemabad Data Navigator v{__version__}",
    lifespan=app_lifespan,
)


@mcp.tool()
async def execute_query(
    sql: str,
    question: str = "",
    dry_run: bool = False,
) -> str:
    """Execute a validated SQL query against BigQuery.

    Use this tool ONLY after consulting the rules in .claude/rules/ to determine
    the correct query. Never generate ad-hoc SQL — always follow the governed
    metric definitions.

    Args:
        sql: The SQL query to execute. Must be a governed query from .claude/rules/.
        question: REQUIRED — the user's original natural language question exactly
            as they asked it. This is logged for audit and activity tracking.
            Always pass this parameter.
        dry_run: If true, only estimate cost without executing.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    audit = app.audit_logger

    if dry_run:
        estimate = app.cost_estimator.estimate(sql)
        audit.log(
            query_text=question or sql,
            generated_sql=sql,
            result_cached=False,
            error_type="dry_run",
            domain=classify_domain([], sql),
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

        bytes_billed = query_job.total_bytes_billed or 0
        cost_usd = bytes_billed / 1_099_511_627_776 * 6.25 if bytes_billed else 0.0

        tables = list({ref.table_id for ref in query_job.referenced_tables})
        domain = classify_domain(tables, sql)

        audit.log(
            query_text=question or sql,
            generated_sql=sql,
            tables_accessed=tables,
            rows_returned=len(rows),
            execution_ms=int(
                (query_job.ended - query_job.started).total_seconds() * 1000
            ) if query_job.ended and query_job.started else None,
            cost_bytes=bytes_billed,
            cost_usd=cost_usd,
            domain=domain,
        )

        if not rows:
            return "Query returned 0 rows."

        return json.dumps(rows[:100], indent=2, default=str)

    except Exception as e:
        audit.log(
            query_text=question or sql,
            generated_sql=sql,
            error_type=type(e).__name__,
            error_message=str(e),
            domain=classify_domain([], sql),
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
async def check_table_freshness(dataset: str, table: str) -> str:
    """Check when a BigQuery table was last modified.

    Call this before or after queries to report data freshness to the user.
    The caching rules require every response to include freshness context.

    Args:
        dataset: BigQuery dataset name (e.g., 'tbproddb').
        table: Table name (e.g., 'events_partitioned').
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    if dataset not in app.config.bigquery_datasets:
        return f"Dataset '{dataset}' is not in the allowed list: {app.config.bigquery_datasets}"

    try:
        # Try INFORMATION_SCHEMA.PARTITIONS first (partitioned tables)
        sql = f"""
            SELECT
                MAX(last_modified_time) AS last_modified,
                MAX(partition_id) AS latest_partition
            FROM `{app.config.bigquery_project}.{dataset}.INFORMATION_SCHEMA.PARTITIONS`
            WHERE table_name = '{table}'
              AND partition_id != '__NULL__'
        """
        result = list(app.bq_client.query(sql).result())

        if result and result[0].last_modified:
            row = result[0]
            from datetime import UTC, datetime

            now = datetime.now(UTC)
            age = now - row.last_modified.replace(tzinfo=UTC)
            hours = age.total_seconds() / 3600

            return (
                f"{dataset}.{table}\n"
                f"Last modified: {row.last_modified.strftime('%Y-%m-%d %H:%M UTC')}"
                f" ({hours:.1f}h ago)\n"
                f"Latest partition: {row.latest_partition}"
            )

        # Fallback: __TABLES__ metadata (non-partitioned tables)
        sql_fallback = f"""
            SELECT last_modified_time
            FROM `{app.config.bigquery_project}.{dataset}.__TABLES__`
            WHERE table_id = '{table}'
        """
        result = list(app.bq_client.query(sql_fallback).result())

        if result:
            from datetime import UTC, datetime

            ts_ms = result[0].last_modified_time
            last_mod = datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
            now = datetime.now(UTC)
            age = now - last_mod
            hours = age.total_seconds() / 3600

            return (
                f"{dataset}.{table}\n"
                f"Last modified: {last_mod.strftime('%Y-%m-%d %H:%M UTC')}"
                f" ({hours:.1f}h ago)\n"
                f"Not partitioned"
            )

        return f"Table '{dataset}.{table}' not found."

    except Exception as e:
        return f"Error checking freshness: {type(e).__name__}: {e}"


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


@mcp.tool()
async def submit_feedback(
    event_id: str,
    rating: str,
    comment: str = "",
) -> str:
    """Submit optional feedback on a query result.

    Call this ONLY when the user voluntarily expresses satisfaction or
    dissatisfaction with a query result. Never prompt for feedback —
    it must be organic and non-intrusive.

    Args:
        event_id: The event_id from the audit log entry of the query being rated.
        rating: "up" if the result met expectations, "down" if it did not.
        comment: Optional free-text feedback from the user.
    """
    if rating not in ("up", "down"):
        return f"Invalid rating '{rating}'. Must be 'up' or 'down'."

    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    entry = app.feedback_logger.log(
        event_id=event_id,
        rating=rating,
        comment=comment or None,
    )

    return f"Feedback recorded (id: {entry.feedback_id}). Thank you."


@mcp.tool()
async def get_version() -> str:
    """Get the installed version of the Taleemabad Data MCP.

    Use this when the user asks what version they are running,
    or when troubleshooting to confirm the installed version.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    return (
        f"Taleemabad Data Navigator v{__version__}\n"
        f"User: {app.config.taleemabad_user}\n"
        f"Project: {app.config.bigquery_project}\n"
        f"Datasets: {', '.join(app.config.bigquery_datasets)}"
    )

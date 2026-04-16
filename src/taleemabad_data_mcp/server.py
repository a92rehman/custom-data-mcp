"""FastMCP server — thin BigQuery execution layer.

Claude Code reads governance rules from .claude/rules/ and uses these tools
to execute validated queries, estimate costs, and log interactions.

Supports two modes:
- **Local (stdio):** Used by Claude Code plugin, reads user from env file.
- **Remote (streamable-http):** Deployed on Railway, reads user from HTTP headers.
"""

import json
import os
import re as _re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

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

CREDENTIALS_MISSING_MSG = (
    "BigQuery connection unavailable. "
    "The MCP server could not connect to BigQuery. "
    "If this persists, contact the data team."
)

BANNED_TABLES = {"analytics_analyticsevent"}
_SAFE_FILTER_RE = _re.compile(
    r"^[a-zA-Z_]\w*\s*(>=|<=|>|<|=|!=|BETWEEN)\s*"
    r"(DATE\('[^']+'\)|TIMESTAMP\('[^']+'\)|'[^']*'|\d+)"
    r"(\s+AND\s+[a-zA-Z_]\w*\s*(>=|<=|>|<|=|!=)\s*(DATE\('[^']+'\)|'[^']*'|\d+))*$",
    _re.IGNORECASE,
)
_SAFE_IDENTIFIER_RE = _re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

_ENV_FILE = Path.home() / ".claude" / "taleemabad-data-mcp.env"

ALLOWED_EMAIL_DOMAINS = {"taleemabad.com", "niete.edu.pk", "niete.pk"}


def _is_remote_mode() -> bool:
    """Check if running in remote mode (Railway deployment)."""
    return os.environ.get("TALEEMABAD_REMOTE_MODE", "").lower() in ("1", "true", "yes")


def _read_user_from_env_file() -> str | None:
    """Read TALEEMABAD_USER from saved env file.

    The plugin .mcp.json passes ${TALEEMABAD_USER} but Claude Code does not
    expand arbitrary env vars. This function reads the value directly from
    the env file written by /taleemabad-setup.
    """
    if not _ENV_FILE.exists():
        return None
    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                if key.strip() == "TALEEMABAD_USER" and value.strip():
                    return value.strip()
    except Exception:
        pass
    return None


def _get_request_user_email() -> str | None:
    """Extract user email from HTTP request headers (remote mode only).

    Returns None if not in HTTP context (e.g., stdio transport).
    """
    try:
        from fastmcp.server.dependencies import get_http_headers
        headers = get_http_headers(include={"x-taleemabad-user"})
        return headers.get("x-taleemabad-user")
    except (ImportError, RuntimeError):
        return None


def _validate_email_domain(email: str) -> bool:
    """Validate that email belongs to an allowed domain."""
    if not email or "@" not in email:
        return False
    domain = email.split("@")[1].lower()
    return domain in ALLOWED_EMAIL_DOMAINS


def _validate_bearer_token() -> bool:
    """Validate the Authorization bearer token from HTTP headers.

    Returns True if token matches the server's TALEEMABAD_API_TOKEN,
    or if no token is configured (open access).
    """
    expected_token = os.environ.get("TALEEMABAD_API_TOKEN", "")
    if not expected_token:
        return True  # No token configured = open access

    try:
        from fastmcp.server.dependencies import get_http_headers
        headers = get_http_headers(include={"authorization"})
        auth = headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:] == expected_token
        return False
    except (ImportError, RuntimeError):
        return True  # Not in HTTP context (stdio) = no auth needed


@dataclass
class AppContext:
    config: ServerConfig
    bq_client: bigquery.Client | None
    audit_logger: AuditLogger | None
    cost_estimator: CostEstimator | None
    feedback_logger: FeedbackLogger | None
    remote_mode: bool = False


def _require_bq(app: "AppContext") -> str | None:
    """Return an error message if BigQuery is not available, else None."""
    if app.bq_client is None:
        return CREDENTIALS_MISSING_MSG
    return None


def _require_auth(app: "AppContext") -> str | None:
    """Validate auth in remote mode. Returns error message or None.

    Currently permissive: allows all requests. Email header is optional
    and used only for audit logging when present.
    """
    if not app.remote_mode:
        return None

    # Email header is optional — used for audit enrichment only
    # Treat unexpanded env var placeholders (e.g. "${TALEEMABAD_USER}") as absent
    # Treat non-email values (no @) as absent — MCP clients may send session IDs
    email = _get_request_user_email()
    if email and (email.startswith("${") or email.startswith("${")):
        email = None
    if email and "@" not in email:
        email = None  # Not an email — likely a session ID or username
    if email and not _validate_email_domain(email):
        return f"Unauthorized domain in email '{email}'. Allowed: @taleemabad.com, @niete.edu.pk, @niete.pk"

    return None


def _get_audit_email(app: "AppContext") -> str | None:
    """Get user email for audit logging. Returns email in remote mode, None in local."""
    if app.remote_mode:
        email = _get_request_user_email()
        # Treat unexpanded env var placeholders as absent
        if email and (email.startswith("${") or email.startswith("${")):
            return None
        return email
    return None


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize server-wide resources. Gracefully degrades if credentials missing."""
    config = ServerConfig()
    remote_mode = _is_remote_mode()

    # Override user name from env file if config has unexpanded var or default
    if not remote_mode and config.taleemabad_user in ("unknown", "", "${TALEEMABAD_USER}"):
        env_user = _read_user_from_env_file()
        if env_user:
            config.taleemabad_user = env_user
            logger.info("user_name_loaded", source="env_file", user=env_user)

    bq_client = None
    audit_logger = None
    cost_estimator = None
    feedback_logger = None

    try:
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
            remote_mode=remote_mode,
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
            remote_mode=remote_mode,
        )
    except Exception as e:
        logger.warning(
            "server_started_degraded",
            error=str(e),
            hint="Copy credentials file to project directory",
        )

    try:
        yield AppContext(
            config=config,
            bq_client=bq_client,
            audit_logger=audit_logger,
            cost_estimator=cost_estimator,
            feedback_logger=feedback_logger,
            remote_mode=remote_mode,
        )
    finally:
        if bq_client:
            bq_client.close()


mcp = FastMCP(
    f"Taleemabad Data Navigator v{__version__}",
    lifespan=app_lifespan,
)


# --- Health check endpoint (used by Railway for service monitoring) ---

from starlette.requests import Request
from starlette.responses import JSONResponse


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check for Railway monitoring."""
    return JSONResponse({"status": "ok", "version": __version__})


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
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err
    audit = app.audit_logger
    user_email = _get_audit_email(app)

    if dry_run:
        estimate = app.cost_estimator.estimate(sql)
        audit.log(
            query_text=question or sql,
            generated_sql=sql,
            result_cached=False,
            error_type="dry_run",
            domain=classify_domain([], sql),
            user_email=user_email,
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
            user_email=user_email,
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
            user_email=user_email,
        )
        return f"Query failed: {type(e).__name__}: {e}"


@mcp.tool()
async def list_datasets() -> str:
    """List all BigQuery datasets accessible to the service account and their tables.

    Auto-discovers all datasets accessible to the service account.
    If BIGQUERY_DATASETS is configured, those are listed first for priority ordering.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err

    # Auto-discover all datasets in the project
    try:
        all_datasets = [ds.dataset_id for ds in app.bq_client.list_datasets()]
    except Exception as e:
        return f"Error listing datasets: {e}"

    # Configured datasets first, then any newly discovered ones
    configured = set(app.config.bigquery_datasets)
    ordered = [d for d in all_datasets if d in configured]
    ordered += [d for d in all_datasets if d not in configured]

    result = []
    for dataset_id in ordered:
        tag = " [configured]" if dataset_id in configured else " [discovered]"
        try:
            tables = list(app.bq_client.list_tables(dataset_id))
            result.append(f"\n{dataset_id}{tag} ({len(tables)} tables):")
            for t in tables:
                result.append(f"  {t.table_type}: {t.table_id}")
        except Exception as e:
            result.append(f"\n{dataset_id}{tag}: ERROR: {e}")

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
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err

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
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err

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
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err

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

    # Auto-discover accessible datasets
    datasets_str = ", ".join(app.config.bigquery_datasets) if app.config.bigquery_datasets else ""
    if app.bq_client:
        try:
            discovered = [ds.dataset_id for ds in app.bq_client.list_datasets()]
            datasets_str = ", ".join(discovered)
        except Exception:
            pass  # Fall back to configured list

    return (
        f"Taleemabad Data Navigator v{__version__}\n"
        f"User: {app.config.taleemabad_user}\n"
        f"Project: {app.config.bigquery_project}\n"
        f"Datasets: {datasets_str}"
    )


@mcp.tool()
async def preview_table(
    dataset: str,
    table: str,
    limit: int = 10,
    partition_filter: str = "",
) -> str:
    """Preview rows from a BigQuery table.

    For partitioned tables, provide a partition_filter (e.g., "sent_at >= DATE('2025-01-01')").
    Blocked for banned tables (unpartitioned legacy tables).

    Args:
        dataset: BigQuery dataset name (e.g., 'tbproddb').
        table: Table name (e.g., 'coaching_observation').
        limit: Max rows to return (default 10, max 50).
        partition_filter: Simple WHERE condition for partitioned tables.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err

    if not _SAFE_IDENTIFIER_RE.match(table):
        return f"Invalid table name: '{table}'"

    if table in BANNED_TABLES:
        return (
            f"Table '{table}' is banned (unpartitioned legacy table). "
            "Use a governed query instead."
        )

    limit = min(max(1, limit), 50)

    where = ""
    if partition_filter:
        if not _SAFE_FILTER_RE.match(partition_filter.strip()):
            return (
                "Invalid partition_filter. Use simple comparisons only, e.g.: "
                "sent_at >= DATE('2025-01-01')"
            )
        where = f"WHERE {partition_filter}"

    sql = f"SELECT * FROM `{app.config.bigquery_project}.{dataset}.{table}` {where} LIMIT {limit}"

    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=app.config.bigquery_max_bytes,
        )
        query_job = app.bq_client.query(sql, job_config=job_config)
        rows = [dict(row) for row in query_job.result()]

        if app.audit_logger:
            app.audit_logger.log(
                query_text=f"preview: {dataset}.{table}",
                generated_sql=sql,
                tables_accessed=[table],
                rows_returned=len(rows),
                domain="PREVIEW",
            )

        if not rows:
            return f"No rows found in {dataset}.{table}"

        return json.dumps(rows, indent=2, default=str)

    except Exception as e:
        return f"Preview failed: {type(e).__name__}: {e}"


@mcp.tool()
async def save_query_results(
    sql: str,
    question: str = "",
    format: str = "csv",
    output_dir: str = ".",
) -> str:
    """Execute a governed query and save results to a file.

    In local mode, files are saved to output_dir. In remote mode, file content
    is returned as a string (Railway's filesystem is ephemeral).

    Args:
        sql: The governed SQL query to execute.
        question: The user's original question (for audit logging).
        format: Output format — 'csv' or 'json'. Default 'csv'.
        output_dir: Directory to save the file. Default '.' (project directory).
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err

    if format not in ("csv", "json"):
        return f"Invalid format '{format}'. Must be 'csv' or 'json'."

    user_email = _get_audit_email(app)
    user_display = user_email or app.config.taleemabad_user

    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=app.config.bigquery_max_bytes,
        )
        query_job = app.bq_client.query(sql, job_config=job_config)
        results = query_job.result()
        rows = [dict(row) for row in results]

        if not rows:
            return "Query returned 0 rows. Nothing to save."

        from datetime import UTC, datetime
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M")
        tables = list({ref.table_id for ref in query_job.referenced_tables})
        domain = classify_domain(tables, sql)

        if format == "csv":
            import csv
            import io

            output = io.StringIO()
            output.write(f"# Exported by: {user_display}\n")
            output.write(f"# Timestamp: {timestamp}\n")
            output.write(f"# Domain: {domain}\n")
            output.write(f"# Rows: {len(rows)}\n")

            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow({k: str(v) for k, v in row.items()})

            file_content = output.getvalue()
        else:
            export_data = {
                "metadata": {
                    "exported_by": user_display,
                    "timestamp": timestamp,
                    "domain": domain,
                    "row_count": len(rows),
                },
                "data": rows,
            }
            file_content = json.dumps(export_data, indent=2, default=str)

        bytes_billed = query_job.total_bytes_billed or 0
        cost_usd = bytes_billed / 1_099_511_627_776 * 6.25 if bytes_billed else 0.0

        if app.audit_logger:
            app.audit_logger.log(
                query_text=question or sql,
                generated_sql=sql,
                tables_accessed=tables,
                rows_returned=len(rows),
                cost_bytes=bytes_billed,
                cost_usd=cost_usd,
                domain=f"EXPORT_{domain}",
                user_email=user_email,
            )

        # In remote mode, return content directly (can't write to server filesystem)
        if app.remote_mode:
            filename = f"taleemabad_export_{timestamp}_{domain}.{format}"
            return (
                f"FILE_CONTENT:{filename}\n"
                f"---\n"
                f"{file_content}"
            )

        # Local mode: write to disk
        from pathlib import Path
        out_path = Path(output_dir)
        if not out_path.is_dir():
            return f"Output directory '{output_dir}' does not exist."

        filename = f"taleemabad_export_{timestamp}_{domain}.{format}"
        filepath = out_path / filename
        filepath.write_text(file_content, encoding="utf-8")
        return f"Saved {len(rows)} rows to {filepath} ({format.upper()})"

    except Exception as e:
        return f"Save failed: {type(e).__name__}: {e}"


@mcp.tool()
async def describe_data(
    sql: str,
    question: str = "",
) -> str:
    """Execute a governed query and return descriptive statistics.

    Computes count, mean, min, max, nulls for numeric columns.
    Computes count, unique values, top value for string columns.

    Args:
        sql: The governed SQL query to execute.
        question: The user's original question (for audit logging).
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context
    auth_err = _require_auth(app)
    if auth_err:
        return auth_err
    err = _require_bq(app)
    if err:
        return err

    try:
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=app.config.bigquery_max_bytes,
        )
        query_job = app.bq_client.query(sql, job_config=job_config)
        results = query_job.result()
        rows = [dict(row) for row in results]

        if not rows:
            return "Query returned 0 rows. Nothing to describe."

        tables = list({ref.table_id for ref in query_job.referenced_tables})
        domain = classify_domain(tables, sql)

        stats = {"row_count": len(rows), "columns": {}}
        for col in rows[0]:
            values = [row[col] for row in rows if row[col] is not None]
            null_count = len(rows) - len(values)

            numeric_vals = []
            for v in values:
                try:
                    numeric_vals.append(float(v))
                except (TypeError, ValueError):
                    break

            if len(numeric_vals) == len(values) and numeric_vals:
                sorted_vals = sorted(numeric_vals)
                n = len(sorted_vals)
                if n % 2 == 0:
                    median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
                else:
                    median = sorted_vals[n // 2]
                stats["columns"][col] = {
                    "type": "numeric",
                    "count": n,
                    "nulls": null_count,
                    "mean": round(sum(sorted_vals) / n, 4),
                    "min": sorted_vals[0],
                    "max": sorted_vals[-1],
                    "median": round(median, 4),
                }
            else:
                from collections import Counter
                str_vals = [str(v) for v in values]
                counts = Counter(str_vals)
                top_val, top_count = counts.most_common(1)[0] if counts else ("", 0)
                stats["columns"][col] = {
                    "type": "categorical",
                    "count": len(str_vals),
                    "nulls": null_count,
                    "unique": len(counts),
                    "top_value": top_val,
                    "top_count": top_count,
                }

        if app.audit_logger:
            app.audit_logger.log(
                query_text=question or sql,
                generated_sql=sql,
                tables_accessed=tables,
                rows_returned=len(rows),
                domain=f"DESCRIBE_{domain}",
            )

        return json.dumps(stats, indent=2, default=str)

    except Exception as e:
        return f"Describe failed: {type(e).__name__}: {e}"

# BigQuery Best Practices for Data Governance, Cost Control, and Query Management

## Research Report for Taleemabad Data Governance MCP Server

**Date:** 2026-04-04
**Scope:** Partitioning, clustering, cost control, caching, Python client patterns, data governance, EdTech data patterns

---

## Table of Contents

1. [Partitioning and Clustering](#1-partitioning-and-clustering)
2. [Cost Control and Estimation](#2-cost-control-and-estimation)
3. [Caching Strategies](#3-caching-strategies)
4. [Python Client Patterns](#4-python-client-patterns)
5. [Data Governance Features](#5-data-governance-features)
6. [EdTech Data Patterns](#6-edtech-data-patterns)
7. [MCP Server Design Recommendations](#7-mcp-server-design-recommendations)

---

## 1. Partitioning and Clustering

### 1.1 Partitioning Strategies

BigQuery supports three partitioning strategies. A table can only be partitioned on **one** column.

#### Time-Unit Column Partitioning

Best for tables queried with date/time filters (the most common pattern for EdTech analytics).

```sql
-- Daily partitioning on a DATE column (most common)
CREATE TABLE `project.dataset.student_activity`
(
  student_id STRING,
  activity_date DATE,
  school_id STRING,
  content_id STRING,
  time_spent_seconds INT64,
  score FLOAT64
)
PARTITION BY activity_date
CLUSTER BY school_id, content_id
OPTIONS (
  require_partition_filter = TRUE,
  partition_expiration_days = 730  -- 2 years retention
);

-- Monthly partitioning (good for smaller daily volumes)
CREATE TABLE `project.dataset.monthly_school_metrics`
(
  report_month DATE,
  school_id STRING,
  total_students INT64,
  avg_score FLOAT64
)
PARTITION BY DATE_TRUNC(report_month, MONTH)
OPTIONS (require_partition_filter = TRUE);

-- Hourly partitioning (high-volume real-time data)
CREATE TABLE `project.dataset.realtime_events`
(
  event_timestamp TIMESTAMP,
  event_type STRING,
  user_id STRING
)
PARTITION BY TIMESTAMP_TRUNC(event_timestamp, HOUR);
```

Granularity guidelines:
- **Daily**: Best for wide date ranges with continuous data (e.g., daily student activity -- the typical EdTech case)
- **Hourly**: High-volume data spanning less than six months
- **Monthly/Yearly**: Small daily datasets over extended periods

#### Integer-Range Partitioning

Useful when queries filter on integer IDs rather than dates.

```sql
CREATE TABLE `project.dataset.student_scores`
(
  student_id INT64,
  assessment_id STRING,
  score FLOAT64,
  completed_at TIMESTAMP
)
PARTITION BY RANGE_BUCKET(student_id, GENERATE_ARRAY(0, 1000000, 10000));
```

#### Ingestion-Time Partitioning

Automatically partitions based on when data arrives. Uses pseudocolumns `_PARTITIONTIME` and `_PARTITIONDATE`.

```sql
CREATE TABLE `project.dataset.raw_events`
(
  event_data STRING,
  source STRING
)
PARTITION BY _PARTITIONDATE;

-- Querying with the pseudocolumn
SELECT * FROM `project.dataset.raw_events`
WHERE _PARTITIONDATE = '2026-03-15';
```

### 1.2 Enforcing Partition Filters (Critical for MCP Server)

The `require_partition_filter` option is one of the most important cost-control mechanisms. When enabled, any query without a WHERE clause on the partition column is **rejected before execution**.

```sql
-- Set on table creation
CREATE TABLE `project.dataset.metrics`
(
  metric_date DATE,
  metric_name STRING,
  metric_value FLOAT64
)
PARTITION BY metric_date
OPTIONS (require_partition_filter = TRUE);

-- Update existing table
ALTER TABLE `project.dataset.metrics`
SET OPTIONS (require_partition_filter = TRUE);
```

Error when filter is missing:
```
Cannot query over table 'project.dataset.metrics' without a filter
that can be used for partition elimination.
```

**Python enforcement:**

```python
from google.cloud import bigquery

client = bigquery.Client()

# Update existing table to require partition filter
table = client.get_table("project.dataset.metrics")
table.require_partition_filter = True
client.update_table(table, ["require_partition_filter"])
```

**MCP Server recommendation:** Even if `require_partition_filter` is set on tables, the MCP server should independently validate that incoming queries contain partition filters. This provides a defense-in-depth approach and gives users better error messages.

### 1.3 Clustering Best Practices

Clustering sorts data within partitions by up to 4 columns. Benefits kick in for tables larger than 64 MB.

```sql
-- Optimal: Partition + Cluster combination
CREATE TABLE `project.dataset.student_activity`
(
  activity_date DATE,
  school_id STRING,
  grade_level STRING,
  subject STRING,
  student_id STRING,
  score FLOAT64
)
PARTITION BY activity_date
CLUSTER BY school_id, grade_level, subject;
```

Key rules:
- **Column order matters**: Place the most frequently filtered column first
- **Maximum 4 columns**
- **STRING clustering uses only the first 1,024 characters**
- **Auto-reclustering** happens in the background at no cost
- Supported types: STRING, INT64, FLOAT64, NUMERIC, BOOL, DATE, DATETIME, TIMESTAMP, GEOGRAPHY

**When to use clustering vs. partitioning:**

| Aspect | Partitioning | Clustering |
|--------|-------------|-----------|
| Column count | 1 only | Up to 4 |
| Cost estimation | Exact pre-execution estimate | Post-execution only |
| Cardinality | Low (date ranges) | High (IDs, names) |
| Filter type | Equality, range on partition col | Equality, range, IN on cluster cols |

**For Taleemabad:** Partition by date, cluster by `school_id`, `grade_level`, `subject` -- matching the most common query patterns for educational dashboards.

---

## 2. Cost Control and Estimation

### 2.1 Dry Run / Cost Estimation (Critical MCP Feature)

Dry runs validate SQL and return estimated bytes processed **without executing the query**. They are free.

```python
from google.cloud import bigquery

def estimate_query_cost(
    client: bigquery.Client,
    query: str,
    query_parameters: list = None,
    price_per_tb: float = 6.25  # On-demand pricing per TB as of 2026
) -> dict:
    """
    Estimate query cost using dry run before execution.
    Returns cost estimate and bytes to be processed.
    """
    job_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,  # Ensure we get accurate byte estimate
    )
    if query_parameters:
        job_config.query_parameters = query_parameters

    try:
        query_job = client.query(query, job_config=job_config)

        bytes_processed = query_job.total_bytes_processed
        gb_processed = bytes_processed / (1024 ** 3)
        tb_processed = bytes_processed / (1024 ** 4)
        estimated_cost_usd = tb_processed * price_per_tb

        return {
            "valid": True,
            "bytes_processed": bytes_processed,
            "gb_processed": round(gb_processed, 4),
            "tb_processed": round(tb_processed, 6),
            "estimated_cost_usd": round(estimated_cost_usd, 6),
            "human_readable": f"{gb_processed:.2f} GB (~${estimated_cost_usd:.4f})",
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "bytes_processed": 0,
            "estimated_cost_usd": 0,
        }
```

### 2.2 Maximum Bytes Billed (Query-Level Guard)

Set a hard cap per query. If the estimated bytes exceed this limit, the query **fails before execution** with no charge.

```python
def execute_with_cost_guard(
    client: bigquery.Client,
    query: str,
    max_bytes: int = 1 * 1024**3,  # 1 GB default limit
    query_parameters: list = None,
) -> bigquery.table.RowIterator:
    """
    Execute query with a bytes-billed guard.
    Fails before execution if estimated cost exceeds max_bytes.
    """
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=max_bytes,
    )
    if query_parameters:
        job_config.query_parameters = query_parameters

    query_job = client.query(query, job_config=job_config)
    return query_job.result()  # Raises if bytes exceed limit
```

### 2.3 Cost Control Tiers for MCP Server

Recommended tiered approach:

```python
# Cost control configuration for the MCP server
COST_TIERS = {
    "interactive": {
        "max_bytes_billed": 1 * 1024**3,       # 1 GB
        "max_cost_usd": 0.00625,                 # ~$0.006
        "description": "Dashboard queries, quick lookups"
    },
    "analytical": {
        "max_bytes_billed": 10 * 1024**3,       # 10 GB
        "max_cost_usd": 0.0625,                  # ~$0.06
        "description": "Trend analysis, aggregated reports"
    },
    "heavy": {
        "max_bytes_billed": 100 * 1024**3,      # 100 GB
        "max_cost_usd": 0.625,                   # ~$0.63
        "description": "Full data exports, cross-table joins"
    },
    "admin": {
        "max_bytes_billed": 1024 * 1024**3,     # 1 TB
        "max_cost_usd": 6.25,                    # ~$6.25
        "description": "Admin-only heavy operations"
    },
}

def get_cost_tier(user_role: str) -> dict:
    """Map user role to cost tier."""
    role_mapping = {
        "viewer": "interactive",
        "analyst": "analytical",
        "data_engineer": "heavy",
        "admin": "admin",
    }
    tier_name = role_mapping.get(user_role, "interactive")
    return COST_TIERS[tier_name]
```

### 2.4 INFORMATION_SCHEMA for Cost Monitoring

```sql
-- Query cost by user over the last 7 days
SELECT
  user_email,
  COUNT(*) AS query_count,
  SUM(total_bytes_processed) AS total_bytes,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 6.25, 2) AS estimated_cost_usd,
  AVG(total_slot_ms) AS avg_slot_ms
FROM `region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
GROUP BY user_email
ORDER BY total_bytes DESC;

-- Most expensive queries in the last 24 hours
SELECT
  job_id,
  user_email,
  query,
  total_bytes_processed,
  ROUND(total_bytes_processed / POW(1024, 4) * 6.25, 4) AS estimated_cost_usd,
  total_slot_ms,
  creation_time
FROM `region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
ORDER BY total_bytes_processed DESC
LIMIT 20;

-- Daily cost trend
SELECT
  DATE(creation_time) AS query_date,
  COUNT(*) AS query_count,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 6.25, 2) AS daily_cost_usd
FROM `region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
GROUP BY query_date
ORDER BY query_date DESC;
```

### 2.5 Important Cost Facts

- **Minimum billing per table reference**: 10 MiB regardless of actual table size
- **LIMIT clause does NOT reduce bytes scanned** on non-clustered tables
- **Long-term storage discount**: Tables unmodified for 90 days get 50% storage price reduction
- **Cached results**: Free (no bytes billed)
- **Dry runs**: Free
- **Row-level security note**: Queries on RLS-protected tables do not produce `total_bytes_billed` in INFORMATION_SCHEMA.JOBS, which can affect cost tracking accuracy

---

## 3. Caching Strategies

### 3.1 BigQuery Built-in Cache

BigQuery automatically caches query results in temporary tables for approximately **24 hours**. Cached results are free (no bytes billed).

**Cache invalidation triggers:**
1. Any DML operation (INSERT, UPDATE, DELETE, MERGE) on referenced tables
2. Streaming inserts to referenced tables
3. Table data changes of any kind
4. Cache expiry (~24 hours)
5. Non-deterministic functions: `CURRENT_TIMESTAMP()`, `CURRENT_DATE()`, `SESSION_USER()`, `RAND()`, etc.
6. Wildcard table queries
7. External data sources (non-Cloud Storage)
8. Row/column-level security on referenced tables
9. Any change to query text, including whitespace or comments
10. Destination table specified in job config

**Check if a result was cached:**
```python
query_job = client.query(query)
results = query_job.result()

if query_job.cache_hit:
    print("Result served from cache (free)")
else:
    print(f"Bytes billed: {query_job.total_bytes_billed}")
```

### 3.2 Controlling Cache Behavior

```python
# Force fresh results (bypass cache)
job_config = bigquery.QueryJobConfig(use_query_cache=False)
query_job = client.query(query, job_config=job_config)

# Require cached results only (fail if not cached)
job_config = bigquery.QueryJobConfig(
    create_disposition=bigquery.CreateDisposition.CREATE_NEVER
)
```

### 3.3 Application-Level Caching for the MCP Server

Since the MCP server sits between users and BigQuery, implement a multi-tier cache:

```python
import hashlib
import json
import time
from typing import Optional, Any
from dataclasses import dataclass, field

@dataclass
class CachedResult:
    """Represents a cached BigQuery query result."""
    query_hash: str
    results: list[dict]
    timestamp: float
    bytes_processed: int
    row_count: int
    schema: list[dict]
    ttl_seconds: int = 3600  # Default 1 hour

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl_seconds


class QueryCache:
    """
    Application-level query cache for the MCP server.

    Cache tiers:
    - L1: In-memory dict (fastest, limited size)
    - L2: Optional Redis/file-based (larger, persistent)
    - L3: BigQuery's built-in cache (automatic)
    """

    def __init__(self, max_memory_entries: int = 100):
        self._memory_cache: dict[str, CachedResult] = {}
        self._max_entries = max_memory_entries
        # Track which tables are referenced by each cached query
        self._table_dependencies: dict[str, set[str]] = {}

    @staticmethod
    def _compute_hash(query: str, parameters: Optional[list] = None) -> str:
        """Deterministic hash of query + parameters."""
        normalized = " ".join(query.split()).strip().lower()
        param_str = json.dumps(parameters, sort_keys=True, default=str) if parameters else ""
        content = f"{normalized}|{param_str}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, query: str, parameters: Optional[list] = None) -> Optional[CachedResult]:
        """Retrieve cached result if available and not expired."""
        key = self._compute_hash(query, parameters)
        cached = self._memory_cache.get(key)
        if cached and not cached.is_expired:
            return cached
        if cached and cached.is_expired:
            del self._memory_cache[key]
        return None

    def put(
        self,
        query: str,
        results: list[dict],
        bytes_processed: int,
        schema: list[dict],
        parameters: Optional[list] = None,
        ttl_seconds: int = 3600,
        referenced_tables: Optional[set[str]] = None,
    ) -> None:
        """Store query result in cache."""
        key = self._compute_hash(query, parameters)

        # Evict oldest if at capacity
        if len(self._memory_cache) >= self._max_entries:
            oldest_key = min(self._memory_cache, key=lambda k: self._memory_cache[k].timestamp)
            del self._memory_cache[oldest_key]

        self._memory_cache[key] = CachedResult(
            query_hash=key,
            results=results,
            timestamp=time.time(),
            bytes_processed=bytes_processed,
            row_count=len(results),
            schema=schema,
            ttl_seconds=ttl_seconds,
        )

        if referenced_tables:
            self._table_dependencies[key] = referenced_tables

    def invalidate_table(self, table_id: str) -> int:
        """Invalidate all cached queries that reference a specific table."""
        keys_to_remove = [
            key for key, tables in self._table_dependencies.items()
            if table_id in tables
        ]
        for key in keys_to_remove:
            self._memory_cache.pop(key, None)
            self._table_dependencies.pop(key, None)
        return len(keys_to_remove)

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        self._memory_cache.clear()
        self._table_dependencies.clear()

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        valid = sum(1 for c in self._memory_cache.values() if not c.is_expired)
        return {
            "total_entries": len(self._memory_cache),
            "valid_entries": valid,
            "expired_entries": len(self._memory_cache) - valid,
            "bytes_saved": sum(c.bytes_processed for c in self._memory_cache.values() if not c.is_expired),
        }
```

### 3.4 TTL Strategy by Query Type

```python
# TTL configuration based on data freshness requirements
CACHE_TTL_CONFIG = {
    # Static/reference data: cache for a long time
    "school_metadata": 86400,       # 24 hours
    "curriculum_structure": 86400,  # 24 hours
    "grade_definitions": 86400,     # 24 hours

    # Daily aggregated metrics: cache until next daily refresh
    "daily_kpis": 3600,             # 1 hour
    "daily_completion_rates": 3600, # 1 hour

    # Near-real-time data: short cache
    "active_sessions": 60,          # 1 minute
    "live_quiz_results": 120,       # 2 minutes

    # Default for unclassified queries
    "default": 1800,                # 30 minutes
}
```

### 3.5 Materialized Views vs. Application Cache

| Aspect | Materialized View | Application Cache |
|--------|-------------------|-------------------|
| Refresh | Auto (BigQuery managed) | Manual / TTL-based |
| Cost | Storage + refresh compute | Application memory/Redis |
| Freshness | Always current (reads delta) | Potentially stale |
| Best for | Complex aggregations reused across users | Identical repeated queries |
| Staleness control | `max_staleness` option | TTL per query type |

```sql
-- Materialized view for daily school KPIs (auto-refreshed)
CREATE MATERIALIZED VIEW `project.dataset.mv_daily_school_kpis`
OPTIONS (
  enable_refresh = TRUE,
  refresh_interval_minutes = 60,
  max_staleness = INTERVAL "4:0:0" HOUR TO SECOND
)
AS
SELECT
  activity_date,
  school_id,
  COUNT(DISTINCT student_id) AS active_students,
  AVG(score) AS avg_score,
  SUM(time_spent_seconds) AS total_time_seconds,
  COUNT(*) AS total_activities
FROM `project.dataset.student_activity`
WHERE activity_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY activity_date, school_id;
```

---

## 4. Python Client Patterns

### 4.1 Parameterized Queries (SQL Injection Prevention)

**This is mandatory for any MCP server accepting user-provided values.**

```python
from google.cloud import bigquery

def query_school_metrics(
    client: bigquery.Client,
    school_id: str,
    start_date: str,
    end_date: str,
    min_score: float = 0.0,
) -> list[dict]:
    """
    Query school metrics with parameterized inputs.
    Parameters cannot substitute table/column names -- only data values.
    """
    query = """
        SELECT
            activity_date,
            COUNT(DISTINCT student_id) AS active_students,
            AVG(score) AS avg_score,
            SUM(time_spent_seconds) / 3600.0 AS total_hours
        FROM `project.dataset.student_activity`
        WHERE activity_date BETWEEN @start_date AND @end_date
          AND school_id = @school_id
          AND score >= @min_score
        GROUP BY activity_date
        ORDER BY activity_date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("school_id", "STRING", school_id),
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            bigquery.ScalarQueryParameter("min_score", "FLOAT64", min_score),
        ]
    )

    results = client.query_and_wait(query, job_config=job_config)
    return [dict(row) for row in results]


def query_with_array_param(
    client: bigquery.Client,
    school_ids: list[str],
    activity_date: str,
) -> list[dict]:
    """Query with ARRAY parameter for IN-clause filtering."""
    query = """
        SELECT school_id, COUNT(*) AS activity_count
        FROM `project.dataset.student_activity`
        WHERE activity_date = @activity_date
          AND school_id IN UNNEST(@school_ids)
        GROUP BY school_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("activity_date", "DATE", activity_date),
            bigquery.ArrayQueryParameter("school_ids", "STRING", school_ids),
        ]
    )

    results = client.query_and_wait(query, job_config=job_config)
    return [dict(row) for row in results]
```

**Critical limitation:** Parameters can only substitute **data values**, not identifiers (table names, column names, dataset names). The MCP server must use an allowlist approach for any dynamic table/column references.

### 4.2 Async Query Execution

The Python client's `client.query()` returns a `QueryJob` immediately (non-blocking). The blocking happens at `.result()`.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.cloud import bigquery

# Thread pool for running blocking BQ calls in async context
_executor = ThreadPoolExecutor(max_workers=4)


async def async_query(
    client: bigquery.Client,
    query: str,
    job_config: bigquery.QueryJobConfig = None,
) -> list[dict]:
    """
    Run a BigQuery query asynchronously using a thread pool.
    The google-cloud-bigquery library does not natively support asyncio,
    so we wrap the blocking call in an executor.
    """
    loop = asyncio.get_event_loop()

    def _run():
        query_job = client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]

    return await loop.run_in_executor(_executor, _run)


async def run_parallel_queries(client: bigquery.Client) -> dict:
    """Run multiple independent queries in parallel."""
    queries = {
        "active_students": "SELECT COUNT(DISTINCT student_id) AS cnt FROM `project.dataset.student_activity` WHERE activity_date = CURRENT_DATE()",
        "avg_score": "SELECT AVG(score) AS avg FROM `project.dataset.student_activity` WHERE activity_date = CURRENT_DATE()",
        "total_schools": "SELECT COUNT(DISTINCT school_id) AS cnt FROM `project.dataset.student_activity` WHERE activity_date = CURRENT_DATE()",
    }

    tasks = {
        name: async_query(client, sql)
        for name, sql in queries.items()
    }

    results = await asyncio.gather(*tasks.values())
    return dict(zip(tasks.keys(), results))
```

### 4.3 Result Pagination and Streaming

```python
def query_with_pagination(
    client: bigquery.Client,
    query: str,
    page_size: int = 1000,
) -> list[dict]:
    """
    Fetch results with explicit page size.
    BigQuery handles pagination internally via the RowIterator.
    """
    query_job = client.query(query)
    results = query_job.result(page_size=page_size)

    all_rows = []
    for page in results.pages:
        for row in page:
            all_rows.append(dict(row))
    return all_rows


def stream_large_results(
    client: bigquery.Client,
    query: str,
    max_rows: int = None,
) -> list[dict]:
    """
    Stream results row by row for large result sets.
    Avoids loading entire result into memory.
    """
    query_job = client.query(query)
    rows = query_job.result()

    output = []
    for i, row in enumerate(rows):
        if max_rows and i >= max_rows:
            break
        output.append(dict(row))
    return output
```

### 4.4 Error Handling Patterns

```python
from google.cloud import bigquery
from google.api_core import exceptions as api_exceptions
import logging

logger = logging.getLogger(__name__)


class BigQueryError:
    """Structured error response for the MCP server."""
    def __init__(self, error_type: str, message: str, details: dict = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error": True,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
        }


def safe_query(
    client: bigquery.Client,
    query: str,
    job_config: bigquery.QueryJobConfig = None,
    timeout: float = 60.0,
) -> dict:
    """
    Execute query with comprehensive error handling.
    Returns structured response suitable for MCP tool output.
    """
    try:
        query_job = client.query(query, job_config=job_config, timeout=timeout)
        results = query_job.result(timeout=timeout)
        rows = [dict(row) for row in results]

        return {
            "error": False,
            "data": rows,
            "row_count": len(rows),
            "bytes_processed": query_job.total_bytes_processed,
            "bytes_billed": query_job.total_bytes_billed,
            "cache_hit": query_job.cache_hit,
            "job_id": query_job.job_id,
        }

    except api_exceptions.BadRequest as e:
        # SQL syntax errors, invalid references, missing partition filters
        logger.warning(f"Bad request: {e.message}")
        return BigQueryError(
            "BAD_REQUEST",
            f"Query validation failed: {e.message}",
            {"errors": [err for err in e.errors] if hasattr(e, 'errors') else []},
        ).to_dict()

    except api_exceptions.Forbidden as e:
        # Permission denied, quota exceeded, bytes billed limit exceeded
        logger.warning(f"Forbidden: {e.message}")
        return BigQueryError(
            "FORBIDDEN",
            f"Access denied or quota exceeded: {e.message}",
        ).to_dict()

    except api_exceptions.NotFound as e:
        # Table/dataset not found
        logger.warning(f"Not found: {e.message}")
        return BigQueryError(
            "NOT_FOUND",
            f"Resource not found: {e.message}",
        ).to_dict()

    except api_exceptions.TooManyRequests as e:
        # Rate limiting
        logger.warning(f"Rate limited: {e.message}")
        return BigQueryError(
            "RATE_LIMITED",
            "Too many requests. Please retry after a moment.",
        ).to_dict()

    except TimeoutError:
        logger.error("Query timed out")
        return BigQueryError(
            "TIMEOUT",
            f"Query exceeded timeout of {timeout}s. Consider narrowing your date range or filters.",
        ).to_dict()

    except Exception as e:
        logger.exception("Unexpected error during query execution")
        return BigQueryError(
            "INTERNAL_ERROR",
            "An unexpected error occurred. Please contact support.",
            {"exception_type": type(e).__name__},
        ).to_dict()
```

### 4.5 Client Initialization Best Practices

```python
from google.cloud import bigquery
from google.oauth2 import service_account
import os


def create_client(
    project_id: str = None,
    credentials_path: str = None,
) -> bigquery.Client:
    """
    Create BigQuery client with proper configuration.
    Supports both service account (production) and ADC (development).
    """
    if credentials_path:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
        )
        return bigquery.Client(project=project_id, credentials=credentials)

    # Fall back to Application Default Credentials
    return bigquery.Client(project=project_id)


# Singleton pattern for MCP server (reuse client across requests)
_client: bigquery.Client = None

def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = create_client(
            project_id=os.environ.get("GCP_PROJECT_ID"),
            credentials_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        )
    return _client
```

---

## 5. Data Governance Features

### 5.1 Column-Level Security

Restrict access to sensitive columns (e.g., student PII) using **policy tags** and **Data Catalog taxonomies**.

**Implementation steps:**
1. Create a taxonomy in Data Catalog
2. Define policy tags (e.g., `PII`, `SENSITIVE`, `PUBLIC`)
3. Apply tags to table columns
4. Grant `Fine-Grained Reader` role to authorized users
5. Enforce access control through data policies

```python
from google.cloud import datacatalog_v1

def create_taxonomy_and_tags(
    project_id: str,
    location: str = "us",
) -> dict:
    """Create a data classification taxonomy for EdTech data."""
    client = datacatalog_v1.PolicyTagManagerClient()

    # Create taxonomy
    taxonomy = client.create_taxonomy(
        parent=f"projects/{project_id}/locations/{location}",
        taxonomy=datacatalog_v1.Taxonomy(
            display_name="Taleemabad Data Classification",
            description="Data sensitivity classification for EdTech platform",
            activated_policy_types=[
                datacatalog_v1.Taxonomy.PolicyType.FINE_GRAINED_ACCESS_CONTROL
            ],
        ),
    )

    # Create policy tags
    tags = {}
    for tag_name in ["PII", "SENSITIVE", "INTERNAL", "PUBLIC"]:
        tag = client.create_policy_tag(
            parent=taxonomy.name,
            policy_tag=datacatalog_v1.PolicyTag(
                display_name=tag_name,
                description=f"{tag_name} classification level",
            ),
        )
        tags[tag_name] = tag.name

    return tags
```

Users without `Fine-Grained Reader` get an error listing inaccessible columns. They can use `SELECT * EXCEPT(restricted_column)` to work around it.

### 5.2 Row-Level Security

Restrict which rows a user can see using `ROW ACCESS POLICY`.

```sql
-- Restrict school admins to only see their own school's data
CREATE ROW ACCESS POLICY school_admin_filter
ON `project.dataset.student_activity`
GRANT TO ('group:school_123_admins@taleemabad.com')
FILTER USING (school_id = 'school_123');

-- Dynamic policy using SESSION_USER()
-- Requires a mapping table of user -> school
CREATE ROW ACCESS POLICY dynamic_school_filter
ON `project.dataset.student_activity`
GRANT TO ('allAuthenticatedUsers')
FILTER USING (
  school_id IN (
    SELECT school_id
    FROM `project.dataset.user_school_mapping`
    WHERE user_email = SESSION_USER()
  )
);

-- District-level access (users see all schools in their district)
CREATE ROW ACCESS POLICY district_filter
ON `project.dataset.student_activity`
GRANT TO ('group:district_A_users@taleemabad.com')
FILTER USING (
  school_id IN (
    SELECT school_id
    FROM `project.dataset.school_directory`
    WHERE district_id = 'district_A'
  )
);
```

**Important:** Row-level security affects cost tracking -- `total_bytes_billed` is not reported in INFORMATION_SCHEMA.JOBS for RLS-protected tables.

### 5.3 Authorized Views and Authorized Datasets

Authorized views expose a subset of data without granting access to the underlying tables.

```sql
-- Authorized view that masks PII
CREATE VIEW `project.reporting_dataset.student_summary` AS
SELECT
  -- Hash the student ID for anonymization
  SHA256(student_id) AS anonymized_student_id,
  school_id,
  grade_level,
  subject,
  activity_date,
  score,
  time_spent_seconds
FROM `project.raw_dataset.student_activity`;
```

Then authorize the view:
```python
from google.cloud import bigquery

client = bigquery.Client()

# Grant the view access to the source dataset
source_dataset = client.get_dataset("project.raw_dataset")
access_entries = list(source_dataset.access_entries)
access_entries.append(
    bigquery.AccessEntry(
        role=None,  # No role needed for authorized views
        entity_type="view",
        entity_id={
            "projectId": "project",
            "datasetId": "reporting_dataset",
            "tableId": "student_summary",
        },
    )
)
source_dataset.access_entries = access_entries
client.update_dataset(source_dataset, ["access_entries"])
```

**Authorized datasets** are more scalable: authorize an entire dataset so all views within it get access automatically.

### 5.4 Audit Logging

BigQuery generates three types of audit logs:

| Log Type | Content | Enabled by Default |
|----------|---------|-------------------|
| Admin Activity | Schema changes, permission updates | Yes (cannot disable) |
| Data Access | Queries, data reads, metadata reads | **No** (must enable) |
| System Event | Automatic operations (e.g., table expiration) | Yes |

**Enable Data Access logs** (critical for governance):
```python
# Via gcloud CLI
# gcloud projects get-iam-policy PROJECT_ID > policy.yaml
# Add BigQuery Data Access audit config, then set the policy

# Query audit logs from INFORMATION_SCHEMA
AUDIT_QUERY = """
SELECT
  user_email,
  job_id,
  query,
  total_bytes_processed,
  creation_time,
  state,
  error_result
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY creation_time DESC
LIMIT 100;
"""
```

### 5.5 INFORMATION_SCHEMA Governance Queries

```sql
-- List all tables with their row counts and sizes
SELECT
  table_schema AS dataset,
  table_name,
  row_count,
  ROUND(size_bytes / POW(1024, 3), 2) AS size_gb,
  creation_time,
  TIMESTAMP_MILLIS(last_modified_time) AS last_modified
FROM `project`.`region-us`.INFORMATION_SCHEMA.TABLE_STORAGE
ORDER BY size_bytes DESC;

-- List all columns across datasets (data dictionary)
SELECT
  table_catalog AS project,
  table_schema AS dataset,
  table_name,
  column_name,
  data_type,
  is_nullable
FROM `project`.`region-us`.INFORMATION_SCHEMA.COLUMNS
WHERE table_schema NOT LIKE '_%'
ORDER BY table_schema, table_name, ordinal_position;

-- Find tables without partition filters enforced
SELECT
  table_schema AS dataset,
  table_name,
  ddl
FROM `project`.`region-us`.INFORMATION_SCHEMA.TABLES
WHERE ddl LIKE '%PARTITION BY%'
  AND ddl NOT LIKE '%require_partition_filter%true%';

-- Query job statistics for governance reporting
SELECT
  user_email,
  DATE(creation_time) AS query_date,
  COUNT(*) AS queries_run,
  COUNTIF(cache_hit) AS cache_hits,
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2) AS total_gb_processed,
  ROUND(AVG(total_slot_ms) / 1000, 2) AS avg_slot_seconds
FROM `region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
GROUP BY user_email, query_date
ORDER BY total_gb_processed DESC;
```

---

## 6. EdTech Data Patterns

### 6.1 Table Design for Taleemabad

```sql
-- Core fact table: student activity (partitioned + clustered)
CREATE TABLE `project.taleemabad.student_activity`
(
  activity_date DATE NOT NULL,
  student_id STRING NOT NULL,
  school_id STRING NOT NULL,
  grade_level STRING,
  subject STRING,
  content_id STRING,
  content_type STRING,           -- 'lesson', 'quiz', 'game', 'video'
  time_spent_seconds INT64,
  score FLOAT64,                 -- Normalized 0-100
  completion_status STRING,      -- 'started', 'in_progress', 'completed'
  attempt_number INT64,
  device_type STRING,
  session_id STRING,
  created_at TIMESTAMP
)
PARTITION BY activity_date
CLUSTER BY school_id, grade_level, subject
OPTIONS (
  require_partition_filter = TRUE,
  partition_expiration_days = 1095,  -- 3 years
  description = 'Core student activity events, one row per content interaction'
);

-- Dimension table: school directory
CREATE TABLE `project.taleemabad.dim_schools`
(
  school_id STRING NOT NULL,
  school_name STRING,
  district_id STRING,
  district_name STRING,
  province STRING,
  school_type STRING,           -- 'public', 'private', 'partner'
  total_enrolled_students INT64,
  subscription_tier STRING,
  onboarding_date DATE,
  is_active BOOL
)
CLUSTER BY district_id, province;

-- Pre-aggregated daily KPIs (for dashboard performance)
CREATE TABLE `project.taleemabad.daily_school_kpis`
(
  kpi_date DATE NOT NULL,
  school_id STRING NOT NULL,
  grade_level STRING,
  subject STRING,
  active_students INT64,
  total_sessions INT64,
  total_time_hours FLOAT64,
  avg_score FLOAT64,
  completion_rate FLOAT64,
  content_items_completed INT64,
  assessments_taken INT64,
  avg_attempts_per_assessment FLOAT64
)
PARTITION BY kpi_date
CLUSTER BY school_id, grade_level
OPTIONS (
  require_partition_filter = TRUE,
  description = 'Pre-aggregated daily KPIs per school/grade/subject'
);

-- Trend reporting table (monthly rollups for Power BI)
CREATE TABLE `project.taleemabad.monthly_trends`
(
  report_month DATE NOT NULL,     -- First day of month
  school_id STRING NOT NULL,
  district_id STRING,
  grade_level STRING,
  subject STRING,
  metric_name STRING NOT NULL,    -- 'active_students', 'avg_score', etc.
  metric_value FLOAT64,
  previous_month_value FLOAT64,
  month_over_month_change FLOAT64
)
PARTITION BY report_month
CLUSTER BY district_id, school_id, metric_name
OPTIONS (require_partition_filter = TRUE);
```

### 6.2 Common EdTech Aggregation Queries

```sql
-- Daily active students with trend (window function)
SELECT
  activity_date,
  COUNT(DISTINCT student_id) AS dau,
  AVG(COUNT(DISTINCT student_id)) OVER (
    ORDER BY activity_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS dau_7d_avg,
  AVG(COUNT(DISTINCT student_id)) OVER (
    ORDER BY activity_date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) AS dau_30d_avg
FROM `project.taleemabad.student_activity`
WHERE activity_date BETWEEN @start_date AND @end_date
GROUP BY activity_date
ORDER BY activity_date;

-- Content effectiveness analysis
SELECT
  content_id,
  content_type,
  subject,
  COUNT(DISTINCT student_id) AS unique_students,
  AVG(score) AS avg_score,
  STDDEV(score) AS score_stddev,
  AVG(time_spent_seconds) AS avg_time_seconds,
  COUNTIF(completion_status = 'completed') / COUNT(*) AS completion_rate,
  AVG(attempt_number) AS avg_attempts
FROM `project.taleemabad.student_activity`
WHERE activity_date BETWEEN @start_date AND @end_date
  AND school_id = @school_id
GROUP BY content_id, content_type, subject
HAVING unique_students >= 10  -- Statistical significance filter
ORDER BY avg_score ASC;  -- Show struggling content first

-- School comparison dashboard query
SELECT
  s.school_name,
  s.district_name,
  k.kpi_date,
  k.active_students,
  k.avg_score,
  k.completion_rate,
  k.total_time_hours,
  -- Percentile rank within district
  PERCENT_RANK() OVER (
    PARTITION BY s.district_id, k.kpi_date
    ORDER BY k.avg_score
  ) AS score_percentile
FROM `project.taleemabad.daily_school_kpis` k
JOIN `project.taleemabad.dim_schools` s USING (school_id)
WHERE k.kpi_date BETWEEN @start_date AND @end_date
  AND s.district_id = @district_id
ORDER BY k.kpi_date, k.avg_score DESC;

-- Time bucket aggregation for engagement patterns
SELECT
  TIMESTAMP_BUCKET(created_at, INTERVAL 1 HOUR) AS hour_bucket,
  COUNT(*) AS event_count,
  COUNT(DISTINCT student_id) AS unique_students,
  AVG(time_spent_seconds) AS avg_engagement_seconds
FROM `project.taleemabad.student_activity`
WHERE activity_date = @target_date
  AND school_id = @school_id
GROUP BY hour_bucket
ORDER BY hour_bucket;
```

### 6.3 ETL Pattern for Daily KPI Aggregation

```sql
-- Daily scheduled query to populate KPIs (can be run via Cloud Scheduler)
MERGE `project.taleemabad.daily_school_kpis` AS target
USING (
  SELECT
    activity_date AS kpi_date,
    school_id,
    grade_level,
    subject,
    COUNT(DISTINCT student_id) AS active_students,
    COUNT(DISTINCT session_id) AS total_sessions,
    ROUND(SUM(time_spent_seconds) / 3600.0, 2) AS total_time_hours,
    ROUND(AVG(score), 2) AS avg_score,
    ROUND(COUNTIF(completion_status = 'completed') / COUNT(*), 4) AS completion_rate,
    COUNTIF(completion_status = 'completed') AS content_items_completed,
    COUNTIF(content_type = 'quiz') AS assessments_taken,
    ROUND(AVG(IF(content_type = 'quiz', attempt_number, NULL)), 2) AS avg_attempts_per_assessment
  FROM `project.taleemabad.student_activity`
  WHERE activity_date = @target_date
  GROUP BY activity_date, school_id, grade_level, subject
) AS source
ON target.kpi_date = source.kpi_date
  AND target.school_id = source.school_id
  AND target.grade_level = source.grade_level
  AND target.subject = source.subject
WHEN MATCHED THEN
  UPDATE SET
    active_students = source.active_students,
    total_sessions = source.total_sessions,
    total_time_hours = source.total_time_hours,
    avg_score = source.avg_score,
    completion_rate = source.completion_rate,
    content_items_completed = source.content_items_completed,
    assessments_taken = source.assessments_taken,
    avg_attempts_per_assessment = source.avg_attempts_per_assessment
WHEN NOT MATCHED THEN
  INSERT ROW;
```

### 6.4 Power BI Integration Considerations

- **Use pre-aggregated tables** (`daily_school_kpis`, `monthly_trends`) for Power BI DirectQuery mode to minimize bytes scanned
- **Partition by date, cluster by dimensions** that appear in Power BI slicers (school, grade, subject)
- **Materialized views** work well as Power BI data sources since they auto-refresh
- **`max_staleness`** on materialized views prevents Power BI refresh storms from hitting base tables repeatedly
- **Export mode**: For very large dashboards, consider BigQuery BI Engine or scheduled exports to a reporting dataset

---

## 7. MCP Server Design Recommendations

### 7.1 Query Execution Pipeline

The MCP server should implement this pipeline for every query:

```
User Query
    |
    v
[1. SQL Parsing & Validation]
    - Parse SQL to identify tables, columns, operations
    - Reject DDL/DML if user role doesn't permit
    - Verify all referenced tables are in allowlist
    |
    v
[2. Partition Filter Check]
    - Verify WHERE clause includes partition column filter
    - Reject queries without partition filters on partitioned tables
    - Provide helpful error: "Please add a date filter"
    |
    v
[3. Parameterization]
    - Replace user-provided values with @parameters
    - Build QueryJobConfig with typed parameters
    |
    v
[4. Cache Check]
    - Hash query + parameters
    - Return cached result if valid
    |
    v
[5. Dry Run / Cost Estimation]
    - Run dry_run=True
    - Compare estimated bytes to user's cost tier limit
    - Reject if over budget with explanation
    |
    v
[6. Execute with Guards]
    - Set maximum_bytes_billed
    - Set query timeout
    - Execute query
    |
    v
[7. Result Processing]
    - Format results
    - Store in application cache
    - Log to audit trail
    - Return to user
```

### 7.2 Core MCP Server Class

```python
from google.cloud import bigquery
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryRequest:
    """Incoming query request from MCP tool call."""
    query: str
    parameters: dict = None
    user_role: str = "viewer"
    max_rows: int = 10000
    bypass_cache: bool = False


@dataclass
class QueryResponse:
    """Structured response from the query pipeline."""
    success: bool
    data: list[dict] = None
    row_count: int = 0
    bytes_processed: int = 0
    estimated_cost_usd: float = 0.0
    cache_hit: bool = False
    job_id: str = None
    error_message: str = None
    error_type: str = None


class BigQueryGovernor:
    """
    Central governance layer between MCP tools and BigQuery.
    Enforces cost controls, caching, and access policies.
    """

    def __init__(
        self,
        client: bigquery.Client,
        cache: "QueryCache",
        allowed_datasets: set[str],
        cost_tiers: dict,
    ):
        self.client = client
        self.cache = cache
        self.allowed_datasets = allowed_datasets
        self.cost_tiers = cost_tiers

    def execute(self, request: QueryRequest) -> QueryResponse:
        """Full governed query execution pipeline."""

        # Step 1: Check cache
        if not request.bypass_cache:
            cached = self.cache.get(request.query, request.parameters)
            if cached:
                logger.info(f"Cache hit, saved {cached.bytes_processed} bytes")
                return QueryResponse(
                    success=True,
                    data=cached.results,
                    row_count=cached.row_count,
                    bytes_processed=0,
                    cache_hit=True,
                )

        # Step 2: Dry run cost estimate
        tier = self.cost_tiers.get(request.user_role, self.cost_tiers["viewer"])
        estimate = self._dry_run(request.query, request.parameters)

        if not estimate["valid"]:
            return QueryResponse(
                success=False,
                error_message=estimate["error"],
                error_type="VALIDATION_ERROR",
            )

        if estimate["bytes_processed"] > tier["max_bytes_billed"]:
            return QueryResponse(
                success=False,
                error_message=(
                    f"Query would process {estimate['human_readable']}, "
                    f"exceeding your limit of {tier['max_bytes_billed'] / 1024**3:.1f} GB. "
                    f"Try narrowing your date range or adding more filters."
                ),
                error_type="COST_LIMIT_EXCEEDED",
                bytes_processed=estimate["bytes_processed"],
                estimated_cost_usd=estimate["estimated_cost_usd"],
            )

        # Step 3: Execute with guards
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=tier["max_bytes_billed"],
        )
        if request.parameters:
            job_config.query_parameters = self._build_params(request.parameters)

        try:
            query_job = self.client.query(request.query, job_config=job_config)
            rows = [dict(row) for row in query_job.result(max_results=request.max_rows)]

            # Step 4: Cache results
            self.cache.put(
                query=request.query,
                results=rows,
                bytes_processed=query_job.total_bytes_processed or 0,
                schema=[],
                parameters=request.parameters,
            )

            return QueryResponse(
                success=True,
                data=rows,
                row_count=len(rows),
                bytes_processed=query_job.total_bytes_processed or 0,
                estimated_cost_usd=estimate["estimated_cost_usd"],
                cache_hit=query_job.cache_hit or False,
                job_id=query_job.job_id,
            )

        except Exception as e:
            logger.exception("Query execution failed")
            return QueryResponse(
                success=False,
                error_message=str(e),
                error_type=type(e).__name__,
            )

    def _dry_run(self, query: str, parameters: dict = None) -> dict:
        """Run dry-run cost estimation."""
        job_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
        )
        if parameters:
            job_config.query_parameters = self._build_params(parameters)

        try:
            job = self.client.query(query, job_config=job_config)
            bytes_processed = job.total_bytes_processed
            tb = bytes_processed / (1024 ** 4)
            cost = tb * 6.25
            return {
                "valid": True,
                "bytes_processed": bytes_processed,
                "estimated_cost_usd": round(cost, 6),
                "human_readable": f"{bytes_processed / 1024**3:.2f} GB (~${cost:.4f})",
            }
        except Exception as e:
            return {"valid": False, "error": str(e), "bytes_processed": 0}

    @staticmethod
    def _build_params(params: dict) -> list:
        """Convert dict of parameters to BigQuery query parameters."""
        bq_params = []
        type_map = {
            str: "STRING",
            int: "INT64",
            float: "FLOAT64",
            bool: "BOOL",
        }
        for name, value in params.items():
            if isinstance(value, list):
                element_type = type_map.get(type(value[0]), "STRING") if value else "STRING"
                bq_params.append(bigquery.ArrayQueryParameter(name, element_type, value))
            else:
                bq_type = type_map.get(type(value), "STRING")
                bq_params.append(bigquery.ScalarQueryParameter(name, bq_type, value))
        return bq_params
```

### 7.3 Configuration Summary

```python
# Recommended MCP server configuration
MCP_CONFIG = {
    # Cost control
    "default_max_bytes_billed": 1 * 1024**3,  # 1 GB
    "admin_max_bytes_billed": 100 * 1024**3,   # 100 GB
    "price_per_tb_usd": 6.25,

    # Caching
    "cache_max_entries": 200,
    "cache_default_ttl_seconds": 1800,  # 30 min
    "cache_static_ttl_seconds": 86400,  # 24 hr for reference data

    # Query limits
    "max_result_rows": 50000,
    "query_timeout_seconds": 120,

    # Governance
    "require_partition_filter": True,
    "allowed_datasets": [
        "taleemabad.student_activity",
        "taleemabad.daily_school_kpis",
        "taleemabad.monthly_trends",
        "taleemabad.dim_schools",
    ],
    "blocked_operations": ["DROP", "TRUNCATE", "CREATE", "ALTER", "GRANT"],

    # Audit
    "log_all_queries": True,
    "log_destination": "project.audit.mcp_query_log",
}
```

---

## Sources

### Official Google Cloud Documentation
- [1] Google Cloud. "Introduction to partitioned tables." BigQuery Documentation. https://cloud.google.com/bigquery/docs/partitioned-tables
- [2] Google Cloud. "Estimate and control costs." BigQuery Documentation. https://cloud.google.com/bigquery/docs/best-practices-costs
- [3] Google Cloud. "Using cached query results." BigQuery Documentation. https://cloud.google.com/bigquery/docs/cached-results
- [4] Google Cloud. "Run a parameterized query." BigQuery Documentation. https://cloud.google.com/bigquery/docs/parameterized-queries
- [5] Google Cloud. "Introduction to clustered tables." BigQuery Documentation. https://cloud.google.com/bigquery/docs/clustered-tables
- [6] Google Cloud. "Column-level security." BigQuery Documentation. https://cloud.google.com/bigquery/docs/column-level-security
- [7] Google Cloud. "Introduction to row-level security." BigQuery Documentation. https://cloud.google.com/bigquery/docs/row-level-security-intro
- [8] Google Cloud. "INFORMATION_SCHEMA overview." BigQuery Documentation. https://cloud.google.com/bigquery/docs/information-schema-intro
- [9] Google Cloud. "Authorized views." BigQuery Documentation. https://cloud.google.com/bigquery/docs/authorized-views
- [10] Google Cloud. "Authorized datasets." BigQuery Documentation. https://cloud.google.com/bigquery/docs/authorized-datasets
- [11] Google Cloud. "BigQuery audit logs overview." BigQuery Documentation. https://cloud.google.com/bigquery/docs/reference/auditlogs
- [12] Google Cloud. "Best practices for Cloud Audit Logs." Cloud Logging Documentation. https://cloud.google.com/logging/docs/audit/best-practices
- [13] Google Cloud. "Update require partition filter." BigQuery Samples. https://cloud.google.com/bigquery/docs/samples/bigquery-update-table-require-partition-filter
- [14] Google Cloud. "Introduction to materialized views." BigQuery Documentation. https://cloud.google.com/bigquery/docs/materialized-views-intro
- [15] Google Cloud. "Use materialized views." BigQuery Best Practices. https://cloud.google.com/bigquery/docs/materialized-views-best-practices
- [16] Google Cloud. "Dry run query sample." BigQuery Documentation. https://cloud.google.com/bigquery/docs/samples/bigquery-query-dry-run
- [17] Google Cloud. "Managing row-level security." BigQuery Documentation. https://cloud.google.com/bigquery/docs/managing-row-level-security
- [18] Google Cloud. "Work with time series data." BigQuery Documentation. https://cloud.google.com/bigquery/docs/working-with-time-series
- [19] Google Cloud. "Client class reference." Python Client Libraries. https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.client.Client

### Community Resources
- [20] Medium/Google Cloud Community. "Error Handling BigQuery Python client." https://medium.com/google-cloud/better-error-handling-with-bigquery-python-client-1343582c7a1c
- [21] Medium. "BigQuery Materialized Views vs Caching Layers." Feb 2026. https://medium.com/@hadiyolworld007/bigquery-materialized-views-vs-caching-layers-what-wins-on-cost-when-traffic-becomes-spiky-1afb16bc7b7f
- [22] OneUpTime. "How to Require Partition Filters on BigQuery Tables." Feb 2026. https://oneuptime.com/blog/post/2026-02-17-how-to-require-partition-filters-on-bigquery-tables-to-prevent-full-table-scans/view
- [23] OneUpTime. "How to Estimate BigQuery Query Costs Before Running with Dry Run." Feb 2026. https://oneuptime.com/blog/post/2026-02-17-how-to-estimate-bigquery-query-costs-before-running-with-dry-run/view
- [24] Google Cloud Blog. "BigQuery Admin reference guide: Data governance." https://cloud.google.com/blog/topics/developers-practitioners/bigquery-admin-reference-guide-data-governance

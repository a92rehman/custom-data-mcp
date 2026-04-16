"""All BigQuery SQL queries used by the dashboard."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.data.client import get_bq_client, get_config


def _full_table(table_key: str) -> str:
    """Build fully qualified table name."""
    cfg = get_config()
    table_name = cfg.get(table_key, table_key)
    return f"`{cfg['project']}.{cfg['audit_dataset']}.{table_name}`"


@st.cache_data(ttl=600)
def get_activity_log(
    days: int = 30,
    users: list[str] | None = None,
    domains: list[str] | None = None,
) -> pd.DataFrame:
    """Fetch audit log entries for the given time window."""
    client = get_bq_client()
    table = _full_table("audit_table")

    where = [f"timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)"]
    if users:
        user_list = ", ".join(f"'{u}'" for u in users)
        where.append(f"user_name IN ({user_list})")
    if domains:
        domain_list = ", ".join(f"'{d}'" for d in domains)
        where.append(f"IFNULL(domain, 'other') IN ({domain_list})")

    sql = f"""
        SELECT
            event_id, timestamp, user_name, query_text, generated_sql,
            tables_accessed, rows_returned, execution_ms,
            cost_bytes, cost_usd, result_cached,
            error_type, error_message, IFNULL(domain, 'other') AS domain
        FROM {table}
        WHERE {' AND '.join(where)}
        ORDER BY timestamp DESC
    """
    return client.query(sql).to_dataframe()


@st.cache_data(ttl=600)
def get_feedback(days: int = 30) -> pd.DataFrame:
    """Fetch feedback entries for the given time window."""
    client = get_bq_client()
    table = _full_table("feedback_table")
    audit_table = _full_table("audit_table")

    sql = f"""
        SELECT
            f.feedback_id, f.event_id, f.user_name, f.rating, f.comment, f.timestamp,
            a.query_text, a.generated_sql, IFNULL(a.domain, 'other') AS domain
        FROM {table} f
        LEFT JOIN {audit_table} a ON f.event_id = a.event_id
        WHERE f.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY f.timestamp DESC
    """
    return client.query(sql).to_dataframe()


@st.cache_data(ttl=600)
def get_distinct_users(days: int = 90) -> list[str]:
    """Get distinct user names from recent activity."""
    client = get_bq_client()
    table = _full_table("audit_table")
    sql = f"""
        SELECT DISTINCT user_name
        FROM {table}
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY user_name
    """
    df = client.query(sql).to_dataframe()
    return df["user_name"].tolist() if not df.empty else []


@st.cache_data(ttl=600)
def get_distinct_domains(days: int = 90) -> list[str]:
    """Get distinct domains from recent activity."""
    client = get_bq_client()
    table = _full_table("audit_table")
    sql = f"""
        SELECT DISTINCT IFNULL(domain, 'other') AS domain
        FROM {table}
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY domain
    """
    df = client.query(sql).to_dataframe()
    return df["domain"].tolist() if not df.empty else []


@st.cache_data(ttl=600)
def get_table_freshness(days: int = 30) -> pd.DataFrame:
    """Get freshness for tables that users have actually queried.

    Dynamically reads tables_accessed from the audit log, then checks
    INFORMATION_SCHEMA for each dataset. Falls back to a hardcoded list
    if the audit log has no data.
    """
    client = get_bq_client()
    cfg = get_config()
    audit_table = _full_table("audit_table")

    # Step 1: Get all tables users have actually queried from the audit log
    tables_sql = f"""
        SELECT DISTINCT table_name
        FROM {audit_table},
        UNNEST(tables_accessed) AS table_name
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND table_name IS NOT NULL
          AND table_name != ''
    """
    try:
        tables_df = client.query(tables_sql).to_dataframe()
        queried_tables = tables_df["table_name"].tolist() if not tables_df.empty else []
    except Exception:
        queried_tables = []

    # Fall back to hardcoded key tables if audit log is empty
    if not queried_tables:
        queried_tables = [
            "user_school_profiles", "events_partitioned", "coaching_observation",
            "teacher_training_level", "teacher_training_assessment",
            "lp_info_all_types", "FDE_Schools",
        ]

    table_list = ", ".join(f"'{t}'" for t in queried_tables)

    # Step 2: Check freshness across all configured datasets
    datasets_to_check = ["tbproddb", "RUMI_DB", "TaleemHub_DB", "Muawin_Akhuwat_db", "Zavia_db"]
    all_results = []

    for dataset in datasets_to_check:
        sql = f"""
            SELECT
                '{dataset}' AS dataset,
                table_name,
                MAX(last_modified_time) AS last_modified
            FROM `{cfg['project']}.{dataset}.INFORMATION_SCHEMA.PARTITIONS`
            WHERE table_name IN ({table_list})
              AND partition_id != '__NULL__'
            GROUP BY table_name
        """
        try:
            df = client.query(sql).to_dataframe()
            if not df.empty:
                all_results.append(df)
        except Exception:
            pass  # Dataset may not exist or no permission

    # Also check __TABLES__ for unpartitioned tables
    for dataset in datasets_to_check:
        sql = f"""
            SELECT
                '{dataset}' AS dataset,
                table_id AS table_name,
                TIMESTAMP_MILLIS(last_modified_time) AS last_modified
            FROM `{cfg['project']}.{dataset}.__TABLES__`
            WHERE table_id IN ({table_list})
        """
        try:
            df = client.query(sql).to_dataframe()
            if not df.empty:
                all_results.append(df)
        except Exception:
            pass

    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        # Keep the most recent entry per table (partitioned or unpartitioned)
        return combined.sort_values("last_modified", ascending=False).drop_duplicates(
            subset=["table_name"], keep="first"
        ).reset_index(drop=True)

    return pd.DataFrame(columns=["dataset", "table_name", "last_modified"])


@st.cache_data(ttl=600)
def get_dataset_freshness() -> pd.DataFrame:
    """Get dataset-level freshness: earliest and latest table modification per dataset.

    Returns DataFrame with columns:
        dataset, table_count, oldest_table, oldest_modified, newest_table, newest_modified
    """
    client = get_bq_client()
    cfg = get_config()
    project = cfg["project"]
    datasets_to_check = ["tbproddb", "RUMI_DB", "TaleemHub_DB", "Muawin_Akhuwat_db", "Zavia_db"]
    all_results = []

    for dataset in datasets_to_check:
        sql = f"""
            SELECT
                '{dataset}' AS dataset,
                COUNT(*) AS table_count,
                MIN(TIMESTAMP_MILLIS(last_modified_time)) AS oldest_modified,
                MAX(TIMESTAMP_MILLIS(last_modified_time)) AS newest_modified,
                MIN(TIMESTAMP_MILLIS(creation_time)) AS earliest_created
            FROM `{project}.{dataset}.__TABLES__`
        """
        try:
            df = client.query(sql).to_dataframe()
            if not df.empty:
                all_results.append(df)
        except Exception:
            pass

    if all_results:
        return pd.concat(all_results, ignore_index=True)

    return pd.DataFrame(columns=[
        "dataset", "table_count", "oldest_modified", "newest_modified", "earliest_created",
    ])

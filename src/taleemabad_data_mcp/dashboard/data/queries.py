"""All BigQuery SQL queries used by the dashboard."""

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.data.client import get_bq_client, get_config


def _full_table(table_key: str) -> str:
    """Build fully qualified table name."""
    cfg = get_config()
    table_name = cfg[table_key] if table_key in cfg else table_key
    return f"`{cfg['project']}.{cfg['audit_dataset']}.{table_name}`"


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
def get_table_freshness() -> pd.DataFrame:
    """Get freshness for key tables from INFORMATION_SCHEMA."""
    client = get_bq_client()
    cfg = get_config()

    key_tables = [
        "user_school_profiles", "events_partitioned", "coaching_observation",
        "teacher_training_level", "teacher_training_assessment",
        "lp_info_all_types", "FDE_Schools",
    ]
    table_list = ", ".join(f"'{t}'" for t in key_tables)

    sql = f"""
        SELECT
            table_name,
            MAX(last_modified_time) AS last_modified
        FROM `{cfg['project']}.tbproddb.INFORMATION_SCHEMA.PARTITIONS`
        WHERE table_name IN ({table_list})
          AND partition_id != '__NULL__'
        GROUP BY table_name
    """
    return client.query(sql).to_dataframe()

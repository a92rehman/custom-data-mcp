"""Project registry and dataset statistics for the dashboard."""

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from taleemabad_data_mcp.dashboard.data.client import get_bq_client, get_config
from taleemabad_data_mcp.engine.governance_mapper import get_governance_map

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECTS_YAML = Path(__file__).parent.parent.parent / "projects.yaml"
_RULES_DIR = Path(__file__).parent.parent.parent / "rules"


# ---------------------------------------------------------------------------
# Project registry
# ---------------------------------------------------------------------------


@st.cache_data(ttl=600)
def load_projects() -> list[dict]:
    """Load the project registry from projects.yaml.

    Returns a list of project dicts, each with keys:
    name, dataset, status, region, description.
    Returns an empty list if the file cannot be read.
    """
    try:
        with open(_PROJECTS_YAML, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("projects", []) if data else []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# BigQuery dataset statistics
# ---------------------------------------------------------------------------


@st.cache_data(ttl=600)
def get_dataset_stats(datasets: list[str]) -> dict[str, dict]:
    """Query BigQuery __TABLES__ for table_count and total_rows per dataset.

    Args:
        datasets: List of BigQuery dataset names to inspect.

    Returns:
        Mapping of dataset_name → {"table_count": int, "total_rows": int}.
        Datasets that fail (no permission, not found) are omitted.
    """
    client = get_bq_client()
    cfg = get_config()
    project = cfg["project"]
    result: dict[str, dict] = {}

    for dataset in datasets:
        sql = f"""
            SELECT
                COUNT(*) AS table_count,
                SUM(row_count) AS total_rows
            FROM `{project}.{dataset}.__TABLES__`
        """
        try:
            df = client.query(sql).to_dataframe()
            if not df.empty:
                row = df.iloc[0]
                result[dataset] = {
                    "table_count": int(row["table_count"] or 0),
                    "total_rows": int(row["total_rows"] or 0),
                }
        except Exception:
            pass  # Dataset inaccessible or does not exist

    return result


@st.cache_data(ttl=600)
def get_all_tables(datasets: list[str]) -> pd.DataFrame:
    """Get all tables across the given datasets with metadata.

    Args:
        datasets: List of BigQuery dataset names to inspect.

    Returns:
        DataFrame with columns: dataset, table_name, row_count, last_modified.
        Returns an empty DataFrame if no data can be retrieved.
    """
    client = get_bq_client()
    cfg = get_config()
    project = cfg["project"]
    frames: list[pd.DataFrame] = []

    for dataset in datasets:
        sql = f"""
            SELECT
                '{dataset}' AS dataset,
                table_id AS table_name,
                row_count,
                TIMESTAMP_MILLIS(last_modified_time) AS last_modified
            FROM `{project}.{dataset}.__TABLES__`
            ORDER BY table_id
        """
        try:
            df = client.query(sql).to_dataframe()
            if not df.empty:
                frames.append(df)
        except Exception:
            pass

    if frames:
        return pd.concat(frames, ignore_index=True)

    return pd.DataFrame(columns=["dataset", "table_name", "row_count", "last_modified"])


# ---------------------------------------------------------------------------
# Governance coverage
# ---------------------------------------------------------------------------


@st.cache_data(ttl=600)
def get_governance_coverage() -> dict:
    """Return the governance map from all rule files, cached 1 hour.

    Returns:
        Mapping of (dataset, table) → {"domain", "region", "rule_files"}.
    """
    return get_governance_map()


# ---------------------------------------------------------------------------
# Rule file counting
# ---------------------------------------------------------------------------


def count_rule_files(region: str | None) -> int:
    """Count .md files in the rules directory for the given region.

    Args:
        region: Region subdirectory name (e.g. "ict-islamabad", "rawalpindi"),
                or None to count all .md files under the rules root.

    Returns:
        Number of .md files found. Returns 0 if the path does not exist.
    """
    if region is not None:
        target = _RULES_DIR / region
    else:
        target = _RULES_DIR

    if not target.exists():
        return 0

    return len(list(target.rglob("*.md")))


# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------


def format_rows(n: int) -> str:
    """Format a row count as a human-readable string.

    Examples:
        123       → "123"
        1_234     → "1.2K"
        1_234_567 → "1.2M"

    Args:
        n: Non-negative integer row count.

    Returns:
        Formatted string.
    """
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)

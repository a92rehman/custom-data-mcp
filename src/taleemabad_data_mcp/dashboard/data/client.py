"""BigQuery client for the dashboard."""

import base64
import os
import tempfile

import streamlit as st
from google.cloud import bigquery


@st.cache_resource
def get_bq_client() -> bigquery.Client:
    """Create a BigQuery client, cached for the Streamlit session.

    Supports two credential modes:
    - GOOGLE_APPLICATION_CREDENTIALS_BASE64: base64-encoded JSON key (Railway)
    - GOOGLE_APPLICATION_CREDENTIALS: path to JSON key file (local dev)
    """
    project = os.environ.get("BIGQUERY_PROJECT", "niete-bq-prod")

    b64_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
    if b64_creds:
        creds_json = base64.b64decode(b64_creds).decode("utf-8")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(creds_json)
            temp_path = f.name
        return bigquery.Client.from_service_account_json(temp_path, project=project)

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        return bigquery.Client.from_service_account_json(creds_path, project=project)

    env_file = os.path.expanduser("~/.claude/taleemabad-data-mcp.env")
    if os.path.exists(env_file):
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    env_vars[k] = v
        creds = env_vars.get("GOOGLE_APPLICATION_CREDENTIALS")
        if creds:
            return bigquery.Client.from_service_account_json(creds, project=project)

    return bigquery.Client(project=project)


def get_config() -> dict:
    """Get dashboard configuration from environment."""
    return {
        "project": os.environ.get("BIGQUERY_PROJECT", "niete-bq-prod"),
        "audit_dataset": os.environ.get("AUDIT_DATASET", "mcp_audit"),
        "audit_table": os.environ.get("AUDIT_TABLE", "activity_log"),
        "feedback_table": os.environ.get("FEEDBACK_TABLE", "query_feedback"),
    }

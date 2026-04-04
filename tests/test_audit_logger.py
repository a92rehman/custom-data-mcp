"""Tests for audit logging."""

from taleemabad_data_mcp.engine.audit_logger import AuditLogger


def test_log_creates_entry():
    logger = AuditLogger()
    entry = logger.log(
        query_text="What is LP adoption?",
        matched_metric="lp_adoption_rate_weekly",
        generated_sql="SELECT ...",
        tables_accessed=["fact_lesson_plan_usage"],
    )
    assert entry.event_id is not None
    assert entry.timestamp is not None
    assert entry.query_text == "What is LP adoption?"
    assert entry.matched_metric == "lp_adoption_rate_weekly"


def test_log_stores_entries():
    logger = AuditLogger()
    logger.log(query_text="query 1")
    logger.log(query_text="query 2")
    assert len(logger.entries) == 2


def test_log_with_error():
    logger = AuditLogger()
    entry = logger.log(
        query_text="bad query",
        error_type="NoMatchingMetric",
        error_message="No metric found for 'bad query'",
    )
    assert entry.error_type == "NoMatchingMetric"

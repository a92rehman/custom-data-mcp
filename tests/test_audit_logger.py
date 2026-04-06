"""Tests for audit logging."""

from taleemabad_data_mcp.engine.audit_logger import AuditLogger


def test_log_creates_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_FILE",
        tmp_path / "activity.jsonl",
    )
    logger = AuditLogger(user_name="test-user", hostname="test-host")
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
    assert entry.user_name == "test-user"
    assert entry.hostname == "test-host"


def test_log_writes_local_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_DIR", tmp_path
    )
    log_file = tmp_path / "activity.jsonl"
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_FILE", log_file
    )
    logger = AuditLogger()
    logger.log(query_text="query 1")
    logger.log(query_text="query 2")
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 2


def test_log_with_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_FILE",
        tmp_path / "activity.jsonl",
    )
    logger = AuditLogger()
    entry = logger.log(
        query_text="bad query",
        error_type="NoMatchingMetric",
        error_message="No metric found for 'bad query'",
    )
    assert entry.error_type == "NoMatchingMetric"


def test_log_with_cost(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.audit_logger._LOCAL_LOG_FILE",
        tmp_path / "activity.jsonl",
    )
    logger = AuditLogger()
    entry = logger.log(
        query_text="SELECT * FROM t",
        cost_bytes=1_000_000,
        cost_usd=0.0057,
    )
    assert entry.cost_bytes == 1_000_000
    assert entry.cost_usd == 0.0057

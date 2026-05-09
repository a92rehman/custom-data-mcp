"""Tests for feedback logging."""

from custom_data_mcp.engine.feedback_logger import FeedbackLogger


def test_log_feedback_creates_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "custom_data_mcp.engine.feedback_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "custom_data_mcp.engine.feedback_logger._LOCAL_LOG_FILE",
        tmp_path / "feedback.jsonl",
    )
    fb_logger = FeedbackLogger(user_name="test-user")
    entry = fb_logger.log(event_id="evt-123", rating="up")
    assert entry.feedback_id is not None
    assert entry.event_id == "evt-123"
    assert entry.rating == "up"
    assert entry.user_name == "test-user"


def test_log_feedback_with_comment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "custom_data_mcp.engine.feedback_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "custom_data_mcp.engine.feedback_logger._LOCAL_LOG_FILE",
        tmp_path / "feedback.jsonl",
    )
    fb_logger = FeedbackLogger(user_name="test-user")
    entry = fb_logger.log(event_id="evt-456", rating="down", comment="Wrong number")
    assert entry.comment == "Wrong number"
    assert entry.rating == "down"


def test_log_feedback_writes_local_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "custom_data_mcp.engine.feedback_logger._LOCAL_LOG_DIR", tmp_path
    )
    log_file = tmp_path / "feedback.jsonl"
    monkeypatch.setattr(
        "custom_data_mcp.engine.feedback_logger._LOCAL_LOG_FILE", log_file
    )
    fb_logger = FeedbackLogger()
    fb_logger.log(event_id="evt-1", rating="up")
    fb_logger.log(event_id="evt-2", rating="down", comment="bad data")
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 2

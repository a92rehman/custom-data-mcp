"""Tests for ticket logger — JSONL persistence and BQ fallback."""

from unittest.mock import MagicMock

from taleemabad_data_mcp.engine.ticket_logger import TicketLogger


def test_open_ticket_writes_local(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    ticket_file = tmp_path / "tickets.jsonl"
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE", ticket_file
    )

    tl = TicketLogger(hostname="test-host")
    ticket = tl.open_ticket(
        loop="query",
        category="syntax",
        symptom="bad_sql",
        evidence={"sql": "SELECT oops"},
    )

    assert ticket.ticket_id.startswith("TKT-")
    assert ticket.status == "open"
    assert ticket_file.exists()
    lines = ticket_file.read_text().strip().split("\n")
    assert len(lines) == 1


def test_update_ticket(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE",
        tmp_path / "tickets.jsonl",
    )

    tl = TicketLogger()
    ticket = tl.open_ticket(loop="query", category="schema", symptom="col_missing")
    updated = tl.update_ticket(
        ticket.ticket_id,
        action={"action": "tried_fix", "result": "failed", "timestamp": "now"},
        diagnosis="Column was renamed",
        status="diagnosing",
    )

    assert updated is not None
    assert updated.status == "diagnosing"
    assert len(updated.actions_attempted) == 1
    assert updated.diagnosis == "Column was renamed"


def test_close_ticket(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE",
        tmp_path / "tickets.jsonl",
    )

    tl = TicketLogger()
    ticket = tl.open_ticket(loop="system", category="connection", symptom="mcp_down")
    closed = tl.close_ticket(
        ticket.ticket_id,
        status="auto_fixed",
        resolution_notes="Retried and succeeded",
    )

    assert closed is not None
    assert closed.status == "auto_fixed"
    assert closed.resolution_notes == "Retried and succeeded"


def test_update_nonexistent_ticket(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE",
        tmp_path / "tickets.jsonl",
    )

    tl = TicketLogger()
    result = tl.update_ticket("TKT-00000000-000000", action={"a": "b"})
    assert result is None


def test_read_local_tickets_filtered(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE",
        tmp_path / "tickets.jsonl",
    )

    tl = TicketLogger()
    tl.open_ticket(loop="query", category="syntax", symptom="s1")
    tl.open_ticket(loop="system", category="connection", symptom="s2")

    all_tickets = tl.read_local_tickets()
    assert len(all_tickets) == 2

    query_only = tl.read_local_tickets(category="syntax")
    assert len(query_only) == 1
    assert query_only[0].symptom == "s1"


def test_bq_write_failure_does_not_raise(tmp_path, monkeypatch):
    """BigQuery write failures must not propagate."""
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE",
        tmp_path / "tickets.jsonl",
    )

    mock_bq = MagicMock()
    mock_bq.insert_rows_json.side_effect = Exception("BQ down")
    mock_bq.get_dataset.side_effect = Exception("BQ down")

    tl = TicketLogger(
        bq_client=mock_bq,
        project="test-project",
        audit_dataset="mcp_audit",
    )

    # Should not raise despite BQ failure
    ticket = tl.open_ticket(loop="query", category="other", symptom="test")
    assert ticket.ticket_id.startswith("TKT-")


def test_close_nonexistent_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE",
        tmp_path / "tickets.jsonl",
    )

    tl = TicketLogger()
    result = tl.close_ticket("TKT-00000000-000000", status="abandoned")
    assert result is None

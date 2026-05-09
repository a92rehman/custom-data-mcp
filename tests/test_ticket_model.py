"""Tests for ticket model."""

from custom_data_mcp.models.ticket import Ticket, _make_ticket_id


def test_ticket_id_format():
    tid = _make_ticket_id()
    assert tid.startswith("TKT-")
    parts = tid.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 6  # hex


def test_ticket_defaults():
    t = Ticket(loop="query", category="syntax", symptom="bad_sql")
    assert t.status == "open"
    assert t.severity == "warning"
    assert t.actions_attempted == []
    assert t.evidence == {}
    assert t.ticket_id.startswith("TKT-")


def test_ticket_roundtrip():
    t = Ticket(
        loop="system",
        category="connection",
        symptom="connection_failed",
        severity="error",
        evidence={"url": "https://example.com", "status_code": 503},
    )
    json_str = t.model_dump_json()
    t2 = Ticket.model_validate_json(json_str)
    assert t2.ticket_id == t.ticket_id
    assert t2.evidence == t.evidence
    assert t2.loop == "system"

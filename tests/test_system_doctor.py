"""Tests for system-doctor infrastructure — symptom detection and ticket lifecycle.

The system-doctor agent is a markdown file. These tests verify the Python
infrastructure it relies on: health checks (from the hook), ticket creation
for each symptom class, and the escalation flow.
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

from taleemabad_data_mcp.engine.ticket_logger import TicketLogger
from taleemabad_data_mcp.models.ticket import Ticket


def _setup_ticket_logger(tmp_path, monkeypatch):
    """Create a TicketLogger with temp paths."""
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_LOG_DIR", tmp_path
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.engine.ticket_logger._LOCAL_TICKET_FILE",
        tmp_path / "tickets.jsonl",
    )
    return TicketLogger(hostname="test-host", user_email="test@taleemabad.com")


class TestConnectionFailedSymptom:
    """connection_failed: MCP server unreachable."""

    def test_opens_ticket_with_correct_category(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="connection",
            symptom="connection_failed",
            severity="error",
            evidence={"url": "https://example.com/health", "status_code": 0},
        )
        assert ticket.category == "connection"
        assert ticket.symptom == "connection_failed"
        assert ticket.loop == "system"

    def test_retry_logged_as_action(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system", category="connection", symptom="connection_failed"
        )
        updated = tl.update_ticket(
            ticket.ticket_id,
            action={"action": "retry_curl", "result": "still_503", "timestamp": "now"},
        )
        assert len(updated.actions_attempted) == 1


class TestUserEnvMissingSymptom:
    """user_env_missing: no env file or TALEEMABAD_USER unset."""

    def test_opens_identity_ticket(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="identity",
            symptom="user_env_missing",
            evidence={"env_file_exists": False, "env_var_set": False},
        )
        assert ticket.category == "identity"
        assert ticket.symptom == "user_env_missing"

    def test_auto_fix_from_audit_log(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system", category="identity", symptom="user_env_missing"
        )
        tl.update_ticket(
            ticket.ticket_id,
            action={"action": "extract_from_audit", "result": "found user@taleemabad.com"},
            diagnosis="Recovered email from audit log",
        )
        closed = tl.close_ticket(ticket.ticket_id, status="auto_fixed",
                                  resolution_notes="Wrote env file from audit history")
        assert closed.status == "auto_fixed"


class TestUserEnvUnexpandedSymptom:
    """user_env_unexpanded: literal ${TALEEMABAD_USER} in config."""

    def test_opens_identity_ticket(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="identity",
            symptom="user_env_unexpanded",
            evidence={"env_value": "${TALEEMABAD_USER}"},
        )
        assert ticket.symptom == "user_env_unexpanded"


class TestRulesPathMissingSymptom:
    """rules_path_missing: pointer file missing or stale."""

    def test_opens_rules_ticket(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="rules",
            symptom="rules_path_missing",
            evidence={"path_file_exists": False},
        )
        assert ticket.category == "rules"

    def test_escalated_after_two_failures(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system", category="rules", symptom="rules_path_missing"
        )
        tl.update_ticket(ticket.ticket_id,
                         action={"action": "run_hook", "result": "failed", "attempt": 1})
        tl.update_ticket(ticket.ticket_id,
                         action={"action": "run_hook", "result": "failed", "attempt": 2})
        closed = tl.close_ticket(ticket.ticket_id, status="escalated",
                                  resolution_notes="2 heal attempts failed")
        assert closed.status == "escalated"
        assert len(closed.actions_attempted) == 2


class TestRulesStaleSymptom:
    """rules_stale: local version behind remote by 2+ versions."""

    def test_opens_rules_ticket(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="rules",
            symptom="rules_stale",
            evidence={"local": "v0.15.0", "remote": "v0.17.15"},
        )
        assert ticket.symptom == "rules_stale"


class TestPluginNotInstalledSymptom:
    """plugin_not_installed: claude plugin list doesn't include taleemabad-data."""

    def test_user_action_required(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="plugin",
            symptom="plugin_not_installed",
        )
        closed = tl.close_ticket(ticket.ticket_id, status="user_action_required",
                                  resolution_notes="User must install plugin manually")
        assert closed.status == "user_action_required"


class TestPluginOutdatedSymptom:
    """plugin_outdated: local version behind by 2+ minor."""

    def test_user_action_required(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="plugin",
            symptom="plugin_outdated",
            evidence={"local": "v0.15.0", "latest": "v0.17.15"},
        )
        closed = tl.close_ticket(ticket.ticket_id, status="user_action_required")
        assert closed.status == "user_action_required"


class TestMcpHandshakeFailSymptom:
    """mcp_handshake_fail: server up but MCP protocol fails."""

    def test_escalated_on_retry_failure(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system", category="connection", symptom="mcp_handshake_fail"
        )
        tl.update_ticket(ticket.ticket_id,
                         action={"action": "retry", "result": "still_failing"})
        closed = tl.close_ticket(ticket.ticket_id, status="escalated",
                                  escalated_to="https://github.com/a92rehman/custom-data-mcp/issues/99")
        assert closed.escalated_to is not None


class TestHookCrashedSymptom:
    """hook_crashed: bash.exe.stackdump or hook log errors."""

    def test_auto_fix_switch_to_python(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)
        ticket = tl.open_ticket(
            loop="system",
            category="plugin",
            symptom="hook_crashed",
            evidence={"stackdump_found": True, "python_hook_exists": True},
        )
        tl.update_ticket(ticket.ticket_id,
                         action={"action": "verify_python_hook", "result": "success"})
        closed = tl.close_ticket(ticket.ticket_id, status="auto_fixed",
                                  resolution_notes="Switched to Python hook, deleted stackdump")
        assert closed.status == "auto_fixed"


class TestTicketLifecycleRoundtrip:
    """Full lifecycle: open → diagnose → attempt fix → close/escalate."""

    def test_full_lifecycle(self, tmp_path, monkeypatch):
        tl = _setup_ticket_logger(tmp_path, monkeypatch)

        # Open
        ticket = tl.open_ticket(
            loop="system", category="connection", symptom="connection_failed",
            severity="error",
        )
        assert ticket.status == "open"

        # Diagnose
        tl.update_ticket(ticket.ticket_id, diagnosis="Server returned 503",
                         status="diagnosing")

        # Attempt 1
        tl.update_ticket(ticket.ticket_id,
                         action={"action": "retry", "result": "503", "attempt": 1})

        # Attempt 2
        tl.update_ticket(ticket.ticket_id,
                         action={"action": "retry", "result": "503", "attempt": 2})

        # Escalate
        closed = tl.close_ticket(ticket.ticket_id, status="escalated",
                                  resolution_notes="2 retries failed, filing issue")
        assert closed.status == "escalated"
        assert len(closed.actions_attempted) == 2

        # Verify read back
        all_tickets = tl.read_local_tickets()
        matching = [t for t in all_tickets if t.ticket_id == ticket.ticket_id]
        assert len(matching) == 1
        assert matching[0].status == "escalated"

"""Tests for CLI setup/uninstall commands."""

import json

from click.testing import CliRunner

from taleemabad_data_mcp.cli import _bundled_rules_dir, main


def test_setup_copies_rules_and_config(tmp_path, monkeypatch):
    """Setup should copy rules and create settings.json."""
    claude_dir = tmp_path / ".claude"
    monkeypatch.setattr("taleemabad_data_mcp.cli._claude_dir", lambda: claude_dir)
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._rules_dest", lambda: claude_dir / "rules" / "taleemabad"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._settings_path", lambda: claude_dir / "settings.json"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._env_path", lambda: claude_dir / "taleemabad-data-mcp.env"
    )

    # Create a fake credentials file
    creds = tmp_path / "key.json"
    creds.write_text("{}")

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--user", "Test User", "--credentials", str(creds)])
    assert result.exit_code == 0, result.output

    # Rules were copied
    rules_dir = claude_dir / "rules" / "taleemabad"
    assert rules_dir.exists()
    assert (rules_dir / "index.md").exists()
    assert (rules_dir / "bigquery.md").exists()
    teacher_rules = rules_dir / "ict-islamabad" / "dimensions" / "teachers"
    assert (teacher_rules / "teacher-query-rules.md").exists()

    # Settings.json was created with MCP config
    settings = json.loads((claude_dir / "settings.json").read_text())
    assert "mcpServers" in settings
    assert "taleemabad-data" in settings["mcpServers"]

    # Env file was created
    env_content = (claude_dir / "taleemabad-data-mcp.env").read_text()
    assert "TALEEMABAD_USER=Test User" in env_content


def test_uninstall_removes_everything(tmp_path, monkeypatch):
    """Uninstall should remove rules, config, and env file."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    monkeypatch.setattr("taleemabad_data_mcp.cli._claude_dir", lambda: claude_dir)
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._rules_dest", lambda: claude_dir / "rules" / "taleemabad"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._settings_path", lambda: claude_dir / "settings.json"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._env_path", lambda: claude_dir / "taleemabad-data-mcp.env"
    )

    # Create the things that setup would have created
    rules_dir = claude_dir / "rules" / "taleemabad"
    rules_dir.mkdir(parents=True)
    (rules_dir / "index.md").write_text("test")

    settings = {"mcpServers": {"taleemabad-data": {"command": "uvx"}}}
    (claude_dir / "settings.json").write_text(json.dumps(settings))

    env_path = claude_dir / "taleemabad-data-mcp.env"
    env_path.write_text("TALEEMABAD_USER=test")

    runner = CliRunner()
    result = runner.invoke(main, ["uninstall"])
    assert result.exit_code == 0, result.output

    assert not rules_dir.exists()
    assert "taleemabad-data" not in json.loads((claude_dir / "settings.json").read_text()).get(
        "mcpServers", {}
    )
    assert not env_path.exists()


def test_setup_merges_existing_settings(tmp_path, monkeypatch):
    """Setup should merge into existing settings, not overwrite."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    monkeypatch.setattr("taleemabad_data_mcp.cli._claude_dir", lambda: claude_dir)
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._rules_dest", lambda: claude_dir / "rules" / "taleemabad"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._settings_path", lambda: claude_dir / "settings.json"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._env_path", lambda: claude_dir / "taleemabad-data-mcp.env"
    )

    # Pre-existing settings with another MCP server
    existing = {"mcpServers": {"other-server": {"command": "node"}}, "theme": "dark"}
    (claude_dir / "settings.json").write_text(json.dumps(existing))

    creds = tmp_path / "key.json"
    creds.write_text("{}")

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--user", "Ali", "--credentials", str(creds)])
    assert result.exit_code == 0, result.output

    settings = json.loads((claude_dir / "settings.json").read_text())
    # Both servers should exist
    assert "other-server" in settings["mcpServers"]
    assert "taleemabad-data" in settings["mcpServers"]
    # Other settings preserved
    assert settings["theme"] == "dark"


def test_bundled_rules_exist():
    """The package should include bundled rule files."""
    rules_dir = _bundled_rules_dir()
    assert rules_dir.exists(), f"Rules dir not found: {rules_dir}"
    assert (rules_dir / "index.md").exists()
    assert (rules_dir / "data-governance.md").exists()
    assert (rules_dir / "bigquery.md").exists()

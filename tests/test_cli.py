"""Tests for CLI setup/uninstall commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from taleemabad_data_mcp.cli import _bundled_rules_dir, _mcp_server_config, _uv_path, main


def _mock_patches(monkeypatch, claude_dir):
    """Apply common monkeypatches for CLI tests."""
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
    # Skip actual venv creation in tests
    monkeypatch.setattr("taleemabad_data_mcp.cli._create_venv_and_install", lambda: None)
    # Return current python as the venv python (it exists)
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._venv_python", lambda: claude_dir / "fake-python"
    )
    # Create the fake python file so the exists() check passes
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "fake-python").write_text("")


def test_setup_copies_rules_and_config(tmp_path, monkeypatch):
    """Setup should copy rules and create settings.json."""
    claude_dir = tmp_path / ".claude"
    _mock_patches(monkeypatch, claude_dir)

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
    # Verify it uses uv-based config
    server_config = settings["mcpServers"]["taleemabad-data"]
    assert server_config["args"][0] == "run"
    assert "--with" in server_config["args"]
    assert "TALEEMABAD_USER" in server_config["env"]
    assert server_config["env"]["TALEEMABAD_USER"] == "Test User"

    # Env file was created
    env_content = (claude_dir / "taleemabad-data-mcp.env").read_text()
    assert "TALEEMABAD_USER=Test User" in env_content


def test_uninstall_removes_everything(tmp_path, monkeypatch):
    """Uninstall should remove rules, config, venv, and env file."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    _mock_patches(monkeypatch, claude_dir)
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._venv_dir", lambda: claude_dir / "taleemabad-venv"
    )

    # Create the things that setup would have created
    rules_dir = claude_dir / "rules" / "taleemabad"
    rules_dir.mkdir(parents=True)
    (rules_dir / "index.md").write_text("test")

    venv_dir = claude_dir / "taleemabad-venv"
    venv_dir.mkdir()
    (venv_dir / "marker").write_text("venv")

    settings = {"mcpServers": {"taleemabad-data": {"command": "python"}}}
    (claude_dir / "settings.json").write_text(json.dumps(settings))

    env_path = claude_dir / "taleemabad-data-mcp.env"
    env_path.write_text("TALEEMABAD_USER=test")

    runner = CliRunner()
    result = runner.invoke(main, ["uninstall"])
    assert result.exit_code == 0, result.output

    assert not rules_dir.exists()
    assert not venv_dir.exists()
    assert "taleemabad-data" not in json.loads(
        (claude_dir / "settings.json").read_text()
    ).get("mcpServers", {})
    assert not env_path.exists()


def test_setup_merges_existing_settings(tmp_path, monkeypatch):
    """Setup should merge into existing settings, not overwrite."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    _mock_patches(monkeypatch, claude_dir)

    # Pre-existing settings with another MCP server
    existing = {"mcpServers": {"other-server": {"command": "node"}}, "theme": "dark"}
    (claude_dir / "settings.json").write_text(json.dumps(existing))

    creds = tmp_path / "key.json"
    creds.write_text("{}")

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--user", "Ali", "--credentials", str(creds)])
    assert result.exit_code == 0, result.output

    settings = json.loads((claude_dir / "settings.json").read_text())
    assert "other-server" in settings["mcpServers"]
    assert "taleemabad-data" in settings["mcpServers"]
    assert settings["theme"] == "dark"


def test_bundled_rules_exist():
    """The package should include bundled rule files."""
    rules_dir = _bundled_rules_dir()
    assert rules_dir.exists(), f"Rules dir not found: {rules_dir}"
    assert (rules_dir / "index.md").exists()
    assert (rules_dir / "data-governance.md").exists()
    assert (rules_dir / "bigquery.md").exists()


def test_uv_path_windows(monkeypatch):
    monkeypatch.setattr("taleemabad_data_mcp.cli.sys.platform", "win32")
    result = _uv_path()
    assert result.name == "uv.exe"
    assert ".claude" in str(result)


def test_uv_path_unix(monkeypatch):
    monkeypatch.setattr("taleemabad_data_mcp.cli.sys.platform", "linux")
    result = _uv_path()
    assert result.name == "uv"
    assert ".claude" in str(result)


def test_mcp_server_config_uses_uv(monkeypatch):
    fake_uv = Path("/fake/.claude/uv")
    monkeypatch.setattr("taleemabad_data_mcp.cli._uv_path", lambda: fake_uv)
    config = _mcp_server_config("/path/to/creds.json", "Test User")
    assert config["command"] == str(fake_uv)
    assert config["args"][0] == "run"
    assert "--with" in config["args"]


def test_mcp_server_config_git_url_format(monkeypatch):
    monkeypatch.setattr("taleemabad_data_mcp.cli._uv_path", lambda: Path("/fake/uv"))
    config = _mcp_server_config("/path/to/creds.json", "Test User")
    with_idx = config["args"].index("--with")
    git_url = config["args"][with_idx + 1]
    assert git_url.startswith("git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v")
    assert "TALEEMABAD_HOSTNAME" not in config.get("env", {})

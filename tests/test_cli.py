"""Tests for CLI setup/uninstall commands."""


from click.testing import CliRunner

from taleemabad_data_mcp.cli import _bundled_rules_dir, main


def _mock_patches(monkeypatch, claude_dir):
    """Apply common monkeypatches for CLI tests."""
    monkeypatch.setattr("taleemabad_data_mcp.cli._claude_dir", lambda: claude_dir)
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._rules_dest", lambda: claude_dir / "rules" / "taleemabad"
    )
    monkeypatch.setattr(
        "taleemabad_data_mcp.cli._env_path", lambda: claude_dir / "taleemabad-data-mcp.env"
    )
    claude_dir.mkdir(parents=True, exist_ok=True)


def test_setup_saves_email_and_cleans_old_rules(tmp_path, monkeypatch):
    """Setup should save email config and remove old global rules."""
    claude_dir = tmp_path / ".claude"
    _mock_patches(monkeypatch, claude_dir)

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--email", "test@taleemabad.com"])
    assert result.exit_code == 0, result.output

    # Old global rules should NOT exist (setup removes them, doesn't create them)
    rules_dir = claude_dir / "rules" / "taleemabad"
    assert not rules_dir.exists()

    # Env file was created with email
    env_content = (claude_dir / "taleemabad-data-mcp.env").read_text()
    assert "TALEEMABAD_USER=test@taleemabad.com" in env_content

    # Setup message mentions rules are managed by plugin
    assert "managed by the plugin" in result.output


def test_uninstall_removes_rules_and_env(tmp_path, monkeypatch):
    """Uninstall should remove rules and env file."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    _mock_patches(monkeypatch, claude_dir)

    # Create the things that setup would have created
    rules_dir = claude_dir / "rules" / "taleemabad"
    rules_dir.mkdir(parents=True)
    (rules_dir / "index.md").write_text("test")

    env_path = claude_dir / "taleemabad-data-mcp.env"
    env_path.write_text("TALEEMABAD_USER=test")

    runner = CliRunner()
    result = runner.invoke(main, ["uninstall"])
    assert result.exit_code == 0, result.output

    assert not rules_dir.exists()
    assert not env_path.exists()


def test_bundled_rules_exist():
    """The package should include bundled rule files."""
    rules_dir = _bundled_rules_dir()
    assert rules_dir.exists(), f"Rules dir not found: {rules_dir}"
    assert (rules_dir / "index.md").exists()
    assert (rules_dir / "data-governance.md").exists()
    assert (rules_dir / "bigquery.md").exists()


def test_setup_warns_about_old_artifacts(tmp_path, monkeypatch):
    """Setup should warn about old venv and .mcp.json."""
    claude_dir = tmp_path / ".claude"
    _mock_patches(monkeypatch, claude_dir)

    # Create old artifacts
    old_venv = claude_dir / "taleemabad-venv"
    old_venv.mkdir(parents=True)

    monkeypatch.chdir(tmp_path)
    old_mcp = tmp_path / ".mcp.json"
    old_mcp.write_text('{"mcpServers": {"taleemabad-data": {}}}')

    runner = CliRunner()
    result = runner.invoke(main, ["setup", "--email", "ali@taleemabad.com"])
    assert result.exit_code == 0, result.output
    assert "Old venv found" in result.output
    assert "Old .mcp.json found" in result.output

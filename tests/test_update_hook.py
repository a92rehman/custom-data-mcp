"""Tests for the cross-platform Python session-start hook."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _import_hook():
    """Import the hook module dynamically."""
    hook_path = Path(__file__).parent.parent / "hooks" / "session-start" / "update.py"
    spec = importlib.util.spec_from_file_location("update_hook", hook_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_hook_imports():
    """Hook module should import without errors."""
    mod = _import_hook()
    assert hasattr(mod, "main")
    assert hasattr(mod, "_get_latest_tag")
    assert hasattr(mod, "_find_plugin_dir")


def test_export_user_env(tmp_path, monkeypatch):
    """Should read TALEEMABAD_USER from env file."""
    mod = _import_hook()
    env_file = tmp_path / "taleemabad-data-mcp.env"
    env_file.write_text("TALEEMABAD_USER=test@taleemabad.com\n")
    monkeypatch.setattr(mod, "ENV_FILE", env_file)
    monkeypatch.delenv("TALEEMABAD_USER", raising=False)

    mod._export_user_env()
    import os
    assert os.environ.get("TALEEMABAD_USER") == "test@taleemabad.com"

    # Clean up
    monkeypatch.delenv("TALEEMABAD_USER", raising=False)


def test_export_user_env_missing_file(tmp_path, monkeypatch):
    """Should not fail if env file doesn't exist."""
    mod = _import_hook()
    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / "nonexistent.env")
    mod._export_user_env()  # Should not raise


def test_is_recently_checked_no_file(tmp_path, monkeypatch):
    """Should return False if version file doesn't exist."""
    mod = _import_hook()
    monkeypatch.setattr(mod, "VERSION_FILE", tmp_path / "nonexistent")
    assert mod._is_recently_checked() is False


def test_is_recently_checked_fresh(tmp_path, monkeypatch):
    """Should return True if version file was just created."""
    mod = _import_hook()
    vf = tmp_path / "version"
    vf.write_text("v0.17.15")
    monkeypatch.setattr(mod, "VERSION_FILE", vf)
    assert mod._is_recently_checked() is True


def test_write_rules_path(tmp_path, monkeypatch):
    """Should write rules path pointer file."""
    mod = _import_hook()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "index.md").write_text("# Rules")

    path_file = tmp_path / "rules-path"
    monkeypatch.setattr(mod, "RULES_PATH_FILE", path_file)

    mod._write_rules_path(rules_dir)
    assert path_file.exists()
    assert path_file.read_text() == str(rules_dir)


def test_write_rules_path_no_index(tmp_path, monkeypatch):
    """Should not write path file if index.md is missing."""
    mod = _import_hook()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    path_file = tmp_path / "rules-path"
    monkeypatch.setattr(mod, "RULES_PATH_FILE", path_file)

    mod._write_rules_path(rules_dir)
    assert not path_file.exists()


def test_check_health_missing_env(tmp_path, monkeypatch):
    """Should detect missing env file."""
    mod = _import_hook()
    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / "nonexistent.env")
    monkeypatch.setattr(mod, "RULES_PATH_FILE", tmp_path / "nonexistent-path")

    symptoms = mod._check_health(tmp_path, tmp_path / "rules")
    assert "user_env_missing" in symptoms
    assert "rules_path_missing" in symptoms


def test_check_health_unexpanded_env(tmp_path, monkeypatch):
    """Should detect unexpanded env var placeholder."""
    mod = _import_hook()
    env_file = tmp_path / "env"
    env_file.write_text("TALEEMABAD_USER=${TALEEMABAD_USER}\n")
    monkeypatch.setattr(mod, "ENV_FILE", env_file)

    rules_path_file = tmp_path / "rp"
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    rules_path_file.write_text(str(rules_dir))
    monkeypatch.setattr(mod, "RULES_PATH_FILE", rules_path_file)

    symptoms = mod._check_health(tmp_path, rules_dir)
    assert "user_env_unexpanded" in symptoms


def test_touch_version(tmp_path, monkeypatch):
    """Should create/touch version file."""
    mod = _import_hook()
    vf = tmp_path / "version"
    monkeypatch.setattr(mod, "VERSION_FILE", vf)

    mod._touch_version()
    assert vf.exists()
    assert vf.read_text() == "unknown"


def test_main_no_plugin_dir(tmp_path, monkeypatch):
    """Main should exit gracefully if no plugin dir found."""
    mod = _import_hook()
    monkeypatch.setattr(mod, "CLAUDE_DIR", tmp_path / ".claude")
    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / "env")
    monkeypatch.setattr(mod, "HOOK_LOG", tmp_path / "hook.log")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", "")

    # Should not raise
    mod.main()


def test_sentinel_written_on_health_failure(tmp_path, monkeypatch):
    """Sentinel file should be written when health checks fail."""
    mod = _import_hook()

    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    # Set up a plugin dir with rules
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / ".claude-plugin").mkdir()
    rules_dir = plugin_dir / "rules"
    rules_dir.mkdir()
    (rules_dir / "index.md").write_text("# Rules")

    # Monkeypatch all paths
    monkeypatch.setattr(mod, "CLAUDE_DIR", claude_dir)
    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / "nonexistent.env")  # missing env
    monkeypatch.setattr(mod, "VERSION_FILE", claude_dir / "version")
    monkeypatch.setattr(mod, "RULES_PATH_FILE", claude_dir / "rules-path")
    monkeypatch.setattr(mod, "HOOK_LOG", claude_dir / "hook.log")
    monkeypatch.setattr(mod, "DOCTOR_SENTINEL", claude_dir / "doctor-needed")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_dir))
    monkeypatch.setenv("TALEEMABAD_PIN_VERSION", "v0.0.1")  # skip network

    mod.main()

    sentinel = claude_dir / "doctor-needed"
    assert sentinel.exists()
    content = sentinel.read_text()
    assert "user_env_missing" in content

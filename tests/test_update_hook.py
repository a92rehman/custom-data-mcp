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


def test_auto_heal_fixes_rules_path(tmp_path, monkeypatch):
    """Auto-heal should rewrite rules path when missing."""
    mod = _import_hook()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "index.md").write_text("# Rules")

    path_file = tmp_path / "rules-path"
    monkeypatch.setattr(mod, "RULES_PATH_FILE", path_file)
    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / "env")
    monkeypatch.setattr(mod, "CLAUDE_DIR", tmp_path)

    mod._auto_heal(tmp_path, rules_dir)
    assert path_file.exists()
    assert path_file.read_text() == str(rules_dir)


def test_auto_heal_recovers_email(tmp_path, monkeypatch):
    """Auto-heal should recover email from audit log when env missing."""
    mod = _import_hook()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "index.md").write_text("# Rules")

    audit_dir = tmp_path / "taleemabad-logs"
    audit_dir.mkdir(parents=True)
    (audit_dir / "activity.jsonl").write_text(
        '{"user_email":"test@taleemabad.com","query_text":"test"}\n'
    )

    env_file = tmp_path / "env"
    monkeypatch.setattr(mod, "ENV_FILE", env_file)
    monkeypatch.setattr(mod, "RULES_PATH_FILE", tmp_path / "rp")
    monkeypatch.setattr(mod, "CLAUDE_DIR", tmp_path)

    mod._auto_heal(tmp_path, rules_dir)
    assert env_file.exists()
    assert "test@taleemabad.com" in env_file.read_text()


def test_auto_heal_fixes_unexpanded_env(tmp_path, monkeypatch):
    """Auto-heal should fix literal ${TALEEMABAD_USER} in env file."""
    mod = _import_hook()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    env_file = tmp_path / "env"
    env_file.write_text("TALEEMABAD_USER=${TALEEMABAD_USER}\n")
    monkeypatch.setattr(mod, "ENV_FILE", env_file)
    monkeypatch.setattr(mod, "RULES_PATH_FILE", tmp_path / "rp")
    monkeypatch.setattr(mod, "CLAUDE_DIR", tmp_path)
    monkeypatch.setenv("TALEEMABAD_USER", "real@taleemabad.com")

    mod._auto_heal(tmp_path, rules_dir)
    content = env_file.read_text()
    assert "${" not in content
    assert "real@taleemabad.com" in content


def test_auto_heal_deletes_stackdump(tmp_path, monkeypatch):
    """Auto-heal should silently delete bash.exe.stackdump."""
    mod = _import_hook()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    stackdump = tmp_path / "bash.exe.stackdump"
    stackdump.write_text("crash data")

    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / "env")
    monkeypatch.setattr(mod, "RULES_PATH_FILE", tmp_path / "rp")
    monkeypatch.setattr(mod, "CLAUDE_DIR", tmp_path)

    mod._auto_heal(tmp_path, rules_dir)
    assert not stackdump.exists()


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


def test_auto_heal_runs_in_main(tmp_path, monkeypatch):
    """Main should run auto-heal silently when version is pinned."""
    mod = _import_hook()

    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / ".claude-plugin").mkdir()
    rules_dir = plugin_dir / "rules"
    rules_dir.mkdir()
    (rules_dir / "index.md").write_text("# Rules")

    # Create stackdump to verify auto-heal runs
    stackdump = plugin_dir / "bash.exe.stackdump"
    stackdump.write_text("crash")

    monkeypatch.setattr(mod, "CLAUDE_DIR", claude_dir)
    monkeypatch.setattr(mod, "ENV_FILE", tmp_path / "nonexistent.env")
    monkeypatch.setattr(mod, "VERSION_FILE", claude_dir / "version")
    monkeypatch.setattr(mod, "RULES_PATH_FILE", claude_dir / "rules-path")
    monkeypatch.setattr(mod, "HOOK_LOG", claude_dir / "hook.log")
    monkeypatch.setattr(mod, "DOCTOR_SENTINEL", claude_dir / "doctor-needed")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_dir))
    monkeypatch.setenv("TALEEMABAD_PIN_VERSION", "v0.0.1")  # skip network

    mod.main()

    # Auto-heal should have deleted the stackdump
    assert not stackdump.exists()
    # Auto-heal should have fixed the rules path
    assert (claude_dir / "rules-path").exists()

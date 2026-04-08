"""Tests for bump_version CLI function — TDD: write tests before implementation."""
import re
import json
import shutil
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def fake_repo(tmp_path):
    """Create a minimal fake repo structure for testing bump_version."""
    src = tmp_path / "src" / "taleemabad_data_mcp"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text('__version__ = "0.4.8"\n')

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "taleemabad-data-mcp"
        version = "0.4.8"
    """))

    # Create source rules (what bump_version copies FROM)
    rules = src / "rules"
    rules.mkdir()
    (rules / "index.md").write_text("# Rules Index\n")
    (rules / "bigquery.md").write_text("# BigQuery\n")

    # Create plugin directory (what bump_version writes TO)
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / ".current-version").write_text("v0.4.8\n")

    manifest_dir = plugin_dir / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(
        json.dumps({"name": "taleemabad-data", "version": "0.4.8"}) + "\n"
    )

    # Existing plugin/rules with stale content (should be replaced by bump)
    plugin_rules = plugin_dir / "rules"
    plugin_rules.mkdir()
    (plugin_rules / "old-stale.md").write_text("stale content\n")

    return tmp_path


def _call_bump(fake_repo, minor=False):
    """Call bump_version with fake_repo as the project root."""
    from taleemabad_data_mcp.cli import bump_version
    # Patch Path(__file__).parent inside bump_version to point at fake_repo/src/taleemabad_data_mcp
    fake_cli_file = fake_repo / "src" / "taleemabad_data_mcp" / "cli.py"
    with patch("taleemabad_data_mcp.cli.__file__", str(fake_cli_file)):
        bump_version(minor=minor)


def test_patch_bump_updates_init(fake_repo):
    _call_bump(fake_repo, minor=False)
    text = (fake_repo / "src" / "taleemabad_data_mcp" / "__init__.py").read_text()
    assert '__version__ = "0.4.9"' in text


def test_minor_bump_updates_init(fake_repo):
    _call_bump(fake_repo, minor=True)
    text = (fake_repo / "src" / "taleemabad_data_mcp" / "__init__.py").read_text()
    assert '__version__ = "0.5.0"' in text


def test_bump_updates_pyproject(fake_repo):
    _call_bump(fake_repo, minor=False)
    text = (fake_repo / "pyproject.toml").read_text()
    assert 'version = "0.4.9"' in text


def test_bump_syncs_rules_to_plugin(fake_repo):
    """After bump, plugin/rules/ should contain src rules, not stale content."""
    _call_bump(fake_repo, minor=False)
    plugin_rules = fake_repo / "plugin" / "rules"
    assert (plugin_rules / "index.md").exists()
    assert (plugin_rules / "bigquery.md").exists()
    # Old stale file should be gone (directory was replaced)
    assert not (plugin_rules / "old-stale.md").exists()


def test_bump_updates_plugin_manifest_version(fake_repo):
    _call_bump(fake_repo, minor=False)
    manifest = json.loads(
        (fake_repo / "plugin" / ".claude-plugin" / "plugin.json").read_text()
    )
    assert manifest["version"] == "0.4.9"


def test_bump_updates_current_version_file(fake_repo):
    _call_bump(fake_repo, minor=False)
    content = (fake_repo / "plugin" / ".current-version").read_text().strip()
    assert content == "v0.4.9"

"""CLI for setup, uninstall, and running the MCP server."""

from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path

import click
import structlog

logger = structlog.get_logger()

PACKAGE_NAME = "taleemabad-data-mcp"
RULES_DIR_NAME = "taleemabad"


def _claude_dir() -> Path:
    """Return ~/.claude/ path."""
    return Path.home() / ".claude"


def _rules_dest() -> Path:
    """Return ~/.claude/rules/taleemabad/ path."""
    return _claude_dir() / "rules" / RULES_DIR_NAME


def _settings_path() -> Path:
    """Return ~/.claude/settings.json path."""
    return _claude_dir() / "settings.json"


def _env_path() -> Path:
    """Return ~/.claude/taleemabad-data-mcp.env path."""
    return _claude_dir() / "taleemabad-data-mcp.env"


def _bundled_rules_dir() -> Path:
    """Return the rules directory bundled inside this package."""
    return Path(__file__).parent / "rules"


def _load_settings() -> dict:
    """Load existing settings.json or return empty dict."""
    path = _settings_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_settings(settings: dict) -> None:
    """Write settings.json, creating directories as needed."""
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def _mcp_server_config(credentials: str, user_name: str) -> dict:
    """Build the MCP server configuration entry."""
    return {
        "command": "uvx",
        "args": [
            "--from",
            "git+https://github.com/Orenda-Project/taleemabad-data-mcp",
            "taleemabad-data-mcp",
            "serve",
        ],
        "env": {
            "BIGQUERY_PROJECT": "niete-bq-prod",
            "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb",
            "GOOGLE_APPLICATION_CREDENTIALS": credentials,
            "TALEEMABAD_USER": user_name,
            "TALEEMABAD_HOSTNAME": platform.node(),
        },
    }


@click.group()
def main() -> None:
    """Taleemabad Data Navigator — governed semantic layer for BigQuery."""


@main.command()
@click.option("--user", required=True, help="Your name (for activity tracking).")
@click.option(
    "--credentials",
    required=True,
    type=click.Path(exists=True),
    help="Path to Google Cloud service account JSON key.",
)
def setup(user: str, credentials: str) -> None:
    """Install rules and configure Claude Code MCP connection."""
    credentials_abs = str(Path(credentials).resolve())

    # 1. Copy rules to ~/.claude/rules/taleemabad/
    src_rules = _bundled_rules_dir()
    dest_rules = _rules_dest()

    if not src_rules.exists():
        click.echo(f"Error: bundled rules not found at {src_rules}", err=True)
        sys.exit(1)

    if dest_rules.exists():
        shutil.rmtree(dest_rules)
    shutil.copytree(src_rules, dest_rules)
    click.echo(f"Rules installed to {dest_rules}")

    # 2. Merge MCP server config into ~/.claude/settings.json
    settings = _load_settings()
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    settings["mcpServers"]["taleemabad-data"] = _mcp_server_config(credentials_abs, user)
    _save_settings(settings)
    click.echo(f"MCP server configured in {_settings_path()}")

    # 3. Write user config env file
    env_content = (
        f"TALEEMABAD_USER={user}\n"
        f"TALEEMABAD_HOSTNAME={platform.node()}\n"
        f"GOOGLE_APPLICATION_CREDENTIALS={credentials_abs}\n"
    )
    env_path = _env_path()
    env_path.write_text(env_content, encoding="utf-8")
    click.echo(f"User config saved to {env_path}")

    click.echo()
    click.echo("Setup complete! Open Claude Code in any project and ask a data question.")
    click.echo('Try: "Show me LP adoption for ICT schools this month"')


@main.command()
def uninstall() -> None:
    """Remove rules, MCP config, and user settings."""
    # 1. Remove rules
    dest_rules = _rules_dest()
    if dest_rules.exists():
        shutil.rmtree(dest_rules)
        click.echo(f"Rules removed from {dest_rules}")
    else:
        click.echo("Rules directory not found (already removed).")

    # 2. Remove MCP server entry from settings.json
    settings = _load_settings()
    if "mcpServers" in settings and "taleemabad-data" in settings["mcpServers"]:
        del settings["mcpServers"]["taleemabad-data"]
        if not settings["mcpServers"]:
            del settings["mcpServers"]
        _save_settings(settings)
        click.echo(f"MCP server removed from {_settings_path()}")
    else:
        click.echo("MCP server config not found (already removed).")

    # 3. Remove env file
    env_path = _env_path()
    if env_path.exists():
        env_path.unlink()
        click.echo(f"User config removed from {env_path}")

    click.echo("Uninstall complete.")


@main.command()
def serve() -> None:
    """Run the MCP server (stdio mode). Used by Claude Code automatically."""
    from taleemabad_data_mcp.server import mcp

    mcp.run()

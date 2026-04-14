"""CLI for setup, uninstall, and running the MCP server."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import click

RULES_DIR_NAME = "taleemabad"
CREDENTIALS_FILENAME = "niete-bq-prod-48ae5260d1ea.json"


def _claude_dir() -> Path:
    """Return ~/.claude/ path."""
    return Path.home() / ".claude"


def _rules_dest() -> Path:
    """Return ~/.claude/rules/taleemabad/ path."""
    return _claude_dir() / "rules" / RULES_DIR_NAME


def _env_path() -> Path:
    """Return ~/.claude/taleemabad-data-mcp.env path."""
    return _claude_dir() / "taleemabad-data-mcp.env"


def _bundled_rules_dir() -> Path:
    """Return the rules directory bundled inside this package."""
    return Path(__file__).parent / "rules"


@click.group()
def main() -> None:
    """Taleemabad Data Navigator — governed semantic layer for BigQuery."""


@main.command(name="version")
def show_version() -> None:
    """Show the installed version."""
    from taleemabad_data_mcp import __version__

    click.echo(f"taleemabad-data-mcp v{__version__}")


def bump_version(minor: bool = False) -> None:
    """Bump package version (patch or minor) and sync plugin rules.

    Patch bump (default): 0.3.0 -> 0.3.1 (fixes, small changes)
    Minor bump (minor=True): 0.3.1 -> 0.4.0 (new features, bigger releases)
    """
    import re

    init_file = Path(__file__).parent / "__init__.py"
    repo_root = Path(__file__).parent.parent.parent
    pyproject_file = repo_root / "pyproject.toml"
    src_rules_dir = Path(__file__).parent / "rules"
    plugin_rules_dir = repo_root / "rules"
    claude_rules_dir = repo_root / ".claude" / "rules"

    # Read current version
    init_text = init_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', init_text)
    if not match:
        raise RuntimeError("Could not find __version__ in __init__.py")

    major, mid, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    old_version = f"{major}.{mid}.{patch}"

    new_version = f"{major}.{mid + 1}.0" if minor else f"{major}.{mid}.{patch + 1}"

    # Update __init__.py
    new_init = init_text.replace(
        f'__version__ = "{old_version}"', f'__version__ = "{new_version}"'
    )
    init_file.write_text(new_init, encoding="utf-8")

    # Update pyproject.toml
    if pyproject_file.exists():
        pyproject_text = pyproject_file.read_text(encoding="utf-8")
        new_pyproject = pyproject_text.replace(
            f'version = "{old_version}"', f'version = "{new_version}"',
        )
        pyproject_file.write_text(new_pyproject, encoding="utf-8")

    # Determine the rules source: .claude/rules/ (dev working copy) if it exists,
    # otherwise src/rules/ (package source). Developers edit .claude/rules/ directly
    # since Claude Code loads it as session context. Bump syncs it everywhere.
    if claude_rules_dir.exists() and claude_rules_dir.is_dir():
        rules_source = claude_rules_dir
    else:
        rules_source = src_rules_dir

    # Sync rules to all locations from the source
    if rules_source.exists():
        # → src/taleemabad_data_mcp/rules/ (ships with Python package)
        if rules_source != src_rules_dir:
            if src_rules_dir.exists():
                shutil.rmtree(src_rules_dir)
            shutil.copytree(rules_source, src_rules_dir)

        # → rules/ at repo root (plugin agents read from here)
        if plugin_rules_dir.exists():
            shutil.rmtree(plugin_rules_dir)
        shutil.copytree(rules_source, plugin_rules_dir)

        # → .claude/rules/ (dev working copy, gitignored)
        if rules_source != claude_rules_dir and claude_rules_dir.parent.exists():
            if claude_rules_dir.exists():
                shutil.rmtree(claude_rules_dir)
            shutil.copytree(rules_source, claude_rules_dir)

    # Update plugin manifest version
    plugin_json = repo_root / ".claude-plugin" / "plugin.json"
    if plugin_json.exists():
        manifest = json.loads(plugin_json.read_text(encoding="utf-8"))
        manifest["version"] = new_version
        plugin_json.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Update marketplace manifest version
    marketplace_json = repo_root / ".claude-plugin" / "marketplace.json"
    if marketplace_json.exists():
        mp = json.loads(marketplace_json.read_text(encoding="utf-8"))
        if "plugins" in mp and len(mp["plugins"]) > 0:
            mp["plugins"][0]["version"] = new_version
        marketplace_json.write_text(json.dumps(mp, indent=2) + "\n", encoding="utf-8")

    # Update plugin/.current-version
    current_version_file = repo_root / ".current-version"
    if current_version_file.exists():
        current_version_file.write_text(f"v{new_version}\n", encoding="utf-8")

    click.echo(f"Version bumped: {old_version} -> {new_version}")
    click.echo(
        f"  Next: git add -A && git commit -m "
        f"'chore: bump version to v{new_version}' && git push"
    )


@main.command(name="bump")
@click.option(
    "--minor", is_flag=True, default=False,
    help="Bump minor version (0.X.0) for bigger releases. Default is patch (0.0.X).",
)
def bump_cmd(minor: bool) -> None:
    """Bump version, sync plugin rules, and print next steps.

    Patch bump (default): 0.3.0 -> 0.3.1 (fixes, small changes)
    Minor bump (--minor): 0.3.1 -> 0.4.0 (new features, bigger releases)
    """
    try:
        bump_version(minor=minor)
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


ALLOWED_EMAIL_DOMAINS = {"taleemabad.com", "niete.edu.pk", "niete.pk"}


def _validate_email(email: str) -> str | None:
    """Validate email domain. Returns error message or None."""
    if not email or "@" not in email:
        return "Invalid email format."
    domain = email.split("@")[1].lower()
    if domain not in ALLOWED_EMAIL_DOMAINS:
        return (
            f"Domain '@{domain}' is not allowed. "
            "Use your work email: @taleemabad.com, @niete.edu.pk, or @niete.pk"
        )
    return None


@main.command()
@click.option("--email", required=True, help="Your work email (for audit tracking).")
@click.option("--token", default="", help="Team API token (optional, from admin).")
def setup(email: str, token: str) -> None:
    """Save your email and sync governance rules.

    The MCP server runs remotely — no local Python or credentials needed.
    This command only needs to be run once.
    """
    # Validate email domain
    err = _validate_email(email)
    if err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)

    # 1. Copy rules to ~/.claude/rules/taleemabad/
    src_rules = _bundled_rules_dir()
    dest_rules = _rules_dest()

    if not src_rules.exists():
        click.echo(f"Error: bundled rules not found at {src_rules}", err=True)
        sys.exit(1)

    if dest_rules.exists():
        shutil.rmtree(dest_rules)
    dest_rules.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_rules, dest_rules)
    click.echo(f"Rules installed to {dest_rules}")

    # 2. Save user config (email + optional token)
    env_content = f"TALEEMABAD_USER={email}\n"
    if token:
        env_content += f"TALEEMABAD_API_TOKEN={token}\n"
    env_path = _env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(env_content, encoding="utf-8")
    click.echo(f"User config saved to {env_path}")

    # 3. Cleanup old artifacts from previous versions
    old_venv = _claude_dir() / "taleemabad-venv"
    if old_venv.exists():
        click.echo(f"\nNote: Old venv found at {old_venv}")
        click.echo("It is no longer needed. You can delete it manually.")

    cwd = Path.cwd()
    old_mcp = cwd / ".mcp.json"
    if old_mcp.exists():
        click.echo(f"\nNote: Old .mcp.json found at {old_mcp}")
        click.echo("The plugin now provides MCP config automatically.")
        click.echo("Delete this file to avoid conflicts.")

    # Remove stale MCP entry from settings.json (old versions wrote here)
    settings_path = _claude_dir() / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            if "mcpServers" in settings and "taleemabad-data" in settings["mcpServers"]:
                del settings["mcpServers"]["taleemabad-data"]
                if not settings["mcpServers"]:
                    del settings["mcpServers"]
                settings_path.write_text(
                    json.dumps(settings, indent=2) + "\n", encoding="utf-8"
                )
                click.echo("Removed stale MCP entry from settings.json")
        except (json.JSONDecodeError, KeyError):
            pass

    # Remove old credentials file references
    old_creds = cwd / CREDENTIALS_FILENAME
    if old_creds.exists():
        click.echo(f"\nNote: Credentials file '{CREDENTIALS_FILENAME}' found locally.")
        click.echo("It is no longer needed — the MCP server runs remotely.")
        click.echo("You can safely delete it.")

    click.echo()
    click.echo("Setup complete! Restart Claude Code to connect.")
    click.echo("No credentials file needed — the MCP server runs remotely.")


@main.command()
def uninstall() -> None:
    """Remove rules and user settings."""
    # 1. Remove rules
    dest_rules = _rules_dest()
    if dest_rules.exists():
        shutil.rmtree(dest_rules)
        click.echo(f"Rules removed from {dest_rules}")
    else:
        click.echo("Rules directory not found (already removed).")

    # 2. Remove env file
    env_path = _env_path()
    if env_path.exists():
        env_path.unlink()
        click.echo(f"User config removed from {env_path}")

    # 3. Note about old artifacts
    old_venv = _claude_dir() / "taleemabad-venv"
    if old_venv.exists():
        click.echo(f"\nNote: Old venv at {old_venv} can be deleted manually.")

    click.echo("Uninstall complete.")


@main.command()
def serve() -> None:
    """Run the MCP server (stdio mode). Used by Claude Code automatically."""
    from taleemabad_data_mcp.server import mcp

    mcp.run()


@main.command(name="serve-remote")
@click.option("--port", default=None, type=int, help="Port to listen on (default: $PORT or 8000).")
def serve_remote(port: int | None) -> None:
    """Run the MCP server with HTTP transport for Railway deployment."""
    import os

    os.environ["TALEEMABAD_REMOTE_MODE"] = "true"

    from taleemabad_data_mcp.server import mcp

    listen_port = port or int(os.environ.get("PORT", "8000"))

    # Override host/port directly on the mcp settings object
    # (MCP SDK's Settings class doesn't read FASTMCP_ env vars)
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = listen_port

    # Disable DNS rebinding protection for remote deployment
    # Railway handles TLS termination and routing; our auth middleware validates requests
    if mcp.settings.transport_security:
        mcp.settings.transport_security.enable_dns_rebinding_protection = False

    click.echo(f"Starting MCP server (streamable-http) on port {listen_port}...")
    mcp.run(transport="streamable-http")


@main.command()
def dashboard() -> None:
    """Launch the observability dashboard (Streamlit)."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        click.echo(
            "Streamlit is not installed. Install dashboard dependencies:\n"
            '  pip install "taleemabad-data-mcp[dashboard]"',
            err=True,
        )
        sys.exit(1)

    import subprocess as sp

    dashboard_app = Path(__file__).parent / "dashboard" / "app.py"
    if not dashboard_app.exists():
        click.echo(f"Dashboard app not found at {dashboard_app}", err=True)
        sys.exit(1)

    sp.run([sys.executable, "-m", "streamlit", "run", str(dashboard_app)], check=False)

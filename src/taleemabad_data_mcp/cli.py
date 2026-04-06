"""CLI for setup, uninstall, and running the MCP server."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import click

PACKAGE_NAME = "taleemabad-data-mcp"
RULES_DIR_NAME = "taleemabad"
VENV_DIR_NAME = "taleemabad-venv"
GITHUB_URL = "git+https://github.com/Orenda-Project/taleemabad-data-mcp"


def _claude_dir() -> Path:
    """Return ~/.claude/ path."""
    return Path.home() / ".claude"


def _rules_dest() -> Path:
    """Return ~/.claude/rules/taleemabad/ path."""
    return _claude_dir() / "rules" / RULES_DIR_NAME


def _venv_dir() -> Path:
    """Return ~/.claude/taleemabad-venv/ path."""
    return _claude_dir() / VENV_DIR_NAME


def _venv_python() -> Path:
    """Return the python executable inside the venv (cross-platform)."""
    venv = _venv_dir()
    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


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
    python_path = str(_venv_python())
    return {
        "command": python_path,
        "args": ["-m", "taleemabad_data_mcp", "serve"],
        "env": {
            "BIGQUERY_PROJECT": "niete-bq-prod",
            "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb",
            "GOOGLE_APPLICATION_CREDENTIALS": credentials,
            "TALEEMABAD_USER": user_name,
            "TALEEMABAD_HOSTNAME": platform.node(),
        },
    }


def _running_inside_target_venv() -> bool:
    """Check if we're already running inside the target venv."""
    venv = _venv_dir()
    try:
        return Path(sys.executable).resolve().is_relative_to(venv.resolve())
    except (ValueError, OSError):
        return False


def _create_venv_and_install() -> None:
    """Create a dedicated venv and install the package from GitHub."""
    venv = _venv_dir()

    if _running_inside_target_venv():
        click.echo("Already running from the installed environment. Skipping reinstall.")
        return

    # Create venv
    click.echo("Creating dedicated Python environment...")
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv), "--clear"],
        check=True,
        capture_output=True,
    )

    # Install package from GitHub
    if sys.platform == "win32":
        pip_exe = str(venv / "Scripts" / "pip.exe")
    else:
        pip_exe = str(venv / "bin" / "pip")
    click.echo("Installing taleemabad-data-mcp (this may take a minute)...")
    result = subprocess.run(
        [pip_exe, "install", GITHUB_URL],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo(f"Installation failed:\n{result.stderr}", err=True)
        sys.exit(1)
    click.echo("Package installed successfully.")


def _mcp_json_content(credentials: str, user_name: str) -> dict:
    """Build the .mcp.json file content."""
    return {
        "mcpServers": {
            "taleemabad-data": _mcp_server_config(credentials, user_name),
        },
    }


def _write_mcp_json(directory: Path, credentials: str, user_name: str) -> None:
    """Write .mcp.json to a directory."""
    mcp_json_path = directory / ".mcp.json"
    content = _mcp_json_content(credentials, user_name)
    mcp_json_path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    return mcp_json_path


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

    # 1. Create venv and install package
    _create_venv_and_install()

    # Verify the venv python works
    python_path = _venv_python()
    if not python_path.exists():
        click.echo(f"Error: Python not found at {python_path}", err=True)
        sys.exit(1)

    # 2. Copy rules to ~/.claude/rules/taleemabad/
    src_rules = _bundled_rules_dir()
    dest_rules = _rules_dest()

    if not src_rules.exists():
        click.echo(f"Error: bundled rules not found at {src_rules}", err=True)
        sys.exit(1)

    if dest_rules.exists():
        shutil.rmtree(dest_rules)
    shutil.copytree(src_rules, dest_rules)
    click.echo(f"Rules installed to {dest_rules}")

    # 3. Merge MCP server config into ~/.claude/settings.json
    settings = _load_settings()
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    settings["mcpServers"]["taleemabad-data"] = _mcp_server_config(credentials_abs, user)
    _save_settings(settings)
    click.echo(f"MCP server configured in {_settings_path()}")

    # 4. Write user config env file
    env_content = (
        f"TALEEMABAD_USER={user}\n"
        f"TALEEMABAD_HOSTNAME={platform.node()}\n"
        f"GOOGLE_APPLICATION_CREDENTIALS={credentials_abs}\n"
    )
    env_path = _env_path()
    env_path.write_text(env_content, encoding="utf-8")
    click.echo(f"User config saved to {env_path}")

    click.echo()
    click.echo("Setup complete!")
    click.echo()
    click.echo("Next: go to any project and run:")
    click.echo("  taleemabad-data-mcp init")
    click.echo()
    click.echo("This creates .mcp.json so Claude Code connects to the data MCP.")


@main.command()
def init() -> None:
    """Add .mcp.json to the current project directory.

    Run this in any project where you want the Taleemabad data MCP available.
    Reads your credentials from the setup config.
    """
    env_path = _env_path()
    if not env_path.exists():
        click.echo("Error: run 'taleemabad-data-mcp setup' first.", err=True)
        sys.exit(1)

    # Read saved config
    env_vars = {}
    for line in env_path.read_text(encoding="utf-8").strip().split("\n"):
        if "=" in line:
            key, value = line.split("=", 1)
            env_vars[key] = value

    user_name = env_vars.get("TALEEMABAD_USER", "unknown")
    credentials = env_vars.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    if not credentials:
        click.echo("Error: no credentials found in config. Re-run setup.", err=True)
        sys.exit(1)

    cwd = Path.cwd()
    mcp_path = _write_mcp_json(cwd, credentials, user_name)
    click.echo(f"Created {mcp_path}")
    click.echo()
    click.echo("Open Claude Code here and run /mcp to verify.")
    click.echo('Then ask: "Show me LP adoption for ICT schools this month"')


@main.command()
def uninstall() -> None:
    """Remove rules, MCP config, venv, and user settings."""
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

    # 3. Remove venv
    venv = _venv_dir()
    if venv.exists():
        shutil.rmtree(venv)
        click.echo(f"Python environment removed from {venv}")

    # 4. Remove env file
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

    sp.run(["streamlit", "run", str(dashboard_app)], check=False)

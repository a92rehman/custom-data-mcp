"""CLI for setup, uninstall, and running the MCP server."""

from __future__ import annotations

import json
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


def _uv_path() -> Path:
    """Return ~/.claude/uv.exe (Windows) or ~/.claude/uv (Unix)."""
    if sys.platform == "win32":
        return _claude_dir() / "uv.exe"
    return _claude_dir() / "uv"


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
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {}


def _save_settings(settings: dict) -> None:
    """Write settings.json, creating directories as needed."""
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def _to_bash_path(p: Path) -> str:
    """Convert a Windows path to a bash-compatible path (e.g. C:\\foo -> /c/foo).

    Claude Code on Windows runs in bash (Git Bash / MSYS2), which cannot resolve
    Windows-style paths as executable commands. Convert drive letter paths so the
    MCP server config works correctly on Windows.
    """
    if sys.platform == "win32":
        parts = p.parts  # ('C:\\', 'Users', ...)
        if parts and len(parts[0]) == 3 and parts[0][1] == ":":
            drive = parts[0][0].lower()
            rest = "/".join(parts[1:])
            return f"/{drive}/{rest}"
    return str(p)


def _find_uv_command() -> str:
    """Find the uv command — prefer PATH, fall back to ~/.claude/uv.

    On Windows, returns a bash-compatible path since Claude Code runs
    in Git Bash / MSYS2 which cannot resolve Windows-style paths.
    """
    uv_on_path = shutil.which("uv")
    if uv_on_path:
        return "uv"
    local_uv = _uv_path()
    if local_uv.exists():
        return _to_bash_path(local_uv)
    return "uv"  # hope it's on PATH at runtime


def _mcp_server_config(credentials: str, user_name: str) -> dict:
    """Build the MCP server configuration entry (uv-based)."""
    from taleemabad_data_mcp import __version__
    git_ref = f"git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@v{__version__}"
    return {
        "command": _find_uv_command(),
        "args": [
            "run",
            "--with", git_ref,
            "--python", "3.11",
            "python", "-m", "taleemabad_data_mcp", "serve",
        ],
        "env": {
            "BIGQUERY_PROJECT": "niete-bq-prod",
            "BIGQUERY_DATASETS": "RUMI_DB,TaleemHub_DB,tbproddb,odk,mcp_audit",
            "GOOGLE_APPLICATION_CREDENTIALS": credentials,
            "TALEEMABAD_USER": user_name,
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


def _bigquery_analytics_config(credentials: str) -> dict:
    """Build the bigquery-analytics MCP server configuration entry."""
    return {
        "command": "npx",
        "args": ["-y", "@ergut/mcp-bigquery-server@latest"],
        "env": {
            "GOOGLE_APPLICATION_CREDENTIALS": credentials,
            "BIGQUERY_PROJECT": "niete-bq-prod",
        },
    }


def _mcp_json_content(credentials: str, user_name: str) -> dict:
    """Build the .mcp.json file content with both MCP servers."""
    return {
        "mcpServers": {
            "taleemabad-data": _mcp_server_config(credentials, user_name),
            "bigquery-analytics": _bigquery_analytics_config(credentials),
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

    # Sync plugin/rules/ from src rules
    if src_rules_dir.exists():
        if plugin_rules_dir.exists():
            shutil.rmtree(plugin_rules_dir)
        shutil.copytree(src_rules_dir, plugin_rules_dir)

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
    click.echo(f"  Next: git add -A && git commit -m 'chore: bump version to v{new_version}' && git push")


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

    # 3. Write .mcp.json to current project directory
    cwd = Path.cwd()
    mcp_path = _write_mcp_json(cwd, credentials_abs, user)
    click.echo(f"MCP config written to {mcp_path}")

    # 4. Write user config env file (includes UV_COMMAND for future init)
    uv_cmd = _find_uv_command()
    env_content = (
        f"TALEEMABAD_USER={user}\n"
        f"GOOGLE_APPLICATION_CREDENTIALS={credentials_abs}\n"
        f"UV_COMMAND={uv_cmd}\n"
    )
    env_path = _env_path()
    env_path.write_text(env_content, encoding="utf-8")
    click.echo(f"User config saved to {env_path}")

    click.echo()
    click.echo("Setup complete! Restart Claude Code to connect.")
    click.echo()
    click.echo("For other projects, run:")
    click.echo("  /taleemabad-init    (in Claude Code)")
    click.echo("  or: python -m taleemabad_data_mcp init  (from CLI)")


def _read_saved_config() -> dict[str, str]:
    """Read saved user config from ~/.claude/taleemabad-data-mcp.env."""
    env_path = _env_path()
    if not env_path.exists():
        return {}
    env_vars = {}
    for line in env_path.read_text(encoding="utf-8").strip().split("\n"):
        if "=" in line:
            key, value = line.split("=", 1)
            env_vars[key] = value
    return env_vars


@main.command()
def upgrade() -> None:
    """Update rules and MCP config using your saved credentials.

    Run this after updating the package. No need to re-enter your name
    or credentials path — they are read from your first setup.
    """
    saved = _read_saved_config()
    user_name = saved.get("TALEEMABAD_USER")
    credentials = saved.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not user_name or not credentials:
        click.echo(
            "Error: no saved config found. Run setup first:\n"
            '  python -m taleemabad_data_mcp setup --user "Name" '
            "--credentials /path/to/key.json",
            err=True,
        )
        sys.exit(1)

    if not Path(credentials).exists():
        click.echo(
            f"Error: saved credentials file not found: {credentials}\n"
            "Re-run setup with the correct path.",
            err=True,
        )
        sys.exit(1)

    # Copy rules
    src_rules = _bundled_rules_dir()
    dest_rules = _rules_dest()
    if dest_rules.exists():
        shutil.rmtree(dest_rules)
    shutil.copytree(src_rules, dest_rules)
    click.echo(f"Rules updated in {dest_rules}")

    # Update .mcp.json in current project directory
    cwd = Path.cwd()
    mcp_json_path = cwd / ".mcp.json"
    if mcp_json_path.exists():
        _write_mcp_json(cwd, credentials, user_name)
        click.echo(f"MCP config updated in {mcp_json_path}")
    else:
        click.echo("No .mcp.json in current directory — run 'init' to create one.")

    from taleemabad_data_mcp import __version__

    click.echo()
    click.echo(f"Upgrade complete! Now running v{__version__}")
    click.echo("Restart Claude Code and run /mcp to verify.")


@main.command()
def init() -> None:
    """Add .mcp.json to the current project directory.

    Run this in any project where you want the Taleemabad data MCP available.
    Reads your credentials from the setup config.
    """
    saved = _read_saved_config()
    user_name = saved.get("TALEEMABAD_USER", "unknown")
    credentials = saved.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    if not credentials or not user_name:
        click.echo("Error: run setup first.", err=True)
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

    sp.run([sys.executable, "-m", "streamlit", "run", str(dashboard_app)], check=False)

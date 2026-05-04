#!/usr/bin/env python3
"""Taleemabad Data Plugin — cross-platform session-start hook.

Downloads latest governance rules into the plugin's rules/ directory.
Pure stdlib — no third-party dependencies required.

Flow:
  1. Export TALEEMABAD_USER from saved env file
  2. If rules were checked <6 hours ago: skip network call
  3. Otherwise: check latest tag, download rules/ via shallow clone
  4. Fallback: plugin ships with rules/ already — no sync needed

Set TALEEMABAD_PIN_VERSION=v0.17.5 to lock to a specific version.
Delete ~/.claude/taleemabad-rules-version to force immediate refresh.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_URL = "https://github.com/Orenda-Project/taleemabad-data-mcp.git"
CHECK_INTERVAL = 21600  # 6 hours in seconds

# Paths
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
VERSION_FILE = CLAUDE_DIR / "taleemabad-rules-version"
ENV_FILE = CLAUDE_DIR / "taleemabad-data-mcp.env"
RULES_PATH_FILE = CLAUDE_DIR / "taleemabad-rules-path"
HOOK_LOG = CLAUDE_DIR / "taleemabad-hook.log"
DOCTOR_SENTINEL = CLAUDE_DIR / "taleemabad-doctor-needed"

# Set up file logging (never stdout — hooks are fire-and-forget)
logging.basicConfig(
    filename=str(HOOK_LOG),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("taleemabad-hook")


def _export_user_env() -> None:
    """Read TALEEMABAD_USER from env file and set in current process."""
    if not ENV_FILE.exists():
        return
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").strip().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                if key.strip() == "TALEEMABAD_USER" and value.strip():
                    os.environ["TALEEMABAD_USER"] = value.strip()
    except Exception as e:
        log.warning("Failed to read env file: %s", e)


def _find_plugin_dir() -> Path | None:
    """Locate the plugin directory."""
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if env_root:
        p = Path(env_root)
        if p.is_dir():
            return p

    # Search the plugin cache
    cache_base = CLAUDE_DIR / "plugins" / "cache" / "Orenda-Project" / "taleemabad-data"
    if cache_base.is_dir():
        for d in sorted(cache_base.iterdir(), reverse=True):
            if (d / ".claude-plugin").is_dir():
                return d

    return None


def _is_recently_checked() -> bool:
    """Check if version file was modified less than CHECK_INTERVAL seconds ago."""
    if not VERSION_FILE.exists():
        return False
    try:
        age = time.time() - VERSION_FILE.stat().st_mtime
        return age < CHECK_INTERVAL
    except Exception:
        return False


def _run_git(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess | None:
    """Run a git command with timeout. Returns None on failure."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        return subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        log.warning("git command failed: %s", e)
        return None


def _get_latest_tag() -> str | None:
    """Get the latest semver tag from the remote repo."""
    result = _run_git(["ls-remote", "--tags", REPO_URL, "v*"], timeout=15)
    if result is None or result.returncode != 0:
        return None

    import re
    tags: list[str] = []
    for line in result.stdout.strip().splitlines():
        # Extract tag name from refs/tags/vX.Y.Z
        match = re.search(r"refs/tags/(v\d+\.\d+\.\d+)$", line)
        if match:
            tags.append(match.group(1))

    if not tags:
        return None

    # Sort by semver (major, minor, patch) descending
    def _ver_key(tag: str) -> tuple[int, ...]:
        return tuple(int(x) for x in tag.lstrip("v").split("."))

    tags.sort(key=_ver_key, reverse=True)
    return tags[0]


def _download_rules(tag: str, dest: Path) -> bool:
    """Download rules/, agents/, commands/, and hooks/ from a specific tag.

    Syncs all plugin-distributed directories so users get new agents,
    commands, and hook updates automatically — not just rule files.
    """
    import shutil
    import tempfile

    tmp_dir = Path(tempfile.mkdtemp(prefix="taleemabad-"))
    plugin_dir = dest.parent  # dest is plugin_dir/rules
    try:
        repo_dir = tmp_dir / "repo"
        result = _run_git([
            "clone", "--depth", "1", "--branch", tag,
            "--no-checkout", "--quiet", REPO_URL, str(repo_dir),
        ], timeout=30)
        if result is None or result.returncode != 0:
            return False

        # Checkout all plugin-distributed directories
        result = _run_git(
            ["-C", str(repo_dir), "checkout", tag, "--",
             "rules/", "agents/", "commands/", "hooks/"],
            timeout=10,
        )
        if result is None or result.returncode != 0:
            # Fallback: at minimum sync rules/ (older tags may not have all dirs)
            result = _run_git(
                ["-C", str(repo_dir), "checkout", tag, "--", "rules/"],
                timeout=10,
            )
            if result is None or result.returncode != 0:
                return False

        src_rules = repo_dir / "rules"
        if not (src_rules / "index.md").exists():
            return False

        # Sync rules/
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(str(src_rules), str(dest))

        # Sync agents/ (new agents like query-fixer, system-doctor)
        src_agents = repo_dir / "agents"
        if src_agents.is_dir():
            dst_agents = plugin_dir / "agents"
            if dst_agents.exists():
                shutil.rmtree(dst_agents)
            shutil.copytree(str(src_agents), str(dst_agents))
            log.info("Agents synced from %s", tag)

        # Sync commands/ (new commands like doctor.md)
        src_commands = repo_dir / "commands"
        if src_commands.is_dir():
            dst_commands = plugin_dir / "commands"
            if dst_commands.exists():
                shutil.rmtree(dst_commands)
            shutil.copytree(str(src_commands), str(dst_commands))
            log.info("Commands synced from %s", tag)

        # Sync hooks/ (but don't overwrite the currently running hook)
        src_hooks = repo_dir / "hooks"
        if src_hooks.is_dir():
            dst_hooks = plugin_dir / "hooks"
            for src_file in src_hooks.rglob("*"):
                if src_file.is_file():
                    rel = src_file.relative_to(src_hooks)
                    dst_file = dst_hooks / rel
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(str(src_file), str(dst_file))
                    except (PermissionError, OSError):
                        # File may be locked (currently running) — skip
                        log.info("Skipped locked hook file: %s", rel)
            log.info("Hooks synced from %s", tag)

        VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        VERSION_FILE.write_text(tag, encoding="utf-8")
        return True
    except Exception as e:
        log.warning("Download failed: %s", e)
        return False
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


def _touch_version() -> None:
    """Update version file's mtime to record last-checked time."""
    try:
        VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        if VERSION_FILE.exists():
            VERSION_FILE.touch()
        else:
            VERSION_FILE.write_text("unknown", encoding="utf-8")
    except Exception:
        pass


def _write_rules_path(rules_dest: Path) -> None:
    """Write the rules path pointer file."""
    if (rules_dest / "index.md").exists():
        try:
            RULES_PATH_FILE.parent.mkdir(parents=True, exist_ok=True)
            RULES_PATH_FILE.write_text(str(rules_dest), encoding="utf-8")
        except Exception as e:
            log.warning("Failed to write rules path: %s", e)


def _cleanup_old_global_rules() -> None:
    """Remove old global rules that bypass agent governance."""
    old_rules = CLAUDE_DIR / "rules" / "taleemabad"
    if old_rules.is_dir():
        import shutil
        try:
            shutil.rmtree(old_rules)
        except Exception:
            pass


def _check_health(plugin_dir: Path, rules_dest: Path) -> list[str]:
    """Check for common issues and return list of symptom IDs."""
    symptoms: list[str] = []

    if not ENV_FILE.exists():
        symptoms.append("user_env_missing")
    elif ENV_FILE.exists():
        content = ENV_FILE.read_text(encoding="utf-8")
        if "${" in content:
            symptoms.append("user_env_unexpanded")

    if not RULES_PATH_FILE.exists():
        symptoms.append("rules_path_missing")
    elif RULES_PATH_FILE.exists():
        rp = RULES_PATH_FILE.read_text(encoding="utf-8").strip()
        if not Path(rp).is_dir():
            symptoms.append("rules_path_missing")

    return symptoms


def main() -> None:
    """Main hook logic."""
    try:
        log.info("Session-start hook running")

        _export_user_env()

        plugin_dir = _find_plugin_dir()
        if not plugin_dir:
            log.info("Plugin directory not found, skipping")
            return

        rules_dest = plugin_dir / "rules"

        # Write rules path immediately (before network update)
        _write_rules_path(rules_dest)

        # Clean up old global rules
        _cleanup_old_global_rules()

        # Respect version pin — skip network update but still run health checks
        if os.environ.get("TALEEMABAD_PIN_VERSION"):
            log.info("Version pinned, skipping update")
            symptoms = _check_health(plugin_dir, rules_dest)
            if symptoms:
                DOCTOR_SENTINEL.parent.mkdir(parents=True, exist_ok=True)
                DOCTOR_SENTINEL.write_text("\n".join(symptoms), encoding="utf-8")
                log.warning("Health issues detected: %s", symptoms)
            elif DOCTOR_SENTINEL.exists():
                DOCTOR_SENTINEL.unlink(missing_ok=True)
            return

        # Skip if recently checked and rules exist
        if (rules_dest / "index.md").exists() and _is_recently_checked():
            log.info("Rules fresh, skipping network check")
            # Still run health checks
            symptoms = _check_health(plugin_dir, rules_dest)
            if symptoms:
                DOCTOR_SENTINEL.parent.mkdir(parents=True, exist_ok=True)
                DOCTOR_SENTINEL.write_text("\n".join(symptoms), encoding="utf-8")
                log.warning("Health issues detected: %s", symptoms)
            return

        current = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "none"
        latest = _get_latest_tag()

        if latest and latest != current:
            if _download_rules(latest, rules_dest):
                log.info("Rules updated to %s", latest)
                print(f"[Taleemabad Data] Rules updated to {latest}")
            else:
                _touch_version()
        elif latest:
            _touch_version()
        else:
            _touch_version()

        # Update path file again — rules may have been downloaded to a new location
        _write_rules_path(rules_dest)

        if not (rules_dest / "index.md").exists():
            log.warning("Governance rules not available in %s", rules_dest)
            print(f"[Taleemabad Data] WARNING: Governance rules not available in {rules_dest}")

        # Health check — write sentinel for system-doctor
        symptoms = _check_health(plugin_dir, rules_dest)
        if symptoms:
            DOCTOR_SENTINEL.parent.mkdir(parents=True, exist_ok=True)
            DOCTOR_SENTINEL.write_text("\n".join(symptoms), encoding="utf-8")
            log.warning("Health issues detected: %s", symptoms)
        elif DOCTOR_SENTINEL.exists():
            DOCTOR_SENTINEL.unlink(missing_ok=True)

        log.info("Session-start hook completed")

    except Exception as e:
        log.error("Hook failed: %s", e, exc_info=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Auto-update Taleemabad Data Plugin on session start
# Uses .current-version file to avoid git describe / detached HEAD issues
# Set TALEEMABAD_PIN_VERSION env var to skip updates and stay on current version

PLUGIN_DIR="${HOME}/.claude/plugins/taleemabad-data"

# Respect pin — if user has pinned a version, skip update silently
if [ -n "$TALEEMABAD_PIN_VERSION" ]; then
  exit 0
fi

# Must be inside the plugin directory
if [ ! -d "$PLUGIN_DIR" ]; then
  exit 0
fi

cd "$PLUGIN_DIR" || exit 0

# Fetch latest tags quietly — if network fails, continue with current version
git fetch --tags --quiet 2>/dev/null || exit 0

# Find latest semantic version tag
LATEST=$(git tag -l 'v*' --sort=-v:refname 2>/dev/null | head -1)
CURRENT=$(cat .current-version 2>/dev/null || echo "none")

# No tags found — nothing to update
if [ -z "$LATEST" ]; then
  exit 0
fi

# Already on latest — nothing to do
if [ "$LATEST" = "$CURRENT" ]; then
  exit 0
fi

# Update to latest tag.
# NOTE: `git checkout <tag>` intentionally creates a detached HEAD — this is expected.
# The plugin directory is a read-only, auto-managed clone. Version tracking uses
# .current-version, not git describe. "HEAD detached at v1.0.0" in this dir is normal.
git checkout "$LATEST" --quiet 2>/dev/null
if [ $? -eq 0 ]; then
  echo "$LATEST" > .current-version
  # Reinstall Python package after update
  "${HOME}/.claude/taleemabad-venv/bin/pip" install \
    --quiet --force-reinstall \
    "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@${LATEST}" 2>/dev/null
  echo "[Taleemabad Data] Updated to ${LATEST}"
fi

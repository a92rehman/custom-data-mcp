#!/usr/bin/env bash
# Auto-update Taleemabad Data Plugin on session start
# - Checks for new git tags and updates plugin cache
# - Syncs governance rules to ~/.claude/rules/taleemabad/ every session
# Set TALEEMABAD_PIN_VERSION env var to skip updates and stay on current version

# Use CLAUDE_PLUGIN_ROOT if available, otherwise try common paths
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$PLUGIN_DIR" ]; then
  # Fallback: search in plugin cache
  for d in "${HOME}/.claude/plugins/cache/Orenda-Project/taleemabad-data"/*; do
    if [ -d "$d/.claude-plugin" ]; then
      PLUGIN_DIR="$d"
      break
    fi
  done
fi

# Must have a valid plugin directory
if [ -z "$PLUGIN_DIR" ] || [ ! -d "$PLUGIN_DIR" ]; then
  exit 0
fi

RULES_SRC="${PLUGIN_DIR}/rules"
RULES_DEST="${HOME}/.claude/rules/taleemabad"

# --- Always sync rules (even if version unchanged) ---
# This ensures rules are present even if user deleted them or ran setup before this fix
if [ -d "$RULES_SRC" ]; then
  mkdir -p "$(dirname "$RULES_DEST")"
  # Only copy if source is newer or dest doesn't exist
  if [ ! -d "$RULES_DEST" ] || [ "$RULES_SRC/index.md" -nt "$RULES_DEST/index.md" ] 2>/dev/null; then
    rm -rf "$RULES_DEST"
    cp -r "$RULES_SRC" "$RULES_DEST"
  fi
fi

# Respect pin — if user has pinned a version, skip version update (rules still sync above)
if [ -n "$TALEEMABAD_PIN_VERSION" ]; then
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

  # Sync rules after version update
  if [ -d "$RULES_SRC" ]; then
    rm -rf "$RULES_DEST"
    cp -r "$RULES_SRC" "$RULES_DEST"
  fi

  echo "[Taleemabad Data] Updated to ${LATEST} — rules synced"
fi

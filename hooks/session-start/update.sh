#!/usr/bin/env bash
# Auto-update Taleemabad Data Plugin on session start
# - Checks for new git tags and updates plugin cache
# - Syncs governance rules to ~/.claude/rules/taleemabad/ every session
# - Exports TALEEMABAD_USER from saved env file
# Set TALEEMABAD_PIN_VERSION env var to skip updates and stay on current version

# Use CLAUDE_PLUGIN_ROOT if available, otherwise try common paths
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$PLUGIN_DIR" ]; then
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
ENV_FILE="${HOME}/.claude/taleemabad-data-mcp.env"

# --- Export TALEEMABAD_USER from saved env file ---
if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r key value; do
    if [ "$key" = "TALEEMABAD_USER" ] && [ -n "$value" ]; then
      export TALEEMABAD_USER="$value"
    fi
  done < "$ENV_FILE"
fi

# --- Sync rules function (reused after update) ---
sync_rules() {
  if [ -d "$RULES_SRC" ]; then
    mkdir -p "$(dirname "$RULES_DEST")"
    rm -rf "$RULES_DEST"
    cp -r "$RULES_SRC" "$RULES_DEST"

    # Verify sync succeeded — index.md must exist
    if [ ! -f "$RULES_DEST/index.md" ]; then
      echo "[Taleemabad Data] WARNING: Rule sync failed — index.md not found at $RULES_DEST"
    fi
  fi
}

# --- Always sync rules (every session, ensures new files are picked up) ---
sync_rules

# Respect pin
if [ -n "$TALEEMABAD_PIN_VERSION" ]; then
  exit 0
fi

cd "$PLUGIN_DIR" || exit 0

# Fetch latest tags quietly
git fetch --tags --quiet 2>/dev/null || exit 0

LATEST=$(git tag -l 'v*' --sort=-v:refname 2>/dev/null | head -1)
CURRENT=$(cat .current-version 2>/dev/null || echo "none")

if [ -z "$LATEST" ]; then
  exit 0
fi

if [ "$LATEST" = "$CURRENT" ]; then
  exit 0
fi

# Update plugin cache to latest tag
git checkout "$LATEST" --quiet 2>/dev/null
if [ $? -eq 0 ]; then
  echo "$LATEST" > .current-version

  # Sync rules after update
  sync_rules

  echo "[Taleemabad Data] Updated to ${LATEST}"
fi

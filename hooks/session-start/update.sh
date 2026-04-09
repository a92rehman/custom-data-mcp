#!/usr/bin/env bash
# Auto-update Taleemabad Data Plugin on session start
# - Checks for new git tags and updates plugin cache
# - Syncs governance rules to ~/.claude/rules/taleemabad/ every session
# - Updates the venv package when a new version is released
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
VENV_DIR="${HOME}/.claude/taleemabad-venv"

# --- Always sync rules (even if version unchanged) ---
if [ -d "$RULES_SRC" ]; then
  mkdir -p "$(dirname "$RULES_DEST")"
  if [ ! -d "$RULES_DEST" ] || [ "$RULES_SRC/index.md" -nt "$RULES_DEST/index.md" ] 2>/dev/null; then
    rm -rf "$RULES_DEST"
    cp -r "$RULES_SRC" "$RULES_DEST"
  fi
fi

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

  # Sync rules
  if [ -d "$RULES_SRC" ]; then
    rm -rf "$RULES_DEST"
    cp -r "$RULES_SRC" "$RULES_DEST"
  fi

  # Update venv package if venv exists
  if [ -d "$VENV_DIR" ]; then
    if [ -f "$VENV_DIR/Scripts/pip.exe" ]; then
      PIP="$VENV_DIR/Scripts/pip.exe"
    elif [ -f "$VENV_DIR/bin/pip" ]; then
      PIP="$VENV_DIR/bin/pip"
    fi
    if [ -n "$PIP" ]; then
      "$PIP" install --quiet --force-reinstall \
        "git+https://github.com/Orenda-Project/taleemabad-data-mcp.git@${LATEST}" 2>/dev/null
    fi
  fi

  echo "[Taleemabad Data] Updated to ${LATEST}"
fi

#!/usr/bin/env bash
# Taleemabad Data Plugin — Unix Installer
# Two-step install (download script, then run) — not curl|bash
set -e

REPO="https://github.com/Orenda-Project/taleemabad-data-mcp.git"
PLUGIN_DIR="${HOME}/.claude/plugins/taleemabad-data"
VENV_DIR="${HOME}/.claude/taleemabad-venv"
ENV_FILE="${HOME}/.claude/taleemabad-data-mcp.env"
export PLUGIN_DIR

echo ""
echo "=== Taleemabad Data Plugin Installer ==="
echo ""

# --- Prerequisites check ---
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found. Install Python 3.11+"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "ERROR: git not found. Install git"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "WARN: node not found. bigquery-analytics MCP will not work."; }

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
  echo "✓ Python ${PYTHON_VERSION}"
else
  echo "ERROR: Python 3.11+ required. Found ${PYTHON_VERSION}"; exit 1
fi

# --- Detect existing install ---
if [ -d "$PLUGIN_DIR" ]; then
  echo "Existing install detected at ${PLUGIN_DIR}"
  echo "Running upgrade instead..."
  cd "$PLUGIN_DIR"
  git fetch --tags --quiet
  LATEST=$(git tag -l 'v*' --sort=-v:refname | head -1)
  git checkout "${LATEST:-main}" --quiet
  [ -n "$LATEST" ] && echo "$LATEST" > .current-version
  "${VENV_DIR}/bin/pip" install --quiet --force-reinstall \
    "git+${REPO}@${LATEST:-main}[dashboard]"
  # Re-substitute .mcp.json in case template changed in this release
  if [ -f "$ENV_FILE" ]; then
    SAVED_USER=$(grep '^TALEEMABAD_USER=' "$ENV_FILE" | cut -d= -f2- | tr -d '"')
    SAVED_CREDS=$(grep '^GOOGLE_APPLICATION_CREDENTIALS=' "$ENV_FILE" | cut -d= -f2- | tr -d '"')
    if [ -n "$SAVED_USER" ] && [ -n "$SAVED_CREDS" ]; then
      export _USER="$SAVED_USER"
      export _CREDS="$SAVED_CREDS"
      python3 - << 'PYEOF'
import json, os, sys
template = open(os.path.join(os.environ['PLUGIN_DIR'], '.mcp.json')).read()
result = template \
    .replace('${HOME}', os.environ['HOME']) \
    .replace('${TALEEMABAD_CREDENTIALS}', os.environ['_CREDS']) \
    .replace('${TALEEMABAD_USER}', os.environ['_USER'])
open(os.path.join(os.environ['PLUGIN_DIR'], '.mcp.json'), 'w').write(result)
PYEOF
      echo "✓ MCP config refreshed"
    fi
  fi
  echo "✓ Upgraded to ${LATEST:-latest}"
  exit 0
fi

# --- Detect old rules-based setup ---
OLD_RULES="${HOME}/.claude/rules/taleemabad"
if [ -d "$OLD_RULES" ]; then
  echo ""
  echo "Old setup detected at ~/.claude/rules/taleemabad/"
  read -p "Migrate to plugin? Old rules will be removed. [y/N] " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    MIGRATE_OLD=true
  fi
fi

# --- Clone plugin ---
echo "Cloning plugin to ${PLUGIN_DIR}..."
git clone --quiet "$REPO" "$PLUGIN_DIR"
cd "$PLUGIN_DIR"
LATEST=$(git tag -l 'v*' --sort=-v:refname | head -1)
if [ -n "$LATEST" ]; then
  git checkout "$LATEST" --quiet
  echo "$LATEST" > .current-version
  echo "✓ Pinned to ${LATEST}"
fi

# --- Create venv ---
echo "Creating Python venv at ${VENV_DIR}..."
python3 -m venv "$VENV_DIR"
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip

# --- Install MCP server ---
echo "Installing taleemabad-data-mcp..."
"${VENV_DIR}/bin/pip" install --quiet \
  "git+${REPO}@${LATEST:-main}[dashboard]"
echo "✓ MCP server installed"

# --- Prompt for credentials ---
echo ""
echo "=== Configuration ==="
read -p "Your name (for audit logs): " TALEEMABAD_USER
read -e -p "Path to GCP service account JSON: " CREDENTIALS_PATH
CREDENTIALS_PATH="${CREDENTIALS_PATH/#\~/$HOME}"

if [ ! -f "$CREDENTIALS_PATH" ]; then
  echo "ERROR: File not found: ${CREDENTIALS_PATH}"; exit 1
fi

# --- Save config ---
cat > "$ENV_FILE" << EOF
TALEEMABAD_USER="${TALEEMABAD_USER}"
GOOGLE_APPLICATION_CREDENTIALS="${CREDENTIALS_PATH}"
EOF
chmod 600 "$ENV_FILE"
echo "✓ Config saved to ${ENV_FILE}"

# --- Write final .mcp.json with substituted values ---
export _USER="$TALEEMABAD_USER"
export _CREDS="$CREDENTIALS_PATH"
python3 - << 'PYEOF'
import json, os, sys
template = open(os.path.join(os.environ['PLUGIN_DIR'], '.mcp.json')).read()
result = template \
    .replace('${HOME}', os.environ['HOME']) \
    .replace('${TALEEMABAD_CREDENTIALS}', os.environ['_CREDS']) \
    .replace('${TALEEMABAD_USER}', os.environ['_USER'])
open(os.path.join(os.environ['PLUGIN_DIR'], '.mcp.json'), 'w').write(result)
PYEOF
echo "✓ MCP config written"

# --- Migrate old setup ---
if [ "${MIGRATE_OLD}" = "true" ]; then
  rm -rf "$OLD_RULES"
  echo "✓ Removed old rules at ~/.claude/rules/taleemabad/"
  echo "ACTION REQUIRED: Remove the 'taleemabad-data' key from ~/.claude/settings.json manually"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Plugin installed at: ${PLUGIN_DIR}"
echo "Version: ${LATEST:-latest}"
echo ""
echo "Restart Claude Code to activate the plugin."
echo "Ask 'what version of taleemabad data am I running?' to verify."

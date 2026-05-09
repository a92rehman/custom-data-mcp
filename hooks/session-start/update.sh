#!/usr/bin/env bash
# Custom Data Plugin — session-start hook
# Downloads latest governance rules into the plugin's rules/ directory.
# Rules are NOT placed in ~/.claude/rules/ — that would inject them into the
# parent session's context, causing it to bypass the agent's Read→Clarify→Execute flow.
#
# Flow:
#   1. Export CUSTOM_DATA_USER from saved env file
#   2. If rules were checked <6 hours ago: skip network call
#   3. Otherwise: check latest tag, download rules/ via shallow clone
#   4. Fallback: plugin ships with rules/ already — no sync needed
#
# Set CUSTOM_DATA_PIN_VERSION=v0.17.5 to lock to a specific version.
# Delete ~/.claude/custom-data-rules-version to force immediate refresh.

REPO_URL="https://github.com/a92rehman/custom-data-mcp.git"
VERSION_FILE="${HOME}/.claude/custom-data-rules-version"
ENV_FILE="${HOME}/.claude/custom-data-mcp.env"
CHECK_INTERVAL=21600  # 6 hours in seconds

# Never prompt for credentials — fail fast if not available
export GIT_TERMINAL_PROMPT=0

# --- Export CUSTOM_DATA_USER from saved env file ---
if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r key value; do
    if [ "$key" = "CUSTOM_DATA_USER" ] && [ -n "$value" ]; then
      export CUSTOM_DATA_USER="$value"
    fi
  done < "$ENV_FILE"
fi

# --- Locate plugin directory ---
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$PLUGIN_DIR" ]; then
  for d in "${HOME}/.claude/plugins/cache/a92rehman/custom-data"/*; do
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

RULES_DEST="${PLUGIN_DIR}/rules"
RULES_PATH_FILE="${HOME}/.claude/custom-data-rules-path"

# --- Write rules path immediately (before network update) ---
# The data-analyst agent needs this to find rules on user machines.
# Write it early so even if the network update is slow, the agent can
# find the bundled rules that ship with the plugin.
if [ -f "$RULES_DEST/index.md" ]; then
  echo "$RULES_DEST" > "$RULES_PATH_FILE"
fi

# --- Clean up old global rules (from previous versions) ---
# These were injected into parent session context, causing governance bypass.
OLD_GLOBAL_RULES="${HOME}/.claude/rules/custom-data"
if [ -d "$OLD_GLOBAL_RULES" ]; then
  rm -rf "$OLD_GLOBAL_RULES"
fi

# --- Check if version file was modified recently ---
is_recently_checked() {
  [ ! -f "$VERSION_FILE" ] && return 1

  local now file_time age
  now=$(date +%s 2>/dev/null)
  [ -z "$now" ] && return 1

  if stat --version >/dev/null 2>&1; then
    file_time=$(stat -c %Y "$VERSION_FILE" 2>/dev/null)
  else
    file_time=$(stat -f %m "$VERSION_FILE" 2>/dev/null)
  fi
  [ -z "$file_time" ] && return 1

  age=$((now - file_time))
  [ "$age" -lt "$CHECK_INTERVAL" ]
}

# --- Get latest tag via git ls-remote ---
get_latest_tag() {
  local tmp_tags
  tmp_tags=$(mktemp 2>/dev/null || mktemp -t 'tags')

  git ls-remote --tags "$REPO_URL" 'v*' > "$tmp_tags" 2>/dev/null &
  local pid=$!

  local waited=0
  while kill -0 "$pid" 2>/dev/null && [ "$waited" -lt 15 ]; do
    sleep 1
    waited=$((waited + 1))
  done

  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null
    wait "$pid" 2>/dev/null
    rm -f "$tmp_tags"
    return 1
  fi
  wait "$pid" 2>/dev/null

  local tags
  tags=$(cat "$tmp_tags" 2>/dev/null)
  rm -f "$tmp_tags"
  [ -z "$tags" ] && return 1

  echo "$tags" \
    | sed 's/.*refs\/tags\///' \
    | sed 's/\^{}//' \
    | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' \
    | sort -Vr \
    | head -1
}

# --- Download rules from a specific tag into plugin rules/ ---
download_rules() {
  local tag="$1"
  local tmp_dir
  tmp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'custom-data')

  if ! timeout 20 git clone --depth 1 --branch "$tag" --no-checkout --quiet \
       "$REPO_URL" "${tmp_dir}/repo" 2>/dev/null; then
    rm -rf "$tmp_dir"
    return 1
  fi

  if ! git -C "${tmp_dir}/repo" checkout "$tag" -- rules/ agents/ commands/ hooks/ 2>/dev/null; then
    # Fallback: at minimum sync rules/ (older tags may not have all dirs)
    if ! git -C "${tmp_dir}/repo" checkout "$tag" -- rules/ 2>/dev/null; then
      rm -rf "$tmp_dir"
      return 1
    fi
  fi

  if [ ! -f "${tmp_dir}/repo/rules/index.md" ]; then
    rm -rf "$tmp_dir"
    return 1
  fi

  # Replace plugin's rules/ directory with downloaded version
  rm -rf "$RULES_DEST"
  cp -r "${tmp_dir}/repo/rules" "$RULES_DEST"

  # Sync agents/ (new agents like query-fixer, system-doctor)
  if [ -d "${tmp_dir}/repo/agents" ]; then
    rm -rf "${PLUGIN_DIR}/agents"
    cp -r "${tmp_dir}/repo/agents" "${PLUGIN_DIR}/agents"
  fi

  # Sync commands/ (new commands like doctor.md)
  if [ -d "${tmp_dir}/repo/commands" ]; then
    rm -rf "${PLUGIN_DIR}/commands"
    cp -r "${tmp_dir}/repo/commands" "${PLUGIN_DIR}/commands"
  fi

  # Sync hooks/ (copy new files, skip locked ones)
  if [ -d "${tmp_dir}/repo/hooks" ]; then
    cp -r "${tmp_dir}/repo/hooks/"* "${PLUGIN_DIR}/hooks/" 2>/dev/null || true
  fi

  echo "$tag" > "$VERSION_FILE"

  rm -rf "$tmp_dir"
  return 0
}

# --- Touch version file to update last-checked timestamp ---
touch_version() {
  if [ -f "$VERSION_FILE" ]; then
    touch "$VERSION_FILE" 2>/dev/null
  else
    echo "unknown" > "$VERSION_FILE"
  fi
}

# --- Main logic ---

# Respect version pin
if [ -n "$CUSTOM_DATA_PIN_VERSION" ]; then
  exit 0
fi

# Force re-download if agents/ dir is missing (migration from pre-v0.18.0)
# Old hook only synced rules/. New hook syncs agents/, commands/, hooks/ too.
# This ensures existing users get new agents on their next session.
if [ ! -f "${PLUGIN_DIR}/agents/query-fixer.md" ] && [ -f "$VERSION_FILE" ]; then
  rm -f "$VERSION_FILE"
fi

# If rules exist and were checked recently, skip network call
if [ -f "$RULES_DEST/index.md" ] && is_recently_checked; then
  exit 0
fi

CURRENT=$(cat "$VERSION_FILE" 2>/dev/null || echo "none")

LATEST=$(get_latest_tag)

if [ -n "$LATEST" ] && [ "$LATEST" != "$CURRENT" ]; then
  if download_rules "$LATEST"; then
    echo "[Custom Data] Rules updated to ${LATEST}"
  else
    touch_version
  fi
elif [ -n "$LATEST" ]; then
  touch_version
else
  touch_version
fi

if [ ! -f "$RULES_DEST/index.md" ]; then
  echo "[Custom Data] WARNING: Governance rules not available in ${RULES_DEST}"
else
  # Update path file again — rules may have been downloaded to a new location
  echo "$RULES_DEST" > "$RULES_PATH_FILE"
fi

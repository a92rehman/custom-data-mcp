#!/usr/bin/env bash
# Linux/macOS shim to run session-start hook
# Prefers Python (cross-platform), falls back to bash
HOOK_DIR="$(dirname "$0")/$1"

# Try Python first
if command -v python3 >/dev/null 2>&1 && [ -f "$HOOK_DIR/update.py" ]; then
  python3 "$HOOK_DIR/update.py"
  exit 0
elif command -v python >/dev/null 2>&1 && [ -f "$HOOK_DIR/update.py" ]; then
  python "$HOOK_DIR/update.py"
  exit 0
fi

# Fallback to bash
if [ -f "$HOOK_DIR/update.sh" ]; then
  bash "$HOOK_DIR/update.sh"
fi

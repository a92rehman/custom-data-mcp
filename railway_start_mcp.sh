#!/bin/bash
set -e

# MCP Server startup script for Railway deployment.
# This runs the MCP server with HTTP transport — separate from the dashboard.
# The dashboard uses railway_start.sh (unchanged).

# Make the package importable by adding a .pth file to the venv site-packages
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
if [ -n "$SITE_PACKAGES" ]; then
    echo "/app/src" > "${SITE_PACKAGES}/taleemabad_src.pth"
    echo "Added /app/src to ${SITE_PACKAGES}/taleemabad_src.pth"
fi
export PYTHONPATH="${PYTHONPATH}:/app/src"

# Write GCP credentials from env var to file (Railway can't upload files)
echo "Checking for GOOGLE_CREDENTIALS_JSON env var..."
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "$GOOGLE_CREDENTIALS_JSON" > /tmp/credentials.json
    export GOOGLE_APPLICATION_CREDENTIALS=/tmp/credentials.json
    echo "GCP credentials written to /tmp/credentials.json ($(wc -c < /tmp/credentials.json) bytes)"
else
    echo "WARNING: GOOGLE_CREDENTIALS_JSON not set — BigQuery will not be available"
fi

echo "Starting MCP server on port ${PORT:-8000}..."
python -m taleemabad_data_mcp serve-remote

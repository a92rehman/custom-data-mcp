#!/bin/bash
set -e

# Write GCP credentials from env var to file (Railway can't upload files)
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "$GOOGLE_CREDENTIALS_JSON" > /tmp/credentials.json
    export GOOGLE_APPLICATION_CREDENTIALS=/tmp/credentials.json
fi

# Debug: show where we are and what files exist
echo "Working directory: $(pwd)"
echo "Dashboard files:"
ls -la src/taleemabad_data_mcp/dashboard/pages/ 2>/dev/null || echo "pages dir not found at src/"
ls -la taleemabad_data_mcp/dashboard/pages/ 2>/dev/null || echo "pages dir not found at root"

python -m streamlit run src/taleemabad_data_mcp/dashboard/app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true

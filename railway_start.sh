#!/bin/bash
set -e

# Make the package importable by adding a .pth file to the venv site-packages
# This works even when PYTHONPATH is ignored by the venv Python
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
if [ -n "$SITE_PACKAGES" ]; then
    echo "/app/src" > "${SITE_PACKAGES}/taleemabad_src.pth"
    echo "Added /app/src to ${SITE_PACKAGES}/taleemabad_src.pth"
fi
export PYTHONPATH="${PYTHONPATH}:/app/src"

# Write GCP credentials from env var to file (Railway can't upload files)
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "$GOOGLE_CREDENTIALS_JSON" > /tmp/credentials.json
    export GOOGLE_APPLICATION_CREDENTIALS=/tmp/credentials.json
fi

python -m streamlit run src/taleemabad_data_mcp/dashboard/app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true

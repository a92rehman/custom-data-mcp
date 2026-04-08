#!/bin/bash
set -e

# Make the package importable when running directly from source
export PYTHONPATH="${PYTHONPATH}:/app/src"

# Write GCP credentials from env var to file (Railway can't upload files)
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "$GOOGLE_CREDENTIALS_JSON" > /tmp/credentials.json
    export GOOGLE_APPLICATION_CREDENTIALS=/tmp/credentials.json
fi

# === DIAGNOSTICS ===
echo "=== Working directory: $(pwd) ==="
echo "=== Python binary: $(which python) ==="
echo "=== Python version: $(python --version) ==="
echo "=== PYTHONPATH: ${PYTHONPATH} ==="
echo "=== /app/src contents: ==="
ls -la /app/src/ 2>/dev/null || echo "/app/src not found"
echo "=== /app/src/taleemabad_data_mcp contents: ==="
ls -la /app/src/taleemabad_data_mcp/ 2>/dev/null || echo "package dir not found"
echo "=== pip show taleemabad-data-mcp: ==="
python -m pip show taleemabad-data-mcp 2>/dev/null || echo "package NOT installed"
echo "=== python -c import test: ==="
python -c "import taleemabad_data_mcp; print('import OK:', taleemabad_data_mcp.__file__)" 2>&1
echo "=== sys.path: ==="
python -c "import sys; [print(p) for p in sys.path]"
echo "=== END DIAGNOSTICS ==="

python -m streamlit run src/taleemabad_data_mcp/dashboard/app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true

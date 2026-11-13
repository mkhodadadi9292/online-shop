#!/bin/bash
# Installs backend dependencies using uv (faster + more robust HTTP stack than pip)
# with a high per-request timeout and a retry loop, because the network to PyPI
# in this environment is intermittent (reads occasionally time out).
set -u

cd "$(dirname "$0")"
VENV_PY=".venv/bin/python"

export UV_HTTP_TIMEOUT=300
export UV_INDEX_STRATEGY=unsafe-best-match

MAX_ATTEMPTS=15

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  echo "=== attempt $attempt ==="
  if uv pip install --python "$VENV_PY" -r requirements-dev.txt && \
     uv pip install --python "$VENV_PY" -e shared; then
    echo "ALL_DEPS_INSTALLED"
    exit 0
  fi
  echo "attempt $attempt failed; retrying in 2s"
  sleep 2
done

echo "FAILED after $MAX_ATTEMPTS attempts"
exit 1

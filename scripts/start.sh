#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f frontend/dist/index.html ]; then
  echo 'Build the frontend first: cd frontend && npm ci && npm run build' >&2
  exit 1
fi
exec "${PYTHON:-.venv/bin/python}" -m uvicorn backend.app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}" --workers 1 --no-access-log --timeout-keep-alive 5

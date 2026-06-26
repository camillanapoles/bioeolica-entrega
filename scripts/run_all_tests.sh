#!/usr/bin/env bash
# Workflow arrastavel: roda todas as suites (root + lab1 + lab2).
# Exit code != 0 se qualquer suite falhar (M1/M5).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
cd "$ROOT"

FAIL=0
echo "=== ROOT smoke ==="
pytest tests/ -p no:cacheprovider -q || FAIL=1
echo "=== Lab1 ==="
( cd workspace/lab1-material-papel-mache-grafite && pytest tests/ -p no:cacheprovider -q ) || FAIL=1
echo "=== Lab2 ==="
( cd workspace/lab2-gerador-eolico-savonius && pytest tests/ -p no:cacheprovider -q ) || FAIL=1

if [ "$FAIL" = "1" ]; then
  echo "::error::suite falhou"
  exit 1
fi
echo "✅ TODAS AS SUITES PASSARAM"

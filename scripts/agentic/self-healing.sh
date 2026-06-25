#!/bin/bash
# Self-healing script for agentic tasks
# Usage: ./self-healing.sh <task_id> [error_message]

TASK_ID="${1:-unknown}"
ERROR_MSG="${2:-unknown error}"

echo "SELF-HEALING >> Task ${TASK_ID}"
echo "SELF-HEALING >> Error: ${ERROR_MSG}"
echo "SELF-HEALING >> Max attempts: 3"

ATTEMPT_FILE=".agentic/retry_${TASK_ID}.count"
mkdir -p .agentic

if [ ! -f "$ATTEMPT_FILE" ]; then
    echo 1 > "$ATTEMPT_FILE"
    echo "SELF-HEALING >> Attempt 1/3 — Re-executando..."
    exit 0
fi

ATTEMPT=$(cat "$ATTEMPT_FILE")
if [ "$ATTEMPT" -ge 3 ]; then
    echo "SELF-HEALING >> Max attempts reached. Escalando para humano."
    rm -f "$ATTEMPT_FILE"
    exit 1
fi

echo $((ATTEMPT + 1)) > "$ATTEMPT_FILE"
echo "SELF-HEALING >> Attempt $((ATTEMPT + 1))/3"
exit 0

#!/bin/bash
# Script to initialize a new workspace from template

set -euo pipefail

TEMPLATE_DIR="$(dirname "$0")"
WORKSPACE_NAME="${1:-new_workspace}"

if [ -d "$WORKSPACE_NAME" ]; then
    echo "Error: Directory $WORKSPACE_NAME already exists."
    exit 1
fi

cp -r "$TEMPLATE_DIR" "$WORKSPACE_NAME"
echo "Workspace '$WORKSPACE_NAME' created from template."
echo "Edit $WORKSPACE_NAME/config.yaml to customize."

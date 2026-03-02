#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

bash "$SCRIPT_DIR/infra_down.sh" || true

info "Removing local runtime artifacts."
rm -rf "$POSTGRES_DATA_DIR"
rm -f "$POSTGRES_LOG_FILE" "$REDIS_LOG_FILE" "$REDIS_PID_FILE"
rm -rf "$ROOT_DIR/.pytest_cache" "$ROOT_DIR/.mypy_cache" "$ROOT_DIR/.ruff_cache"
rm -f "$ROOT_DIR/.coverage"

find "$ROOT_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$ROOT_DIR" -type f -name '*.pyc' -delete

info "Clean complete."


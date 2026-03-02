#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

require_command brew
require_command redis-server
require_command redis-cli

mkdir -p "$ROOT_DIR"

if [[ ! -d "$POSTGRES_DATA_DIR" ]]; then
  info "Initializing Postgres data directory at $POSTGRES_DATA_DIR."
  "$(postgres_bin initdb)" -D "$POSTGRES_DATA_DIR"
fi

if postgres_running; then
  info "Postgres is already running."
else
  info "Starting Postgres."
  "$(postgres_bin pg_ctl)" -D "$POSTGRES_DATA_DIR" -l "$POSTGRES_LOG_FILE" start
fi

wait_for_postgres
ensure_database_exists

if redis_running; then
  info "Redis is already running."
else
  info "Starting Redis."
  redis-server --daemonize yes --dir "$ROOT_DIR" --logfile "$REDIS_LOG_FILE" --pidfile "$REDIS_PID_FILE"
fi

redis_running || fail "Redis did not start successfully."
info "Infrastructure is ready."


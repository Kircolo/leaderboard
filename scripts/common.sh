#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POSTGRES_FORMULA="${POSTGRES_FORMULA:-postgresql@16}"
DB_NAME="${LEADERBOARD_DB_NAME:-leaderboard}"
DB_USER="${LEADERBOARD_DB_USER:-$(id -un)}"
POSTGRES_DATA_DIR="${POSTGRES_DATA_DIR:-$ROOT_DIR/.postgres-data}"
POSTGRES_LOG_FILE="${POSTGRES_LOG_FILE:-$ROOT_DIR/.postgres.log}"
REDIS_LOG_FILE="${REDIS_LOG_FILE:-$ROOT_DIR/.redis.log}"
REDIS_PID_FILE="${REDIS_PID_FILE:-$ROOT_DIR/.redis.pid}"
APP_ENV_FILE="${APP_ENV_FILE:-$ROOT_DIR/.env}"
APP_ENV_EXAMPLE_FILE="${APP_ENV_EXAMPLE_FILE:-$ROOT_DIR/.env.example}"
REDIS_URL="${LEADERBOARD_REDIS_URL:-redis://localhost:6379/0}"


info() {
  printf '[leaderboard] %s\n' "$*"
}


fail() {
  printf '[leaderboard] ERROR: %s\n' "$*" >&2
  exit 1
}


require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || fail "Missing required command: $command_name"
}


brew_prefix_for() {
  local formula="$1"
  brew --prefix "$formula" 2>/dev/null || true
}


postgres_bin_dir() {
  local prefix
  prefix="$(brew_prefix_for "$POSTGRES_FORMULA")"
  [[ -n "$prefix" ]] || fail "Homebrew formula '$POSTGRES_FORMULA' is not installed."
  [[ -x "$prefix/bin/initdb" ]] || fail "Postgres binaries were not found under '$prefix/bin'."
  printf '%s/bin' "$prefix"
}


postgres_bin() {
  local bin_dir
  bin_dir="$(postgres_bin_dir)"
  printf '%s/%s' "$bin_dir" "$1"
}


postgres_running() {
  local pg_isready_bin
  pg_isready_bin="$(postgres_bin pg_isready)"
  "$pg_isready_bin" -h 127.0.0.1 -p 5432 >/dev/null 2>&1
}


redis_running() {
  redis-cli ping >/dev/null 2>&1
}


wait_for_postgres() {
  local pg_isready_bin attempts
  pg_isready_bin="$(postgres_bin pg_isready)"
  attempts=0
  until "$pg_isready_bin" -h 127.0.0.1 -p 5432 >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if (( attempts >= 20 )); then
      fail "Postgres did not become ready on localhost:5432."
    fi
    sleep 1
  done
}


ensure_database_exists() {
  local createdb_bin psql_bin
  createdb_bin="$(postgres_bin createdb)"
  psql_bin="$(postgres_bin psql)"

  if ! "$psql_bin" -d postgres -Atqc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q '^1$'; then
    info "Creating database '$DB_NAME'."
    "$createdb_bin" "$DB_NAME"
  fi
}


set_env_var() {
  local file_path="$1"
  local key="$2"
  local value="$3"
  local tmp_file

  tmp_file="$(mktemp)"
  awk -v key="$key" -v value="$value" '
    BEGIN { updated = 0 }
    index($0, key "=") == 1 { print key "=" value; updated = 1; next }
    { print }
    END { if (updated == 0) print key "=" value }
  ' "$file_path" > "$tmp_file"
  mv "$tmp_file" "$file_path"
}


ensure_env_file() {
  local database_url

  if [[ ! -f "$APP_ENV_FILE" ]]; then
    [[ -f "$APP_ENV_EXAMPLE_FILE" ]] || fail "Missing env template: $APP_ENV_EXAMPLE_FILE"
    cp "$APP_ENV_EXAMPLE_FILE" "$APP_ENV_FILE"
    info "Created $APP_ENV_FILE from the example template."
  fi

  database_url="postgresql+asyncpg://${DB_USER}@localhost:5432/${DB_NAME}"
  set_env_var "$APP_ENV_FILE" "LEADERBOARD_DATABASE_URL" "$database_url"
  set_env_var "$APP_ENV_FILE" "LEADERBOARD_REDIS_URL" "$REDIS_URL"
}


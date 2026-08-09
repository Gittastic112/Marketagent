#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="market-intel-restore-drill"
COMPOSE_FILE="$ROOT_DIR/docker-compose.e2e.yml"
BACKUP_ROOT="$(mktemp -d)"
compose=(docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE")

cleanup() {
  "${compose[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$BACKUP_ROOT"
}
trap cleanup EXIT INT TERM

export NEXTAUTH_SECRET="restore-drill-secret-not-for-production"
export LOCAL_AUTH_USERNAME="restore-drill-user"
export LOCAL_AUTH_PASSWORD="restore-drill-password"
export E2E_BACKEND_PORT="${RESTORE_DRILL_BACKEND_PORT:-18020}"
export E2E_FRONTEND_PORT="${RESTORE_DRILL_FRONTEND_PORT:-13020}"

"${compose[@]}" up --build --detach postgres-e2e backend-e2e

for _ in $(seq 1 60); do
  if "${compose[@]}" exec -T backend-e2e alembic current >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
"${compose[@]}" exec -T backend-e2e alembic current
"${compose[@]}" exec -T backend-e2e python scripts/restore_drill_fixture.py seed

BACKUP_ROOT="$BACKUP_ROOT" \
COMPOSE_FILE="$COMPOSE_FILE" \
COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
POSTGRES_SERVICE="postgres-e2e" \
BACKEND_SERVICE="backend-e2e" \
POSTGRES_DB="marketintel_e2e" \
BACKUP_RETENTION_COUNT=1 \
  "$ROOT_DIR/scripts/backup_local.sh"

backup_dir="$(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -name '*-market-intelligence' -print -quit)"
if [[ -z "$backup_dir" ]]; then
  printf 'Restore drill backup directory was not created.\n' >&2
  exit 1
fi

"${compose[@]}" exec -T backend-e2e python scripts/restore_drill_fixture.py clear

COMPOSE_FILE="$COMPOSE_FILE" \
COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
POSTGRES_SERVICE="postgres-e2e" \
BACKEND_SERVICE="backend-e2e" \
FRONTEND_SERVICE="" \
POSTGRES_DB="marketintel_e2e" \
  "$ROOT_DIR/scripts/restore_local.sh" "$backup_dir" --yes-replace-database

for _ in $(seq 1 60); do
  if "${compose[@]}" exec -T backend-e2e python scripts/restore_drill_fixture.py verify >/dev/null 2>&1; then
    printf 'Backup and restore drill passed, including original document bytes.\n'
    exit 0
  fi
  sleep 2
done

"${compose[@]}" logs --tail=120 backend-e2e >&2
printf 'Restore drill verification timed out.\n' >&2
exit 1

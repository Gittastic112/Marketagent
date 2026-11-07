#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
PROJECT_NAME="market-intel-restore-drill-$$-$RANDOM"
COMPOSE_FILE="$ROOT_DIR/docker-compose.recovery.yml"
BACKUP_ROOT="$(mktemp -d)"
export COMPOSE_ENV_FILE=/dev/null
compose=("$DOCKER_BIN" compose --env-file /dev/null -p "$PROJECT_NAME" -f "$COMPOSE_FILE")
started=false
writer_pid=""
cleanup() {
  if [[ -n "$writer_pid" ]]; then
    kill "$writer_pid" >/dev/null 2>&1 || true
    wait "$writer_pid" 2>/dev/null || true
  fi
  if [[ "$started" == true ]]; then
    "${compose[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  rm -rf "$BACKUP_ROOT"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Never adopt or clear an existing project. Each drill owns a fresh, portless,
# tmpfs-only PostgreSQL instance and Mock Data, separate from the normal app.
if [[ -n "$("${compose[@]}" ps -aq)" ]]; then
  printf 'Disposable project name already exists; refusing to reuse it.\n' >&2
  exit 1
fi
start_time="$(date +%s)"
if [[ "${RESTORE_DRILL_SKIP_BUILD:-false}" != true ]]; then
  "${compose[@]}" build postgres-e2e backend-e2e
fi
started=true
"${compose[@]}" up --detach postgres-e2e backend-e2e
ready=false
for _ in {1..60}; do
  if "${compose[@]}" exec -T backend-e2e alembic current 2>/dev/null | grep -q '(head)'; then
    ready=true
    break
  fi
  sleep 1
done
if [[ "$ready" != true ]]; then
  printf 'Disposable migration chain did not reach its head.\n' >&2
  exit 1
fi
mount_type="$("${compose[@]}" exec -T postgres-e2e stat -f -c %T /var/lib/postgresql/data)"
data_directory="$("${compose[@]}" exec -T postgres-e2e psql -U marketintel -d marketintel_e2e -Atc 'SHOW data_directory;')"
if [[ "$mount_type" != tmpfs || "$data_directory" != /var/lib/postgresql/data ]]; then
  printf 'Refusing recovery fixtures without a disposable tmpfs database.\n' >&2
  exit 1
fi
"${compose[@]}" exec -T backend-e2e python scripts/restore_drill_fixture.py seed
"${compose[@]}" exec -T backend-e2e python scripts/restore_drill_fixture.py write &
writer_pid=$!
sleep 1
BACKUP_ROOT="$BACKUP_ROOT" COMPOSE_FILE="$COMPOSE_FILE" COMPOSE_PROJECT_NAME="$PROJECT_NAME" \
POSTGRES_SERVICE=postgres-e2e POSTGRES_DB=marketintel_e2e BACKUP_RETENTION_COUNT=1 \
  "$ROOT_DIR/scripts/backup_local.sh"
wait "$writer_pid"
writer_pid=""
backup_dir=""
for directory in "$BACKUP_ROOT/"*-market-intelligence; do
  [[ -d "$directory" ]] && backup_dir="$directory"
done
if [[ -z "$backup_dir" ]]; then
  printf 'No completed recovery archive was produced.\n' >&2
  exit 1
fi
dump_count="$(awk -F '\t' '$1 == "sources" {print $2}' "$backup_dir/record_counts.tsv")"
live_count="$("${compose[@]}" exec -T postgres-e2e psql -U marketintel -d marketintel_e2e -Atc 'SELECT count(*) FROM sources;')"
if [[ -z "$dump_count" || "$live_count" -le "$dump_count" ]]; then
  printf 'The drill did not demonstrate committed writes after the dump snapshot.\n' >&2
  exit 1
fi
printf 'Concurrent writes proven: dump sources=%s, later live sources=%s.\n' "$dump_count" "$live_count"
"${compose[@]}" exec -T backend-e2e python scripts/restore_drill_fixture.py clear
restore_start="$(date +%s)"
COMPOSE_FILE="$COMPOSE_FILE" COMPOSE_PROJECT_NAME="$PROJECT_NAME" POSTGRES_SERVICE=postgres-e2e \
BACKEND_SERVICE=backend-e2e FRONTEND_SERVICE="" POSTGRES_DB=marketintel_e2e \
  "$ROOT_DIR/scripts/restore_local.sh" "$backup_dir" --yes-replace-database
"${compose[@]}" exec -T backend-e2e python scripts/restore_drill_fixture.py verify
printf 'Recovery drill passed: both PDF stores, all table contents, private findings/review and portfolio relationships.\n'
printf 'Measured restore verification: %s seconds; complete drill: %s seconds.\n' \
  "$(( $(date +%s) - restore_start ))" "$(( $(date +%s) - start_time ))"

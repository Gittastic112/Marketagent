#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="market-intel-release-check-$$-$RANDOM-$RANDOM"
TEST_PROJECT_NAME="$PROJECT_NAME-unit"
COMPOSE=(docker compose --env-file /dev/null -p "$PROJECT_NAME" -f "$ROOT_DIR/docker-compose.e2e.yml")
TEST_COMPOSE=(docker compose --env-file /dev/null -p "$TEST_PROJECT_NAME" -f "$ROOT_DIR/docker-compose.test.yml")
project_started=false
unit_project_started=false

cleanup() {
  local runner_exit_status=$?
  trap - EXIT INT TERM
  if [[ "$unit_project_started" == true ]]; then
    "${TEST_COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  if [[ "$project_started" == true ]]; then
    "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  exit "$runner_exit_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

assert_unused_project() {
  local checked_project="$1"
  local resource_ids
  resource_ids="$(docker container ls --all --quiet --filter "label=com.docker.compose.project=$checked_project")"
  if [[ -n "$resource_ids" ]]; then
    printf 'Disposable project already has containers; refusing to reuse it.\n' >&2
    exit 1
  fi
  resource_ids="$(docker network ls --quiet --filter "label=com.docker.compose.project=$checked_project")"
  if [[ -n "$resource_ids" ]]; then
    printf 'Disposable project already has networks; refusing to reuse it.\n' >&2
    exit 1
  fi
  resource_ids="$(docker volume ls --quiet --filter "label=com.docker.compose.project=$checked_project")"
  if [[ -n "$resource_ids" ]]; then
    printf 'Disposable project already has volumes; refusing to reuse it.\n' >&2
    exit 1
  fi
}

export NEXTAUTH_SECRET="${NEXTAUTH_SECRET:-release-check-secret-not-for-production}"
export LOCAL_AUTH_USERNAME="${LOCAL_AUTH_USERNAME:-release-check-user}"
export LOCAL_AUTH_PASSWORD="${LOCAL_AUTH_PASSWORD:-release-check-password}"
export E2E_FRONTEND_PORT="${E2E_FRONTEND_PORT:-13000}"
export E2E_BACKEND_PORT="${E2E_BACKEND_PORT:-18000}"

python3 -m unittest scripts.test_check_secrets
python3 -m unittest scripts.test_check_docs
python3 -m unittest scripts.test_local_compose scripts.test_backup_workflow scripts.test_recovery_metadata
python3 -m unittest scripts.test_dependency_locks scripts.test_container_scan scripts.test_legacy_financial_evaluator
python3 "$ROOT_DIR/scripts/check_dependency_locks.py"
python3 "$ROOT_DIR/scripts/check_docs.py"
python3 "$ROOT_DIR/scripts/check_secrets.py" "$ROOT_DIR"
python3 "$ROOT_DIR/scripts/validate_project_skills.py"

for port in "$E2E_FRONTEND_PORT" "$E2E_BACKEND_PORT"; do
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    printf 'Port %s is already allocated. Stop the owning service or override E2E_FRONTEND_PORT/E2E_BACKEND_PORT.\n' "$port" >&2
    exit 1
  fi
done
assert_unused_project "$PROJECT_NAME"
assert_unused_project "$TEST_PROJECT_NAME"
"${COMPOSE[@]}" build
# Build failure cannot claim ownership of resources created by another run.
assert_unused_project "$PROJECT_NAME"
assert_unused_project "$TEST_PROJECT_NAME"
project_started=true
"${COMPOSE[@]}" up --detach postgres-e2e backend-e2e frontend-e2e

for _ in $(seq 1 90); do
  if curl --fail --silent "http://127.0.0.1:${E2E_BACKEND_PORT}/api/readiness" >/dev/null \
    && curl --fail --silent "http://127.0.0.1:${E2E_FRONTEND_PORT}/api/auth/readiness" >/dev/null; then
    break
  fi
  sleep 2
done

curl --fail --silent "http://127.0.0.1:${E2E_BACKEND_PORT}/api/readiness" >/dev/null
curl --fail --silent "http://127.0.0.1:${E2E_FRONTEND_PORT}/api/auth/readiness" >/dev/null
"${COMPOSE[@]}" exec -T backend-e2e alembic heads
"${COMPOSE[@]}" exec -T backend-e2e alembic current
# Unit tests need the approved reference files without baking them into runtime images.
assert_unused_project "$TEST_PROJECT_NAME"
unit_project_started=true
"${TEST_COMPOSE[@]}" run --rm --build backend-tests
# Source guards inspect repository configuration outside the frontend build context.
"${COMPOSE[@]}" run --rm --no-deps \
  --volume "$ROOT_DIR:/repository:ro" --env REPOSITORY_ROOT=/repository \
  frontend-e2e npm test
"${COMPOSE[@]}" exec -T frontend-e2e npm run typecheck

printf 'Release baseline verification passed.\n'

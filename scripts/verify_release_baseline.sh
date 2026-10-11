#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="market-intel-release-check"
COMPOSE=(docker compose -p "$PROJECT_NAME" -f "$ROOT_DIR/docker-compose.e2e.yml")

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

export NEXTAUTH_SECRET="${NEXTAUTH_SECRET:-release-check-secret-not-for-production}"
export LOCAL_AUTH_USERNAME="${LOCAL_AUTH_USERNAME:-release-check-user}"
export LOCAL_AUTH_PASSWORD="${LOCAL_AUTH_PASSWORD:-release-check-password}"
export E2E_FRONTEND_PORT="${E2E_FRONTEND_PORT:-13000}"
export E2E_BACKEND_PORT="${E2E_BACKEND_PORT:-18000}"

python3 -m unittest scripts.test_check_secrets
python3 -m unittest scripts.test_check_docs
python3 -m unittest scripts.test_local_compose scripts.test_backup_workflow
python3 "$ROOT_DIR/scripts/check_docs.py"
python3 "$ROOT_DIR/scripts/check_secrets.py" "$ROOT_DIR"
python3 "$ROOT_DIR/scripts/validate_project_skills.py"

cleanup
"${COMPOSE[@]}" build
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
"${COMPOSE[@]}" exec -T backend-e2e pytest -q backend/tests
"${COMPOSE[@]}" exec -T frontend-e2e npm test
"${COMPOSE[@]}" exec -T frontend-e2e npm run typecheck

printf 'Release baseline verification passed.\n'

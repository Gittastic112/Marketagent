#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-$ROOT_DIR/backups}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-marketintel}"
POSTGRES_DB="${POSTGRES_DB:-marketintel}"
BACKUP_RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-7}"
BACKUP_PRUNE="${BACKUP_PRUNE:-false}"
source "$ROOT_DIR/scripts/recovery_common.sh"

if [[ ! "$BACKUP_RETENTION_COUNT" =~ ^[1-9][0-9]*$ ]]; then
  printf 'BACKUP_RETENTION_COUNT must preserve at least one backup.\n' >&2
  exit 2
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_ROOT"
BACKUP_ROOT="$(cd "$BACKUP_ROOT" && pwd)"
backup_dir="$BACKUP_ROOT/${timestamp}-$RANDOM-market-intelligence"
partial="$backup_dir.partial"
mkdir -m 700 "$partial"
scratch_id=""
cleanup() {
  if [[ -n "$scratch_id" ]]; then
    "$DOCKER_BIN" rm --force "$scratch_id" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# pg_dump provides a consistent MVCC snapshot without pausing normal writers.
"${compose[@]}" exec -T "$POSTGRES_SERVICE" pg_dump \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --compress=6 \
  --no-owner --no-privileges > "$partial/database.dump"

# All manifest evidence comes from this completed dump, never from later live
# counts. This container has no network, published ports or persistent volume.
scratch_id="$("$DOCKER_BIN" run --detach --rm --pull never \
  --name "mi-backup-proof-${timestamp}-$$-$RANDOM" \
  --label com.market-intelligence.purpose=backup-verification \
  --network none --memory 1g --cpus 1 --pids-limit 128 \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=2g \
  -e POSTGRES_USER=proof -e POSTGRES_DB=proof -e POSTGRES_HOST_AUTH_METHOD=trust \
  "${RECOVERY_POSTGRES_IMAGE:-postgres:16@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d}")"
if [[ ! "$scratch_id" =~ ^[a-f0-9]{64}$ ]]; then
  scratch_id=""
  printf 'Recovery verifier did not return a container identity.\n' >&2
  exit 1
fi
ready=false
for _ in {1..60}; do
  if "$DOCKER_BIN" exec "$scratch_id" pg_isready -U proof -d proof >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 1
done
if [[ "$ready" != true ]]; then
  printf 'Recovery verifier did not become ready. Partial backup retained.\n' >&2
  exit 1
fi
"$DOCKER_BIN" exec -i "$scratch_id" pg_restore --list < "$partial/database.dump" >/dev/null
"$DOCKER_BIN" exec -i "$scratch_id" pg_restore -U proof -d proof \
  --no-owner --no-privileges --exit-on-error < "$partial/database.dump"
"$DOCKER_BIN" exec -i "$scratch_id" psql -X -qAt -v ON_ERROR_STOP=1 \
  -U proof -d proof -f - < "$ROOT_DIR/scripts/recovery_inventory.sql" > "$partial/inventory.raw.jsonl"
recovery_python "$partial" create "$timestamp"
# Completion is atomic within the backup root. Interrupted .partial directories
# are never accepted by restore or retention.
mv "$partial" "$backup_dir"
if [[ "$BACKUP_PRUNE" == true ]]; then
  recovery_python "$BACKUP_ROOT" prune "$BACKUP_RETENTION_COUNT"
fi
printf 'Backup verified against restored dump, all table contents and both PDF stores.\nBACKUP_DIR=%s\n' "$backup_dir"

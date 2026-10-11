#!/usr/bin/env bash
set -euo pipefail

# Public package metadata only. No source folder, credentials or Docker socket
# enter the scanner. Images are exported through the operator's existing CLI.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
REPORT_DIR="${REPORT_DIR:-$ROOT_DIR/output/security/container-scan}"
SCANNER="aquasec/trivy:0.75.0@sha256:af6acf9a6b85dfe389a1941505c0ce9efef52a4719635e1a962f022a3d855daa"
[[ $# -gt 0 ]] || { printf 'Supply explicit image references.\n' >&2; exit 2; }
mkdir -p "$REPORT_DIR"
REPORT_DIR="$(cd "$REPORT_DIR" && pwd)"
SCRATCH_DIR="$(mktemp -d)"
trap 'rm -rf "$SCRATCH_DIR"' EXIT
index=0
reports=()
for image in "$@"; do
  index=$((index + 1))
  "$DOCKER_BIN" image save "$image" -o "$SCRATCH_DIR/image.tar"
  "$DOCKER_BIN" run --rm --read-only --cap-drop ALL --security-opt no-new-privileges:true \
    --memory 1g --pids-limit 128 --tmpfs /tmp \
    -v "$SCRATCH_DIR:/input:ro" -v "$REPORT_DIR:/reports" "$SCANNER" image \
    --cache-dir /reports/cache --scanners vuln --pkg-types os --list-all-pkgs \
    --format json --output "/reports/image-$index.json" --input /input/image.tar
  reports+=("$REPORT_DIR/image-$index.json")
done
python3 "$ROOT_DIR/scripts/check_container_scan.py" "${reports[@]}"

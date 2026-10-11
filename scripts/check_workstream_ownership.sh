#!/usr/bin/env bash
# Read-only planning/changed-path guard. No Git, Docker, Python or dependencies.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
manifest="$root/docs/workstreams/ownership.tsv"
owner=""
paths=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest|--owner|--paths)
      [[ $# -ge 2 ]] || { printf 'Missing option value.\n' >&2; exit 2; }
      case "$1" in
        --manifest) manifest=$2 ;;
        --owner) owner=$2 ;;
        --paths) paths=$2 ;;
      esac
      shift 2 ;;
    *) printf 'Usage: bash scripts/check_workstream_ownership.sh [--manifest FILE] [--owner W1 --paths FILE]\n' >&2; exit 2 ;;
  esac
done
[[ -f "$manifest" ]] || { printf 'Ownership manifest not found.\n' >&2; exit 2; }
if [[ -n "$owner" || -n "$paths" ]]; then
  [[ "$owner" =~ ^W[1-5]$ && -f "$paths" ]] || {
    printf 'Provide --owner W1..W5 and --paths FILE together.\n' >&2; exit 2;
  }
fi
arguments=("$manifest")
[[ -z "$paths" ]] || arguments+=("$paths")
awk -v requested="$owner" '
function error(message) { print "ERROR: " message; errors++ }
function safe(p) {
  return p != "" && p !~ /^\// && p !~ /(^|\/)\.\.?($|\/)/ &&
    p !~ /\/\// && p !~ /[\\*?\r\t]/
}
function contains(kind, prefix, p) {
  return kind == "file" ? prefix == p : index(p, prefix) == 1
}
FILENAME == ARGV[1] {
  if ($0 ~ /^#/ || $0 == "") next
  count = split($0, parts, "\t")
  who = parts[1]; kind = parts[2]; p = parts[3]
  if (count != 3 || who !~ /^W[1-5]$/ || (kind != "file" && kind != "tree") ||
      !safe(p) || (kind == "tree" && p !~ /\/$/) || (kind == "file" && p ~ /\/$/)) {
    error("invalid manifest row " FNR); next
  }
  for (i = 1; i <= n; i++) {
    if (contains(kinds[i], names[i], p) || contains(kind, p, names[i]))
      error("overlapping reservations: " owners[i] " " names[i] " and " who " " p)
  }
  n++; owners[n] = who; kinds[n] = kind; names[n] = p; seen[who] = 1
  next
}
{
  p = $0
  if (!safe(p)) { error("invalid changed path on line " FNR); next }
  matches = 0
  for (i = 1; i <= n; i++) {
    if (contains(kinds[i], names[i], p)) {
      matches++
      if (owners[i] != requested) error(p " belongs to " owners[i] ", not " requested)
    }
  }
  if (!matches) error(p " is frozen/unassigned; request coordinator review")
  checked++
}
END {
  for (i = 1; i <= 5; i++) if (!("W" i in seen)) error("missing owner W" i)
  if (errors) exit 1
  printf "Ownership check passed: 5 owners, %d disjoint reservations", n
  if (requested != "") printf "; %d changed paths checked for %s", checked, requested
  print "."
}' "${arguments[@]}"

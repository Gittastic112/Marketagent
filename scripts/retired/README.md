# Retired one-off tooling

The October 10 ownership audit moved 18 unreferenced root/frontend scratch scripts
to `local/2026-10-10/`, preserving their original bytes and paths in
[the inventory](inventory-2026-10-10.json). The `.txt` suffix makes them inactive
source records. They are not supported commands, importable modules or tests.

The local archive is intentionally ignored: old scratch tools can contain local
connection defaults, absolute paths and ad-hoc rewrite/reset instructions.
Never run them against the normal database or copy their defaults into settings.
The existing source safety archive and Git history retain the earlier baseline.
No database, source corpus, upload, backup or active test was deleted by this move.

Use [the execution runbook](../../docs/08-execution-runbook.md) for migrations,
readiness, tests, backups and recovery. Current operations belong in `scripts/`
or `backend/scripts/` with a documented purpose and bounded inputs.

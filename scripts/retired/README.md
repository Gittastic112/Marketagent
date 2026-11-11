# Retired one-off tooling

The October 10 ownership audit moved 18 unreferenced root/frontend scratch scripts
to `local/2026-10-10/`, preserving their original bytes and paths in
[the inventory](inventory-2026-10-10.json). The `.txt` suffix makes them inactive
source records. They are not supported commands, importable modules or tests.

The [October 25 inventory](inventory-2026-10-25.json) adds seven unreferenced
backend-root scripts under local/2026-10-25/backend, making 25 retired scripts in
total. It also records the retained empty debug database, historical error log
and relocation of two local helper packages under skills. Every moved file was
hashed before and after relocation. The inventory records index membership;
full staged/HEAD status still requires working Git.

The local archive is intentionally ignored: old scratch tools can contain local
connection defaults, absolute paths and ad-hoc rewrite/reset instructions.
Never run them against the normal database or copy their defaults into settings.
The existing source safety archive and Git history retain the earlier baseline.
No database, source corpus, upload, backup or active test was deleted by this move.

Use [the execution runbook](../../docs/execution-runbook.md) for migrations,
readiness, tests, backups and recovery. Current operations belong in `scripts/`
or `backend/scripts/` with a documented purpose and bounded inputs.

The [November 10 inventory](inventory-2026-11-10.json) retires two more unreferenced
scratch tools: a hardcoded PDF preview requiring an undeclared package, and a
dated route generator that would overwrite reviewed documentation with inferred
status. Their original bytes remain under local/2026-11-10; the total is 27
retired scripts. The maintained documentation checker owns route coverage.

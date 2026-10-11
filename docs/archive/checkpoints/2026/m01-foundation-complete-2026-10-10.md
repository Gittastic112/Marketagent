# M01 foundation accepted: rollout and browser verification

Accepted October 10, 2026, America/New_York. Some machine timestamps are October
11 UTC. Scope: close M01 in the [completion tracker](../../../roadmaps/completion-tracker.md),
including the explicitly authorized normal rollout and browser verification.
The [earlier infrastructure audit](architecture-and-completion-2026-10-10.md)
records implementation, cleanup and the full source-test baseline.

## Acceptance evidence

| Gate | Result |
|---|---|
| Full backend baseline | 1,294 passed, five upstream deprecation warnings, isolated source tests; application code unchanged since that run |
| Frontend baseline | 234 passed; TypeScript passed again with the final browser test repairs |
| Contract boundaries | Backend schema/import/compatibility and frontend API/export/transport guards included in the passing full suites |
| Production builds | Backend runtime/test/tools and standalone frontend built; normal runtime contains no pytest/backend test tree, UID 10001 |
| Disposable browser | Daily Brief evidence/price changes, multi-currency portfolio reconciliation, and valuation save/reset/refresh/archive/review/promotion/metadata/recalculation all passed |
| Normal browser | Authenticated dashboard, companies, portfolio, Daily Brief and Data Health return 200; visible headings in 364–640 ms in this single sample; no page exceptions or horizontal overflow |
| Normal responsive check | Dashboard inspected at 1440px and 390px; screenshots reviewed, no horizontal overflow |
| Browser security boundary | Authenticated read passes; missing and foreign Origin mutations both return 403 before writes |
| Normal readiness | Backend/frontend/PostgreSQL healthy, Daily Brief worker running, zero restarts and no OOM events |
| Recovery preflight | Current database restored into a network-disabled disposable PostgreSQL instance; all 109 table counts and content fingerprints match |
| Rollout preservation | All 109 fingerprints identical before and immediately after rollout, before resuming the worker |
| Public reference snapshot | Knowledge-base audit passes: 64 canonical files/catalog rows, 44 ledger rows, no inbox files; four auditor tests pass |
| Source publication | Secret scan and Git whitespace check pass for the explicit application/reference snapshot; local reconstructed Git tree equals uploaded tree |
| Final repository/docs | 28 repository/recovery tests pass; 78 active Markdown files and 644 local links validate |

The original browser setup first lacked installed runner dependencies, then hit
a shared-filesystem trace-folder error and a test hostname mismatch. The app's
host/origin checks were retained. Fixture API mutations now send the signed-in
page's Origin. The user explicitly approved updating the existing valuation test:
it opens collapsed input groups through their summaries and uses the desktop
Payouts navigation button. No assertions or valuation calculations were removed.

Screenshots and normal-browser results are under
`output/playwright/m01-20261010/normal-runtime/`, ignored by Git. Test data stayed
inside a separate tmpfs PostgreSQL stack; that stack and the restore instance
were removed. Temporary browser/build image tags and superseded application
containers were removed after verification. Existing persistent volumes remain.

## Backup and rollout identity

Backup: `backups/20261011T015017Z-market-intelligence/`. Directory mode 0700;
dump/manifest files 0600. Custom-format dump: 482,940 bytes, SHA-256
`40a40e915777c4b44bd8c9875880bcd7afa13102c9f482aa8c05e092d146aad1`.
Manifest/count checksums and complete row fingerprints are retained locally.
The original PostgreSQL volume was not restored, replaced, reset or removed.
Migration head remains `s1s1s1s1s1s1`.

Current backend and both workers use image
`sha256:0d4206bab801466ee7f50ed722239ea312095dc272c0c5542d4c2ce45b196b9e`.
The 402-file runtime source manifest matches the checkout exactly; aggregate
SHA-256 is `3383bbd979dd2f617b164d36cc91078d674160f5f295204f476cf74673b36cb3`.
The final rebuild incorporated the latest Compose guard script from the earlier
cleanup pass. Standalone frontend image:
`sha256:2cff08c3a75d861517d9bdd1ea7b815691bc35f4e165b0e2e7cb3749e0f4bbd1`.
Normal Compose image tags point to these validated images.

Protected environment files were never read. The controlled replacement reused
existing container settings in memory, comparing old/new environment lists
without printing or persisting their values. Container limits, localhost ports,
log bounds, runtime users and direct worker commands were checked. Only backend
startup runs Alembic. Old application images remain available for rollback.

The source-refresh worker remains created/stopped with restart disabled, preserving
the prior opt-out. pgAdmin is stopped with restart=no and its 512 MiB limit is now
applied. Source refresh requires an explicit operator start. The Daily Brief
worker was resumed only after the data fingerprint comparison.

## Actual data boundary

The pre-rollout database already contained the October Mock Data demonstration.
Normal screenshots visibly label its portfolio/events as Mock Data. The backup
contains zero document_assets rows, so this restore does not repeat the older
private-PDF evidence proof. Earlier September normal-data inventories are dated
historical evidence, not the current database inventory.

Opening Daily Brief created one deterministic stored brief through the existing
GET get-or-generate behavior. Its row count changed from two to three after the
browser check; the two earlier rows still match their original fingerprint, and
all other 108 tables remain identical. No external AI or provider fetch was
triggered. This is a foundation/browser gate, not genuine-input certification.
M03 still owns concurrent backup consistency, both evidence stores and off-device
recovery; M04 onward still own data/research completeness.

## Docker after verification and cleanup

| Container | Two idle CPU samples | Memory samples |
|---|---|---|
| Frontend | 0.49%, 0.06% | 83.55, 84.49 MiB |
| Backend | 0.60%, 0.21% | 273.9, 273.9 MiB |
| Daily Brief worker | 0.01%, 0.00% | 79.88, 80.12 MiB |
| PostgreSQL | 0.00%, 0.00% | 59.45, 59.85 MiB |

Approximately 497–498 MiB of container RAM, plus Docker Desktop VM overhead.
Four running containers, six present. No observed runaway idle CPU, restart loop
or OOM. Normal published ports remain 127.0.0.1:3000/8000/5432.

Docker reports 51 images/19.74 GB, build cache 21.81 GB (11.27 GB reclaimable),
and the same 18 volumes/3.108 GB. Shared categories cannot be added as unique host
disk consumption. The earlier cache prune reclaimed 11.69 GB; verification builds
subsequently added cache. No permanent cache cap or future monitoring was added.
Container resource usage is healthy now; build/image disk usage can grow again.

## GitHub and handoff

The private repository's previous branch was behind the actual local application.
A cleanup-only commit would have omitted required workers/contracts and other
already-tested modules. The explicit source/reference snapshot therefore spans
567 files, including pre-existing work. This is a preserved application baseline,
not a claim that this milestone authored every included feature.

Published baseline: [e448984](https://github.com/Gittastic112/Marketagent/commit/e4489848dcf37366f016bd9729fec8b361e89263)
on [codex/m01-foundation](https://github.com/Gittastic112/Marketagent/tree/codex/m01-foundation).
Its tree `fec30894cd330f9d447e44639ffa2f42085f1667` was reconstructed locally and
compared before publication. Snapshot scanning excludes environment files,
databases, backups, local agent configuration and unclassified scratch scripts.
Public benchmark bytes were verified; CSV publication respects existing LF rules.
The shared local index, branch and prior/untracked files were not reset or staged.

M01 is accepted at 10%; M02 is next. Use the published review branch as the
integration baseline once its review/CI status is checked. Full-release browser,
real-input, security and recovery gates remain in their assigned milestones.

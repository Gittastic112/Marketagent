# Agent Handoff

November 5, 2026 UTC: the UI review and explicitly approved US/India company
removal are complete locally. The [checkpoint](archive/checkpoints/2026/user-experience-and-company-removal-2026-11-05.md)
and [portable receipt](../data/reviews/user-experience-20261105.json) own evidence.
The prior implementation release is merged in [PR5](https://github.com/Gittastic112/Marketagent/pull/5).
[PR6](https://github.com/Gittastic112/Marketagent/pull/6) owns this pass's current
GitHub checks and merge status.

## Current database boundary

- The user confirmed the concrete full removal plan. All 12 companies, including
  seven US and five Indian companies, and their linked research are removed.
  This includes the eleven previously approved scenarios, financial histories,
  company documents/prices, portfolio contents and saved briefs.
- One guarded transaction removes exactly 7,314 rows in 28 tables and two obsolete
  parent-run metadata members. All 110 before/after fingerprints pass; the other
  82 tables are unchanged. Schema u3u3u3u3u3u3, original volume, portfolio account,
  settings, shared sources, global references and source files remain.
- Do not reseed companies, restore the removed models or recreate demonstration
  activity automatically. Historical approvals/review receipts remain evidence,
  not an instruction to repopulate the cleared workspace.
- The final pre-removal backup is 128,449,855 bytes, mode0600, with full archive
  payload verification. It is not restore-tested. Earlier backups remain.

## Delivered UI behavior

- Ordinary source notes are compact and deduplicated. Dates, Mock Data, actual
  unavailable sections and older-source guidance remain explicit.
- Brief counts describe selected inputs separately from the three visible
  headlines. Counts, caps, exclusions and source limitations remain inspectable.
- Company collection failures no longer look like empty successful results.
  Company/model/context failures retain loaded evidence and offer recovery.
  Incomplete portfolio snapshots name missing prices/FX on the affected card.
- Data Health groups optional checks and displays selected results or failures.
  Provider setup gaps describe the affected capability, not overall app failure.
- Direct Daily Brief links disable prefetch because opening that page can create
  today's missing brief. The saved-history GET remains read-only.
- The mobile company-setup step list supports keyboard focus and scrolling.

## Verified local release

- 351 frontend tests, TypeScript and Linux ARM64 production compilation pass.
  Backend code, contracts, calculation engines and migrations are unchanged.
  The previous backend/remote evidence retains its own November 4 date.
- Nineteen populated-data desktop/mobile views pass before removal. Thirteen
  empty-data views and two setup open/change-market/close workflows pass afterward.
  No page errors, page overflow, unintended requests or detected accessibility
  violations in the scoped scans. Every browser pass preserves its database baseline.
- Frontend is 20261105-ux-r3, image 105d5bc11069. Backend/workers remain
  20261104-independent-r2, image 285827fb5238. Runtime settings and other services
  are preserved; Daily Brief worker runs, source refresh/pgAdmin remain stopped.
  Ports remain localhost-only. Original/intermediate images and containers remain.
- A fresh signed-package build failed with upstream HTTP503. The installed UI
  compiles offline using the verified R2 dependency images; manifest/lock hashes
  match. No package pins, signature checks or security gates were relaxed.
- Local evidence: output/playwright/user-experience-20261105/. Its runtime-images.yml
  selects the current images. Deletion SQL/backups stay local and are not a
  reusable bulk-delete API, migration or public repository payload.

## Preservation and remaining work

Local HEAD remains fba390bf with the existing dirty checkout/index preserved.
Publish only the curated pass, never stage/reset/clean the shared checkout.
Protected settings pass in memory during replacement, never through file reads
or serialized receipts. DELIVERY_VALIDATION.md remains unchanged; the unseen kit
payload, installer and AGENT_PROMPT were not fabricated or claimed as validated.

The [single ledger](agent_capabilities_and_limitations.md#ordered-operator-handoff)
owns remaining limits. Removed issuer records do not resolve missing financial
facts or prove genuine portfolio performance. The user reports zero actual-use
days; agent tests cannot supply five business days or final acceptance. Deferred
Mac/off-device protection and populated recovery rehearsal remain unpassed.
No public hosting, broker activity or real-user AI permission grants are authorized.
M01-M04 remain accepted at 40 points; dependencies stay explicit. Commands belong
in the [runbook](08-execution-runbook.md).

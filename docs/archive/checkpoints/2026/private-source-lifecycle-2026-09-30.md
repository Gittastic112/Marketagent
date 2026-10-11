# Private source archiving and restore verification

Verified September 30, 2026. This workstream completes reversible organization
of private research sources, following the earlier search and pagination work.
It does not complete multi-source interpretation or the scheduled research loop.

## Delivered behavior

- Active sources are the default in both the latest-source list and paged search.
  The inbox can search active, archived, or all sources with the existing filters.
- Source cards and detail pages offer archive/restore, with explicit UTC dates,
  loading/error/retry states and a clear retention explanation.
- Original text, PDFs, source hashes, extraction metadata and completed AI findings
  remain accessible to the owner. Archiving is neither deletion nor approval.
- Duplicate intake returns the existing source without restoring or renaming it.
  The intake confirmation explains when the returned source is archived.
- Lifecycle writes require the viewed version and serialize on the owned row.
  Stale actions return 409 rather than overwriting a newer decision.
- Archived sources cannot start scans. A live scan blocks archiving; after two
  minutes an abandoned attempt can be archived. Publication and failure handling
  compare the claimed scan timestamp and lifecycle version. Late results cannot
  revive an archived/restored source or overwrite a newer successful scan.
- Failed provider executions remain audited separately; failure handling no
  longer guesses which AI output belongs to an attempt by selecting the newest.

## Implementation owners

The new `brief_source_lifecycle.py` service owns organization independently of
immutable source content, AI review and financial models. The existing source
service owns search and scan claims/publication. Narrow Pydantic and frontend
domain contracts carry the lifecycle version; the shared
`brief-source-lifecycle.tsx` component supplies both list and detail controls.

Migration `r9r9r9r9r9r9`, after `q8q8q8q8q8q8`, adds nullable `archived_at` and
non-null `lifecycle_version` defaulting to 1. No existing evidence is rewritten.
The API has 276 paths and 489 schemas. Compared with the prior source-search
workstream, this intentionally adds a lifecycle write route/schema, two read
fields and an active/archived/all query filter. It is not an unchanged-contract
refactor. No new dependency or financial formula was introduced.

## Verification

- Backend: 1,218 tests pass against mounted edited source with network disabled.
  Eighteen new lifecycle tests cover retention, PDF bytes, ownership/authentication,
  stale/no-op actions, duplicates, scan races, filter pagination, validation and
  additive migration. Five existing upstream deprecation warnings remain.
- Frontend: 225 tests and TypeScript pass. Final standalone frontend, backend
  and both worker images build successfully.
- PostgreSQL: fresh chain to q8 and populated q8-to-r9 upgrade preserve legacy
  values and a nonempty PDF fixture. Five pairs of competing lifecycle writes
  each return one success and one 409, with evidence unchanged.
- Browser: disposable signed-login/proxy workflow proves archive, filtered
  retrieval, archived inspection, restore, stale-tab conflict/reload recovery,
  simulated 503 recovery, and duplicate-upload retention/disclosure. No AI scan
  or valuation write is triggered by these actions. Mock Data only.
- The exact final standalone image also passes direct archived-page navigation,
  archive/restore and UTC timestamp checks. Desktop 1440px and mobile 390px
  captures were inspected; no mobile horizontal overflow was detected.
- Browser harness corrections: an exact label selector included descendant
  option text, so the check now uses the observed accessible role; a reload was
  issued before client navigation settled, so direct navigation was verified.
  These were test-control errors, not suppressed application failures.
- Documentation/secret/localhost/backup workflow tests: 23 passed. Secret scan
  and all 11 project-workflow checks pass. Active documentation/link and Git
  whitespace checks pass; an existing knowledge-base CRLF warning is unchanged.

Browser captures and isolated migration/concurrency scripts are under
`output/playwright/source-lifecycle-2026-09-30/`. They are local verification
artifacts, not application entry points. CLI browser session and disposable
`market-intel-source-lifecycle` stack were removed after verification.

## Backup and normal rollout

Normal frontend and both previously running workers were paused during backup
and verification. Backup `backups/20260930T235254Z-market-intelligence` retains
the q8 database, all 108 table counts and original PDF bytes. The custom dump is
8,444,115 bytes, SHA-256
`b1e93e8f063f9f6a526e582330cfcc78c2ce3e7d07fa5e0c0d774d2a557697a7`.

The backup was restored into a separate empty disposable database. All 107 data
table row counts/content fingerprints matched; migration metadata was separately
checked at q8. The restored copy was upgraded to r9 and existing values still
matched. Only then was the normal backend upgraded.

The normal database also preserved all 107 data-table fingerprints, excluding
only the two intentionally new lifecycle fields in source-row comparisons.
Two saved models, four assumption sets, two holdings, three transactions and the
one private source are unchanged. Its 4,919,649 PDF bytes remain stored; it is
active with lifecycle version 1. No real source was archived as a demonstration.

Normal backend/frontend/PostgreSQL health and r9 readiness pass. Both workers
are running again. All four normal published ports remain localhost-only.
The persistent normal PostgreSQL service was not recreated. Backup and evidence
captures remain; only disposable containers, network and temporary databases
were removed. Off-device backup recovery is not established.

## Remaining boundary

No bulk archiving, permanent deletion, storage reclamation, complete lifecycle
event history, source editing or semantic AI quality certification is claimed.
Multi-source triage, contradiction review and scheduled-brief integration remain
the next product boundary. The single limitation ledger owns their current scope.

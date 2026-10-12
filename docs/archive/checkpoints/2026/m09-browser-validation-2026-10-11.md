# M09 integrated workflow validation

October 11, 2026 local date; the final run finishes October 12 UTC. The implemented
changes pass isolated source and production-browser checks. M09 remains in progress:
this does not close every control/adverse-state, genuine-input or load-testing gate.
Normal application images and data remain on the M01 rollout boundary.

## Integrated evidence

| Check | Result |
|---|---|
| Backend | Final SEC/CSV follow-up passes 1,486 tests in 133 seconds. Three PostgreSQL-only skips and five upstream deprecation warnings. Earlier GitHub d9ffa73f passes 1,449, including the independent risk case |
| Additional risk reference | All 13 replay tests pass after adding an independent covariance case; one new test was added after the full suite had collected |
| PostgreSQL | Three real row/advisory-lock tests pass separately; fresh migration chain reaches s1s1s1s1s1s1 |
| Frontend | 264 tests pass; supported Linux production build and TypeScript pass |
| Browser | All 26 workflows pass in 5.3 minutes with one worker and no retries; all 50 page routes checked at 1440px and 390px |
| Operations | 49 documentation-fixture, secret-fixture, Compose, recovery, dependency-lock and container-scan tests pass |
| Contracts | 279 public paths, 510 schemas and 381 inventoried application operations; pure-schema, compatibility, domain/import, ownership and wire-manifest guards pass |

The original local 1,448-test pass precedes the additional risk assertion. GitHub's
[release baseline](https://github.com/Gittastic112/Marketagent/actions/runs/38199420778/job/114649272105)
passes that complete backend source including the assertion. The
[PR](https://github.com/Gittastic112/Marketagent/pull/2) owns its exact resulting head
and CI results. A draft PR and passing tests do not imply a normal-runtime rollout.
The later `m03-final-backend.log` records the 1,486-test source-mounted run after
37 added import/compatibility regressions. M03-05 closes the source input-boundary
check; host credentials, backup finalization and off-device recovery remain open.

The test API uses backend image
`043aaa1b42cfef27725dcfd3e28232fab704b14687c02afbb2762e609641b4a9`.
The production-built frontend image is
`42f239fd94855fe7196002d6beb8efcf0c53dbf67b0a37efc5d1b677f2a7036c`.
Unit tests mount current source; image contents alone are not their source proof.
All normal credentials and protected environment files were excluded.

## Browser coverage and repairs

The matrix enumerates 28 static and 22 owned detail pages. Fixtures include a
retained test PDF, extracted candidate geometry, linked event/alert evidence,
saved valuation, portfolio, thesis, research session and private analyst receipt.
All inputs are isolated Mock Data. No normal database or external provider is used.

Each route checks rendered server-stream completion, the unchanged 15-second
readiness budget, semantic names/labels, keyboard focus, minimum typography and
page overflow. Desktop and mobile run separately under the existing 120-second
per-test timeout. Every route failure is collected; no failing assertion is skipped.
Measurements and screenshots are retained per viewport. CI now retains passing and
failing browser evidence for seven days, with the same pinned upload action.

Functional workflows cover source search/recovery/races, PDF review/promotion,
manual India filing/retry, peer version history, company setup/industry weights,
CSV preview/apply/export, provider-not-configured recovery, saved valuation and
keyboard/mobile sensitivity, portfolio risk/FX/benchmark and snapshot capture.
The new private comparison workflow checks incompatible quoted periods, saved
review history, source archive/restore, immutable receipts and Mock Data exclusion
from deterministic brief context. It makes no AI call.

The audit found and fixed duplicate finding IDs across research cards. Anchors
remain available on standalone source pages. Research input/back-navigation labels,
sign-in/research heading sizes and empty-session auto-scrolling were also repaired.
Selected research-session, mobile comparison and replay-history screenshots were
visually inspected. Automated layout checks do not establish exhaustive contrast,
chart accessibility, every control/state combination or interpretation quality.

Integration also corrected fixture assumptions and selectors: source-detail data
needed canonical field-review links, missing-price fixtures needed recorded funding
and purchases, PDF evidence needed valid geometry and duplicate-safe reuse, and
selectors needed to target the visible main content instead of hidden React stream
copies. Application trust guards and authentication throttles remain intact.

At d9ffa73f, the push-triggered GitHub browser run passed all 26 workflows while
the PR-triggered run hit another hidden-stream copy of the new "Saved as generated"
label. The assertion now scopes that label to the visible main region, preserving
the original visibility assertion. The failed run and trace remain retained in
[CI evidence](https://github.com/Gittastic112/Marketagent/actions/runs/38199423604/job/114649280568).
The follow-up checks remain associated with the resulting PR head.
The corrected Daily Brief workflow passes locally on a fresh isolated database
in 7.2 seconds; its artifacts are retained in `output/milestones/m09/ci-repair-browser`.

The next PR run passes all 26 workflows, while its push run finds a sign-in focus
race: the client Suspense fallback exposes an empty main before the form hydrates.
The matrix now requires the visible username input and enabled sign-in button
before its existing keyboard check, inside the unchanged route-ready budget.
The [failed run](https://github.com/Gittastic112/Marketagent/actions/runs/38200187219/job/114651653031)
retains the failure; no focus assertion, route or timing threshold was removed.
The final SEC/CSV boundary changes are detailed in the
[M03 security follow-up](m03-security-2026-10-11.md#final-input-boundary-follow-up).
All 26 workflows pass again in 4.9 minutes after those fixes, with no retries.
The final local API uses the recorded M08 dependency image with an environment-free
snapshot of current application source mounted read-only; the frontend production
image is unchanged. Three PostgreSQL concurrency tests also pass in 1.53 seconds.
Evidence is under `output/milestones/m09/boundary-browser`; the mobile sign-in
screenshot visibly confirms keyboard focus. These additional 100 route views have
desktop/mobile medians of 632/637 ms, p95 of 2,824/1,830 ms and maxima of
4,281/2,953 ms. This does not convert repeated navigation into controlled load proof.

An early full backend run hit a bounded PDF worker under concurrent build pressure;
18 PDF tests passed serially and the complete serial suite subsequently passed.
A separate cancellation-test race observed an empty PID file before its child had
finished writing. Atomic readiness publication fixes the fixture while preserving
the kill/reap assertions. Test database fixtures now dispose their connection pools.
One resource-limit check also failed while the previous full runner was still
exiting; the isolated ten-test worker suite and final full run pass unchanged limits.

## Measured route readiness

Docker Desktop engine 29.7.2, aarch64, eight CPUs, 4,106,604,544 bytes VM memory.
The seed plus workflow mutations ends with 20 companies, two portfolios, four
portfolio transactions, 69 prices, 22 FX observations, six documents and 27 private
sources. These are deliberately small test inputs, not the normal research database.

| Viewport | Views | Median | 95th percentile | Maximum |
|---|---:|---:|---:|---:|
| 1440 x 900 | 50 | 608 ms | 2,401 ms | 10,711 ms |
| 390 x 844 | 50 | 620 ms | 1,982 ms | 3,350 ms |

Percentiles use nearest rank. The slowest desktop route is event evidence resolution;
the slowest mobile route is quick valuation. Every sample meets the existing 15,000 ms
budget. These are single navigations after shared runtime startup and earlier test
activity, not controlled cold/warm pairs, interaction latency or capacity guarantees.
The event-resolution outlier remains a profiling candidate under M09-05.

Artifacts are retained locally under `output/milestones/m09/integrated-browser`:
100 route screenshots and four route-measurements.json files, plus functional
screenshots. `output/milestones/m09/route-summary.json` and dataset-summary.json
retain the measurement profile. Earlier failed-run artifacts remain available.
The [runbook](../../../08-execution-runbook.md) owns repeatable commands.

## Runtime and acceptance boundary

The disposable project is stopped. Six older stopped M02/M04 test containers were
removed after verifying their PostgreSQL storage was tmpfs. Nine obsolete M02/M03/
M04/M06 image tags were removed. Two bounded build-cache cleanups reported 3.910 GB
and 8.348 GB reclaimed, about 12.26 GB total. The second cleanup retained a 5 GB
cache reserve and requested an 8 GB used-space target; Docker's aggregate/shared
accounting below is not a guarantee of an exact target or host sparse-file shrink.

| Docker report | Before | After |
|---|---:|---:|
| Images | 66 / 25.84 GB | 57 / 22.84 GB |
| Containers | 15 / 7 running | 6 / 4 running |
| Build cache | 342 entries / 23.67 GB | 148 entries / 11.41 GB |
| Persistent volumes | 18 / 3.114 GB | 18 / 3.114 GB |

Image/cache sizes overlap and must not be added as physical disk use. Unclassified
historical images, reusable test tools, normal/rollback images, all volumes, backups
and immutable source material remain. No blanket system or volume prune was used.

Three samples with only the normal stack running used 417-418 MiB across its four
containers. Total sampled CPU was 0.31%, 72.41% and 0.45%; Docker's per-core scale
makes the middle burst about 0.72 of eight available cores, not 72% of the machine.
The backend process averaged 2.3% over roughly 2 hours 50 minutes. Frontend/backend/
PostgreSQL are healthy, every normal restart count is zero, and published ports
3000/8000/5432 bind only 127.0.0.1. Source worker and pgAdmin remain stopped with
restart=no. These are observed readings, not a permanent resource guarantee.
Builds, provider activity and tests can still raise CPU/RAM and cache usage can grow.

M09-07 closes the integrated isolated source/browser gate. It does not close M09 as
a whole or award further cumulative acceptance points. The user has no genuine
trade records or off-device destination yet; the normal backup-finalization blocker
also remains. See the [single ledger](../../../agent_capabilities_and_limitations.md)
and [tracker](../../../roadmaps/completion-tracker.md) for the exact remaining gates.

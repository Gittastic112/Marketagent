# Financial review and product development, November 7, 2026

This pass implements the authorized documentation cleanup and independent
software improvements. It preserves the approved empty company universe,
all original sources/backups and the dirty checkout/index. PR6 was already merged
at 4d96c5e2da83671f3740a1e50bd342c762582171 when this pass began.
The unseen integration-kit payload/installer is not claimed as validated.

## Implementation

- Financial review planning adds a read-only authenticated endpoint and
  Fundamentals panel with operating, bank-equity and equity-cash-flow tracks.
  Three consecutive annual years expose missing disclosures, candidate review,
  unit conflicts, duplicate scopes and exact source linkage. Manual zero stays
  distinct from missing data. Source-linked counts are not certification.
  Normalization now rejects a period belonging to another company. Checklist
  row/column headers support assistive navigation.
- Legacy macro routes delegate to actual canonical calculations and validate
  owned context instead of returning fixed coefficients or persisting inputs.
  Finite, consecutive, chronological inputs are required. Constant factors are
  unavailable; positive rate slopes retain negative signed duration. Bottom-up
  output distinguishes per-factor covered contributions from complete-company
  estimates. Missing active scenario coefficients or currency direction withhold
  totals. Source conventions, formulas and limitations stay visible.
- Macro forms gain labels, responsive layout and up to 24 periods. Blank or
  malformed values never become zero; failed response envelopes remain errors.
  The frontend consumes the canonical bottom-up response shape.
- AI Evaluation v4 keeps citation/policy status separate from bounded
  claim-level numeric, period and instruction/inference cues. Flags require
  review reasoning before approval. Changed citations invalidate approval and
  retain the prior review receipt. No provider call, source instruction execution,
  automatic approval or bulk historical-output rewrite occurs.
- Current documentation distinguishes historical populated evidence from the
  approved removal, corrects the schema head and merged PR6 status, and places
  the next product increments and their real dependencies in the existing roadmap.

## Financial and provider evidence boundary

The retained November 4 US, bank and India packets remain the evidence for
unresolved historical claim values. A November 7 recheck of the official
[NVIDIA proxy](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000036/nvda-20260512.htm)
does not supply the missing fiscal-end ESPP rights. Later purchase-period estimates
and plan capacity are not replacements for that historical quantity. No new
company facts, scenarios or notes are inserted into the cleared database.

The official [NSE data policy](https://www.nseindia.com/static/market-data/nse-data-policy)
describes agreements governing intended use and redistribution. This review
does not establish a new subscription or right to automate a feed. The roadmap
requires a documented endpoint, permitted scope and response contract before
an India adapter; manual official-source intake remains supported.

Macro methodology follows the distinction between regression slopes and duration
in [Damodaran's project guidance](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/project/prques.htm)
and the bounded interpretation of [least squares](https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd141.htm).
These references do not certify the app's source-series conventions or forecasts.

## Validation and delivery

- Initial full local gate: backend 1,921 passed, six skipped, five upstream warnings. Frontend: 363 passed
  and TypeScript passed. All 75 repository tests pass. Contract inventory covers
  28 routes; dependency locks remain at 66 runtime and 70 test packages.
- Fresh production builds use signed pinned OS packages and locked dependencies.
  Last verified installation: backend/workers 20261107-product-r2; frontend 20261107-product-r4.
  A final checklist row-header correction also passes the focused render tests.
- An owned isolated browser, without the user's Chrome profile, verifies 22 views
  at 1440px and 390px and six interactions. It checks period expansion, invalid
  inputs, explicit Mock Data regression, constant-factor availability and empty
  company/portfolio workflows. No unexpected errors, external requests or
  horizontal overflow occurred. Scoped accessibility checks report no violations;
  some contrast checks are inconclusive, not a whole-app accessibility certificate.
- All 110 table fingerprints and stored assets match the pre-release inventory.
  The original PostgreSQL container, schema and settings remain; no migration or
  seed ran. Zero companies remain. One pre-existing empty-universe brief is
  preserved. Original worker states are restored and ports remain localhost-only.
- A fresh 551,827-byte quiesced backup has SHA256
  132d1ae9b41a86b1d3ccfe96452116041716bbe9a1b649d29be25f36c4cf8228.
  Full archive reading succeeds. This is not a new populated restore drill.
- Failed attempts remain recorded: one missing compatibility export was fixed;
  the unchanged yfinance resource-limit test and release-runner group passed
  separately after timeouts under concurrent load. Both full suites subsequently
  passed. Early browser harness assumptions/selectors were corrected for the
  retained brief and hidden page trees; final browser-r6 passed without data writes.

The first GitHub pass completed 70 browser workflows and found a real review-plan
bug: promotion changes the candidate status to `promoted`, which the new source
link check omitted. A regression reproduced that failure; the correction passes
27 financial tests and preserves active revision/value/unit checks. A missing
metric for an already-promoted candidate now requests reconciliation, not another
promotion. The row-header correction passes 45 focused frontend checks.

The same GitHub run and a fresh local scan identify ten available severe-fix
occurrences across three images: [APT](https://security-tracker.debian.org/tracker/CVE-2026-109518)
and trixie zlib [write-state](https://security-tracker.debian.org/tracker/CVE-2026-76844)
and [buffer](https://security-tracker.debian.org/tracker/CVE-2026-85091) findings.
The source advances all signed snapshots to 20261107T180000Z, checks APT bootstrap
safety and adds a pinned PostgreSQL 16.15 OS security build. Backup verification
now selects the running database image and rejects ambiguous service selection;
31 configuration/backup tests pass. No severe-fix check is suppressed.

The revised [GitHub run](https://github.com/Gittastic112/Marketagent/actions/runs/42407662530)
verifies 1,922 backend tests (six skipped), 363 frontend tests, TypeScript,
production builds, repository gates, six PostgreSQL integration checks, 71 browser
workflows and isolated recovery. All five jobs pass. All three OS image
scans report zero available HIGH/CRITICAL fixes; unfixed findings stay visible.
The PR's latest check records own the final documentation and merged-revision status.

Local security PostgreSQL/backend/test images build, but the frontend build stops
when Docker storage becomes read-only. The engine then becomes unresponsive.
At failure the Mac has 2.1 GiB free; deleting only the regenerable scan database
cache releases 1,679,474,688 allocated bytes. Empty directories, complete scan
reports, logs, originals, backups and all rollback images remain. A Docker restart
is requested. Security installation and the promotion fix remain pending locally.
The last healthy verification at 19:25 UTC must not be treated as current health.
The prepared rollout preserves the original PostgreSQL volume/version/collations,
retains the old containers, and uses separate active Compose registration. It has
not run. [PR7's checks](https://github.com/Gittastic112/Marketagent/pull/7/checks)
own the full latest-source, browser, recovery and security results.

The [portable receipt](../../../../data/reviews/product-development-20261107.json)
records the local verification. Detailed logs, before-images and the publication
receipt are under output/milestones/product-development-20261107/; private backups
and runtime settings are excluded from publication. Delivery uses
[codex/product-review-20261107](https://github.com/Gittastic112/Marketagent/tree/codex/product-review-20261107).
The branch's pull request and checks provide the live GitHub result, separately
from local verification. Only curated files are published; local HEAD/index and
unrelated pre-existing changes are preserved.

The [single limitation ledger](../../../agent_capabilities_and_limitations.md)
owns remaining external facts, provider permissions, actual-use acceptance and
deferred host/off-device recovery. Passing software checks does not satisfy them.

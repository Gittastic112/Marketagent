# Four-company handoff review, November 12, 2026

The handoff resolves to the ordered acceptance gates, starting with M05. This
pass uses the existing four-company database: AAPL, NVDA, META and GOOGL. It
does not restore the removed historical universe or create a fixture database.

## Applied source review

Seven official annual reports and three SEC companyfacts snapshots were added
through the existing intake workflows. Processing Runs 219-225 retain attempts,
counts and source scope. One existing Apple report was skipped as a duplicate.
The original statement text remains stored and hashed; seven new filings were
parsed into 445 inspectable sections in Runs 229-235, without generating AI.

The selected review compares exact original inline filing cells, consolidated
statement/note labels, periods, USD/share units and saved companyfacts hashes.
It applies 62 NVIDIA, 61 Meta and 58 Alphabet candidates through version-checked
review and promotion. Runs 226-228 record the 181 promotions. Nine annual
periods and 130 normalized values were added. All 73 reported-versus-normalized
comparisons agree, with no missing normalized counterparts. These are selected
input checks, not complete statement or valuation certification.

The [review receipt](../../../../data/reviews/financial-review-20261112.json)
retains each selected value, source locator/hash, decision, limitation and run.
The [decision register](../../../../data/reviews/research-demo-decisions.json)
records M05-FOUR-COMPANY-20261112 as agent review under delegated authority.
Sixteen selected candidates and 129 older newly imported candidates remain
unreviewed. No held candidate is silently set to zero or promoted.

Nine pretax-income/tax/net-income equations agree. Eight of nine lease-component
comparisons agree; Alphabet FY2025 retains its published USD 1 million
total/component difference. The receipt keeps that exception visible. Historical
consolidated share averages, debt carrying amounts, cash-flow net proceeds and
tax expense retain their specific definitions and valuation limitations.

## Preservation and recovery

Read-only repeatable-read fingerprints cover all 110 database tables. The 101
unaffected tables are unchanged. In the nine changed tables, every pre-existing
row also retains its original fingerprint. Existing Apple facts, the saved Apple
valuation, portfolios, transactions, private research and consent are preserved.

Before/after PostgreSQL custom archives are retained in the private local evidence
directory. Both are fully read by pg_restore without restoring into a database.
This is archive verification, not a populated restore drill or off-device recovery.
The initial source-review pass did not replace runtime services. The subsequent
authorized deployment preserves the same mounts, settings and localhost bindings.

## Evidence navigation repair

The financial review plan omitted candidate_id from non-PDF source links.
The document page already supports that parameter and uses it to show the exact
candidate value, locator and review state. The service now retains the ID, matching
the existing frontend evidence-link helper. No schema or dependency changes.

Two regression assertions fail against the original service; after the fix,
56 focused financial-review, SEC, candidate-version, source-history and provenance
tests pass. The first test-launch attempt used an incompatible in-memory default
engine setting; the supported file-URL default corrected the launcher. The actual
test fixtures remain in-memory, with no connection to the normal database.

A read-only invocation of the corrected service against current data verifies
90 candidate links across the four companies. The derivative production image
market-intelligence-review-backend:20261112-review-links builds successfully.
All 24 documentation-checker tests pass, and the documentation link/ownership
check passes. The owned source/document diff has no whitespace errors.
The initial pass stopped before installation and browser verification. The user
then authorized resolving the deployment conflict while preserving all data and
backups, and signed in for browser checks. The installed correction opens
document 26 with candidate 1692 and displays its reviewed value, locator and state.

## Original-report follow-up

Three additional official annual reports resolve five held facts: NVIDIA FY2024
interest expense and operating leases, Meta FY2023 interest expense and operating
leases, and Alphabet FY2023 interest expense. Runs 236-239 retain intake, including
the Meta recent-feed result that required its exact older filing accession.
Runs 240-242 promote the five version-checked facts; Runs 243-245 add 197 sections.
Both selected operating-lease component sums agree. The three-company normalized
comparison now has 75 exact matches and no mismatches or missing counterparts.

The [follow-up receipt](../../../../data/reviews/financial-review-followup-20261112.json)
retains exact source cells, hashes, versions and scope. Eleven selected candidates
remain held. The original receipt is unchanged. Across this follow-up, 102 of 110
tables are unchanged; only source/review/normalization/run tables change. Existing
Apple records, saved models, portfolios, research and consent retain their hashes.

## Installed deployment and financial overview

The former active backend and a retained rollback container shared Compose labels.
The final active project is market-intelligence-review-20261112-ui. Its six
services have unique registration, with the original external network and volumes.
Every pre-existing container is retained. Replaced containers are stopped with
restart disabled; existing settings, protections and localhost ports are preserved.
The source scheduler and pgAdmin remain stopped, and the daily scheduler resumes.

Two guarded attempts returned to the preserved installation: manually assigned
image identity labels caused an ordinary Compose dry run to request replacement,
and Compose's default source-worker restart policy differed from the installed
disabled policy. Their containers, archives and reports remain retained. The final
rollouts use Compose-generated identity and an explicit disabled source-worker
restart policy. Ordinary Compose dry runs request no replacement, and the backup
helpers' backend/database selectors each resolve exactly one current container.
All 110 table fingerprints match across each successful replacement. Fresh private
archives are fully read, without creating a proof database or restoring live data.

The signed-in browser exposed another defect: the company overview matched only
legacy display names, hiding promoted revenue/net-income codes. The table now
recognizes case/underscore equivalents and still withholds duplicate conflicting
records. Two regression tests fail before the fix; all 365 frontend tests, type
checking and the production build pass afterward. Browser checks verify the
NVIDIA three-year values/units, real missing fields, desktop layout and bounded
horizontal table scrolling at a mobile viewport. No stored values are rescaled.

Installed backend image: 9dcc7cb6c499180bc1ea35e244697cf6b71ad5d2eb2e61ee3424040f69a226ab.
The initial financial-overview frontend image was
a7375c1fd899d4f9f7838ce434b8bcd35fcf13f4fe2329342fd7131a413b7bc3;
it remains retained after the broader UI update below.
The prepared frontend context excludes protected settings before file inspection;
failed context preparation/build reports remain retained. No dependencies or
database migrations were changed.

## Broader installed UI review

The user requested fixes while reviewing the entire interface. The initial pass
visited 26 distinct routes on existing data. Changes span the owning screens,
shared display formatting and three style files because the observed issues
cross research, events, alerts, documents, financials and portfolio workflows.

- Research now orders documents by ingestion time and displays publication dates
  separately; events sort by recorded creation time. Titles link to evidence
  or thesis records. Notes are no longer all described as active regardless of state.
- Narrative impact displays out of 100, replacing the incorrect out-of-10 label.
  Missing event scores stay unscored. Dashboard events resolve company tickers.
- Search links containing an event ID select that record and expose its evidence
  route, with a return to the full list and an explicit missing-record state.
- Documents show company/source names; full hashes remain in expandable controls.
  Status and provenance codes have readable labels without changing stored values.
- Portfolio list prices/weights use up to two displayed decimal places while fractional
  quantities retain six; rounded negative-zero attribution displays as zero.
- Intake panels collapse without discarding their forms. Mobile research cards,
  narrative metadata and saved-valuation headings wrap. Financial tables retain
  source units, unavailable fields and keyboard-accessible horizontal scrolling.

Four new rendered regressions failed before their fixes. The selected-event
regression was then added. The first complete test run passed 369 tests and failed
one source-shape guard that still expected the old raw status formatter; the
guard was updated to the shared formatter without removing the data-state check.
The final suite passes all 370 tests, TypeScript and the production build.
Existing browser specs now open the collapsed forms before testing their inputs;
the isolated fixture browser suite was not run in this no-new-datasets scope.

Installed frontend image:
07ea29b1ac2dc27a3dd694ea8164d5959979dd3436b6ec39b63dd6a39f352a25.
The UI rollout preserves all 110 table fingerprints, settings, mounts, ports,
volumes and prior containers. Its fresh archive was fully read. A second archive
and table comparison after browser verification preserve the same records.
This is archive readability evidence, not a new restore rehearsal.

Post-install signed-in checks record 46 observations: all 19 main pages at both
desktop and mobile sizes, plus selected company, saved-valuation, evidence and
display checks. Requested viewports were 1280×900 and 390×844; the existing browser
scale yielded CSS widths of 1163 and 354. No horizontal page overflow, visible
unlabelled fields, page error alerts or captured console errors were observed.
Four expanded intake forms retain readable mobile controls; financial tables
scroll with the keyboard. Event selection, narrative scores, source hashes,
company links, and preserved financial values were verified in the installed UI.

Evidence is retained in ui-audit-before.json, ui-audit-installed.json,
ui-full-tests-final.log, ui-typecheck-final.log, ui-builder.log, ui-runner.log,
deployment-ui/, final-ui-preservation.json and three UI screenshots under the
local receipt directory below. The browser viewport override was reset and the
updated Research Hub left open. These bounded read-only checks do not certify
every control or create actual-use days.

## Handoff

Local receipts, failed test-launch evidence, source comparisons, database
fingerprints, archives and the built image record live under
output/milestones/handoff-completion-20261112/. Pre-existing changes to local
configuration, the protected environment example, CI, handoff and runbook were
preserved. Protected settings were not read.

[Current State](../../../current-state.md) owns verification status and the
[limitation ledger](../../../limitations.md#selected-company-review-follow-up)
owns remaining input and operating prerequisites. M01-M04 remain accepted;
this pass adds no milestone points or final user acceptance. The user reconfirmed
zero actual-use days on November 12; agent checks do not create use days.

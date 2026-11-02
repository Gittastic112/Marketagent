# Valuation review and existing-data browser audit

October 30 through November 2, 2026. The user asked to exercise the different
functions and fix defects, and confirmed no personal use days. Agent browser
activity is not the five-business-day acceptance record. Git/GitHub publication
remains deferred. No new PostgreSQL dataset, public deployment or broker work.

## Corrections

- Valuation suggestions now use full currency units and full shares before
  ratios and forecasts. Explicit million/thousand/lakh/crore source scales retain
  their original values, units, source IDs, conversion multiplier and formula.
  Ambiguous units or incompatible currencies withhold the suggestion; there is
  no inferred FX conversion. Reviewed financial facts remain unchanged.
- Forecast growth is an Estimate requiring review, not a historical Fact.
  Positive operating leases require explicit accounting/bridge review. Draft
  promotion checks current source, method, benchmark and freshness signatures;
  stale inputs cannot be promoted using an old review. Blank and nonfinite values
  cannot be treated as reviewed zero. Refresh preserves intentional edits.
- Financial-services drafts use equity-model requirements, including book equity,
  net income, ROE, cost of equity and shares. Unused FCFF fields no longer block
  the bank model, and model selection survives reload. Distress reviews include
  probability and proceeds. No saved model was promoted or recalculated.
- An owner can cancel a queued source refresh while retaining its audit history.
  Running/completed jobs reject cancellation. The worker's PostgreSQL advisory
  lock prevents cancellation from racing with execution. The UI explains stopped
  source scheduling and restores draft editing after cancellation.
- Macro import/manual-entry forms have unique field IDs. Portfolio activity
  tables support keyboard scrolling. Macro sensitivity uses readable surfaces,
  explicit selected modes, persistent field labels and responsive input widths.

The change crosses backend source/review services, owned HTTP/API boundaries,
frontend forms and regression tests because source scale and model-specific
review must agree end to end. It does not change the valuation engines' formulas.

## Validation and retained failures

Backend release `20261030-r2`: **1,809 passed, six PostgreSQL opt-in skips, five
warnings**. Frontend: **322 passed**, production Linux build and TypeScript pass.
Twenty-two contract checks, 61 repository checks and dependency-lock validation
pass. The six separate PostgreSQL integration checks retain their earlier remote
CI evidence; this pass does not claim a new isolated PostgreSQL run. A focused
read-only probe against the real database verifies queued cancellation rejects a
held worker advisory lock, without changing the job.

The first broad browser pass exercised 56 routes at desktop/mobile sizes:
109 of 112 views passed. Three view failures found the macro field-ID and
portfolio keyboard defects. Its additional search failure was a test locator
matching a hidden server-render stream copy, corrected by waiting for the render
and scoping the locator. Subsequent focused passes verified the repairs.

Draft workflow checks used Apple, Reliance, Airtel and HDFC with their retained
sources. The October 30 R2 pass records 15 successful actions and 11 views,
including canonical units, blank review rejection, unchanged saves, obsolete
version rejection, stored-input refresh, archive-dialog cancellation, bank-model
selection and cancelling queued Apple run 42. Its mobile section selector used
the wrong locator; the stopped test's later closed-browser errors are preserved.
The corrected selector uses the actual responsive section control.

November 2 continuation: **30 actions and 28 views pass**, with no browser errors,
accessibility violations or page overflow. It covers all 19 mobile saved-model
sections, both macro modes, repaired macro and portfolio screens, keyboard tables,
search and empty results. All six saved sensitivity centers equal the saved base.
Reverse DCF converges to the saved comparison-price assumption within 0.01 currency
units and leaves persisted inputs/outputs unchanged. This verifies calculation
consistency, not the economic validity of the saved NVIDIA assumptions.

Visual inspection then found cramped mobile macro fields that automated checks
missed. The final narrow layout pass adds **four passing desktop/mobile views**,
checks every input's width and persistent label, and passes manual screenshot
inspection. Its first build
rejected a duplicate input attribute; the corrected build uses an isolated audit
directory. The failed log and audit-directory correction note remain retained.
The initial November builder log was overwritten during that correction; its
image identity, runner-build log, source context, tests and rollout remain.

## Database effects and recovery

The broad October browser pass generated Daily Brief 12 and blocked regime score
9, and filing discovery created Processing Runs 167/168. The earlier records in
those tables, the other 106 tables and source assets remained unchanged. These
GET-triggered summary/discovery effects are recorded, not described as read-only.

Opening the four genuine-company drafts created three missing drafts; persisted
draft count moved from two to five. The later source-refresh actions changed
draft state and cancelled queued run 42, retaining its timestamps and step history.
The other 107 tables and source assets were unchanged. No source facts, saved
valuations, holdings or financial-history records were rewritten.

November's continuation preserves all **109 table fingerprints** and source
assets. Every installation retains a fresh quiesced database dump with archive
listing and SHA-256 verification. These are new backup checks, not new restore
drills. Original PostgreSQL volume/schema and in-memory runtime settings remain.
Published ports stay on 127.0.0.1. Rollback files, logs, images and read-only mounts
are preserved; protected environment files are excluded.

Final runtime proof matches **449 backend source files**, the single schema head
`s1s1s1s1s1s1`, and the frontend build identity. Three idle samples show healthy
web/database services and no unexpected restarts. Daily Brief scheduling is
restored; source refresh and pgAdmin remain stopped with restart disabled. The
Daily Brief worker was held during verification; this interval must not be
described as continuous scheduling. Ten additional rollback copies preserve
their changed files/logs/images outside the six-service Compose registration.
No image or volume was deleted and no byte savings are claimed.

Final backend/workers use image `b2079b253c036f824a818328c4d725f0b5e7101711f73bf12e21fdd1088b5bbf`;
frontend uses `5bab9fcc383ba39d9d4a46e9db4bf7a651b8361db23ddca8c54ec7d63097fcca`.
The [changed-source inventory](../../../../output/milestones/valuation-browser-20261102/r2/changed-source-files.json)
lists 27 application/test files changed since the October 28 build, separately
from this documentation reconciliation and local evidence recipes.

## Rechecked next work

A fresh read-only inventory of all 11 securities runs against the installed
backend with no provider calls or review approvals. The
[readiness receipt](../../../../output/milestones/valuation-browser-20261102/r2/review-readiness.json)
pins source signatures, periods and the remaining bridge inputs. The eight
operating-company suggestions contain required fields but still need 19 to 21
field reviews, including placeholders; presence is not approval. HDFC, ICICI and
SBI each lack selected common book equity and target ROE for their bank model,
with ten required review fields. Source/currency corrections do not remove the
remaining economic judgment and accounting-evidence requirements.

The next review should select source-backed bank common equity and distinguish
historical earnings/ROE from the forecast target, then complete operating-company
lease, cash, dilution and minority/preferred/award bridges. Unknown amounts must
stay unavailable. Credential rotation, five actual use days and final acceptance
remain separate gates; no acceptance point is added by the audit.

## Evidence locations

- [October source/build/workflow evidence](../../../../output/milestones/valuation-review-20261030)
- [Final backend and review-flow proof](../../../../output/milestones/valuation-review-20261030/r2)
- [November continuation and database comparisons](../../../../output/milestones/valuation-browser-20261102)
- [Final macro layout build and runtime proof](../../../../output/milestones/valuation-browser-20261102/r2)

Current limitations and next work remain in the [single ledger](../../../agent_capabilities_and_limitations.md).
This closes the observed code/browser defects, not M03 credential work, the
remaining financial/model evidence, five actual use days or final acceptance.

# US financial, AI and existing-example review

October 18, 2026. Research/demo scope and `AUTH-20261017-DELEGATED-REVIEW`
apply. These are agent decisions under user delegation, not personal user approval
or independent human certification. The application change is a keyboard-accessible
portfolio attribution table plus its browser regression. No dependency, backend or
migration changes. Existing database/source records are retained; no new fixture
dataset or provider call was used.

## Reviewed US facts and normal-runtime application

[M05-US-08](../../../../data/reviews/us-financial-review-20261018.json) records exact
candidate versions, source hashes, units, fiscal dates, accounting treatment and
held rows. Ten retained original HTML reports were reparsed independently of the
application extractor: 672 preferred source cells and 402 selected annual
candidates were checked. Five displayed dashes are explicit inline-XBRL zero
facts. Nine Microsoft non-inline cells and five comparative interest concepts
have separately documented source checks.

355 selected candidates were approved; 47 selected candidates and all older
unselected candidates retain their previous review state. Amazon face/carrying
debt stays distinct, Alphabet's USD1m lease-total discrepancy stays unresolved,
and issuer weighted-average shares are not class-specific current shares.
Cash-flow cash including restricted balances is not interchangeable with cash
available for valuation. No numerical forecast was approved by this source review.

[M05-US-09](../../../../data/reviews/us-financial-application-20261018.json) records
the successful exact-version application into the existing normal database:

| Security | Processing Run | Reported facts / source revisions | Annual periods | Normalized values |
|---|---:|---:|---:|---:|
| AAPL | 100 | 72 | 3 | 45 |
| AMZN | 101 | 55 | 3 | 36 |
| GOOG | 102 | 53 | 3 | 37 |
| GOOGL | 103 | 53 | 3 | 37 |
| MSFT | 104 | 61 | 3 | 39 |
| NVDA | 105 | 61 | 3 | 54 |
| Total | Six successful runs | 355 | 18 | 248 |

Seven tables changed. All 102 other tables and unrelated records within the seven
changed tables match their pre-application fingerprints, including prior HDFC
facts, portfolio records and saved valuations. Independent Decimal checks cover
the supported tax, NOPAT, working-capital, ROE and selected EBITDA/debt/ROIC
calculations. Missing FCFF, FCFE and reinvestment inputs remain unavailable.
Together with HDFC, the normal database now has 20 reviewed periods, 415 distinct
reported facts, 419 source revisions and 256 supported normalized values.

The pre-application dump is 12,121,107 bytes, SHA-256
`19877aa2fa5449485b141de33f33e2fd87804e62505b5f98f60badc4197085fa`.
Its archive listing passed; this does not claim a new restore test. Prior verified
recovery and both PDF stores remain intact. The daily-brief worker was paused for
the application/financial-browser comparison, then resumed. Source refresh and
pgAdmin remain off. Protected environment files were not read.

All six financial pages pass at 1440px and 390px: 355 API values, units and fiscal
dates match the reviewed rows; 18 periods and 248 normalized values are shown.
Pending candidates remain unchanged. The app displays incomplete valuation-input
coverage. Twelve views have no horizontal page overflow, browser errors or axe
violations. Mobile keyboard table scrolling passes. Warm readiness ranges from
366 to 921ms against the unchanged 15-second limit; this is not a load benchmark.
All 109 table fingerprints remain unchanged after the financial-browser reads.

The initial financial browser locator matched hidden streamed markup. Scoping to
the accessible normalization region fixes the test; application code and timeouts
were unchanged. Failed artifacts remain alongside the passing run.

## AI interpretation review

[M08-AI-REVIEW-20261018](../../../../data/reviews/ai-interpretation-review-20261018.json)
checks the original packet's hashes, public source excerpt offsets, quotes and
six actual saved Gemini responses, plus four existing adversarial fixtures.
Four outputs are accepted only for constrained source-summary uses. The regional
sales summary does not support the proposed opposing company-wide revenue edits;
those mappings are rejected. The period-comparison response stays blocked because
its own quoted evidence lacks claimed comparison labels.

The four fixture claims with incorrect numbers/periods, unsupported durability or
source-instruction obedience are rejected despite valid citations. Citation
validity and interpretation judgment remain separate. Original output files and
human-review fields are unchanged. There was no new provider call, normal AI
write or saved-model change. This closes the selected M08-04 review-set task, not
a statistical accuracy estimate or future injection-resistance guarantee.

## Existing portfolio examples and keyboard correction

M07-DEMO-REVIEW-20261018 records the revised research/demo check using the existing
three holdings and 22 stored snapshots. 64 independent checks cover current and
historical value/cost totals, dated sample covariance, marginal/component risk,
component sums, no-flow TWR and single-deposit closed-form MWR. TWR is the selected
snapshot-period return; MWR is annualized since the first recorded cash flow.
Both remain provisional because legacy snapshots do not establish verified replay.

Current and historical risk stay partial. Two current histories mix adjustment
bases and remain excluded. Historical risk uses only matching return intervals;
252-period annualization does not establish an exchange calendar. No benchmark or
trusted DCF gap was fabricated. Genuine-input readiness stays blocked and real
multi-currency proof remains unperformed, outside the approved demo release.

The first browser script assumed panel landmarks that the actual markup did not
provide; scoping from the observed headings corrected that test. It then found a
real mobile `scrollable-region-focusable` violation in the populated attribution
table. The table now has a named focusable region. The existing portfolio browser
test adds Tab-to-table and ArrowRight scrolling assertions. Failed artifacts are
retained; the fix does not remove checks or increase timing limits.

All 302 frontend tests, dependency identity check, production build and TypeScript
pass. The incomplete first staging attempt failed before a complete source copy;
its failed build log is retained. The corrected allowlisted staging verifies all
340 source/build inputs and contains only the table/test change plus previously
published ignore-rule maintenance relative to the preceding installed build.

Frontend image `market-intelligence-m07-accessible-frontend:20261018`, ID
`sha256:fa54aa79476f5062ac151ab6cc43135cf08e6a3863ea1ebda584327312f113de`,
is installed on localhost. Runtime settings, localhost ports and the original
backend/PostgreSQL containers are preserved. The previous frontend image/container
is retained for rollback. A fresh 12,146,346-byte dump includes the reviewed US
facts; SHA-256 `c108274ec9088707b32171b26f05d5ec30fb955d33a3a2e296125a8407d497d3`.
Archive listing passed; no new restore test is claimed.

Six normal desktop/mobile views cover overview, selected historical performance
and a current date without a stored snapshot. All pass, with no browser errors,
page overflow or axe violations. Mobile keyboard table scrolling passes. Current
period returns stay unavailable; historical returns retain their distinct dates
and provisional labels. The mobile screenshot was inspected. Warm readiness was
376-579ms against the unchanged 15-second limit. This verifies the revised M07-05
demo treatment; the original complete-source/model proof remains unperformed.

The final frontend image also passes all 12 US financial views again, checking
the same 355 values and preserving the pending candidate roster. Final financial
readiness is 364-880ms. All 109 table fingerprints match the pre-rollout baseline
after both browser suites. Daily Brief scheduling is resumed; source refresh and
pgAdmin remain off. The final verification receipt records the exact image ID.

## Evidence retention and remaining gates

Detailed source checks, private database fingerprints, the backup, browser/API
outputs and execution recipes are retained locally under
`output/milestones/review-continuation-20261018/`. Only public financial receipts,
delegated decisions and aggregate verification evidence belong in GitHub.
Portfolio values, owner identities, credentials and backup contents stay local.

M05 remains open for remaining issuer/note coverage, comparability, complete
valuation bridges and industry weighting. M06 cannot inherit complete input
coverage from these selected histories. M03 credential rotation is still an
operator gate; Mac protection/off-device recovery remain explicitly deferred.
M10 actual-use days and final acceptance are unperformed. Accepted milestones
remain M01-M02, or 20 acceptance points, with M03 next. See the
[tracker](../../../roadmaps/completion-tracker.md) and
[single limitation ledger](../../../agent_capabilities_and_limitations.md).

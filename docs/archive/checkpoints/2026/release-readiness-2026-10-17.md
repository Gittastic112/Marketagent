# Local release preparation, October 17, 2026

M01-M02 remain accepted at 20 acceptance points. This pass completes identified
parser repairs, review preparation and technical rollout; it does not approve
financial sources, forecasts, AI interpretations or a complete daily-driver release.
The [completion tracker](../../../roadmaps/completion-tracker.md) retains stable
gate IDs. The [limitation ledger](../../../agent_capabilities_and_limitations.md)
owns the exact outstanding operator inputs.

## Parser and source evidence

`pdf_targeted_v5` recognizes complete rupee-prefixed EPS tokens and the observed
SBI EPS glyph only when uniquely located characters use the embedded ITFRupee
font. Currency conflicts, unverified glyphs and unsupported monetary use stay
rejected. EPS remains per share, separate from statement scales.

The Airtel cash-flow fallback excludes a trailing two-digit sidebar number only
when repeated sequential navigation numbers sit outside geometrically verified
year/value columns. It rejects missing/reordered columns, in-table numbers and
additional header labels. Original text, exact coordinates, excluded-token
evidence and review warnings remain. No parsing resource limit was relaxed,
schema changed, existing candidate rewritten or valuation formula altered.

Ten retained official India PDFs yield 784 selected candidate entries: 728 match
both value and unit; 56 match values and retain pending HDFC unit proposals.
All eight selected previously skipped Airtel/SBI entries now match. There are no
numeric mismatches, missing candidate references or uncovered selected reference
entries. Counts include duplicate disclosures and comparative years, not unique
company facts, complete statements/notes or an accuracy score. References remain
agent-prepared and unapproved. No normal financial import or promotion occurred.

Local review entry: `output/milestones/m05/review-batches-20261017/review-packet.html`.
It links ten company batches, source hashes/pages, HDFC corroboration and 100
accounting-note topics. Previously retained source originals are unchanged.

## Actual AI review preparation

Six bounded Gemini calls use three retained public Apple FY2025 excerpts and
three labeled Mock Data adversarial cases. Only 2,069 characters of selected
source text, dates, public/Mock Data identity and the field catalog are sent.
Provider/model/prompt: `gemini`, `gemini-3.5-flash-lite`, `brief-source-v3`.
No private portfolio/thesis/valuation data or normal database writes occur.

Five responses pass source/format checks. One response is blocked because its
first finding supplies USD/consolidated labels absent from that finding's quote;
offline schema replay confirms the rejection. Its raw output and failed Processing
Run remain retained, without retry. This is not a passing interpretation case.
Regional-sales suggestions for company-wide revenue still need judgment. Agent
observations and all human verdicts remain separate; no AI output is approved.
The small one-issuer sample cannot certify general model quality.

Local review entry: `output/milestones/m08/interpretation-review-20261017/review-packet.html`.
Inputs, raw responses, exact hashes, timestamps, audit runs and isolated evaluation
database are retained. The earlier host-mounted SQLite attempt failed before any
provider call; its partial database is labeled incomplete.

## Verification and retained failures

| Gate | Result |
|---|---|
| Regression-first parser baseline | Four expected new failures before implementation; 49 prior cases pass |
| Focused parser/source/resource checks | 98 pass before the final extra-header regression; final full suite covers it |
| Full backend | 1,680 pass, six opt-in PostgreSQL checks skip; exit 0 and five upstream deprecation warnings |
| PostgreSQL | All six integration checks pass against the disposable database before the later user restriction |
| Financial/security browser workflows | All four pass: exact-version financial correction/recovery, PDF review/promotion/draft provenance, incorrect Mock Data AI still pending, invalidated-session access |
| Rollout failure handling | Four mocked rollback/success checks pass; the first real rollout also restores prior images on fingerprint failure |
| Current normal browser | 24 routes, 48 desktop/mobile views, zero browser errors/overflow/accessibility violations, two forbidden-Origin checks; maximum readiness 470 ms under the unchanged 15-second gate |
| Recovery before user restriction | Fresh schema and concurrent-write format-3 recovery verify all 109 tables plus both PDF stores. Restore 8 seconds; full drill 30 seconds |
| Review files and documentation | Six desktop/mobile packet views pass without overflow, script controls, browser errors or external requests; local links verified. Twelve documentation tests and the 78-file/735-link check pass |

The first full backend harness omitted required data fixtures: 24 failures, 1,656
passes and six skips. Correcting only the read-only data mount resolves those
failures. The first browser harness omitted its disposable signing configuration;
all four tests failed before sign-in. The corrected configuration passes. No
application assertion or timing threshold was weakened. Failed logs/screenshots
and final runs remain in the packet's `validation` and workflow directories.
The unchanged frontend's full 302-test/type/build and 64-workflow evidence remains
dated in [the October 13 checkpoint](m05-m09-workflows-2026-10-13.md); this pass does
not relabel that whole matrix as a fresh local run.

## Normal localhost rollout and observed data change

Parser source SHA-256: `5116f688c0f4eeb2a79be2b187377796e0a33a3b3e4e694021a3b242909189f7`.
Runtime image: `sha256:2a96dc5820570745aabbe0c2d8674da307e30e7126d55e558bafa7a9b4c34364`.
Test image: `sha256:6c04156e489b1b3eed689cd2767c978e0117e186ae428b7f5af5f8c21fc6495e`.
Unchanged frontend: `sha256:4e624db6e28c016084e5a2b3577dbd11a0148de0661c024f8c08485c64eb0708`.

Verified format-3 backup: `backups/20261017T202749Z-15027-market-intelligence`;
dump SHA-256 `cb346e7ec2f484fe4cd81ae96a983a04f96d645f63a701a7d43c47d6ead8d29c`. Its restore proof completed before
the user requested no further disposable datasets.

The first 48-view pass succeeded but GET `/daily-brief` generated today's stored
brief, so post-browser fingerprint equality failed and the prior app images were
restored automatically. Exact COPY-row comparison proves all six prior briefs
unchanged and exactly one new row; every other table and asset-store fingerprint
is unchanged. The new brief is retained, not deleted to pass verification.

Retry additionally retains `backups/20261017-current-rollout-snapshot`, SHA-256
`9bb203ec72799e792b231e239ca06261d88c07afb8b5726e25894ba9bc53ff31`. It is a quiesced dump with a successful
archive-list check, not a newly restore-tested format-3 backup; no COMPLETE marker
is created. The retry verifies the narrow recorded one-row delta, checks its
baseline before replacement, and requires exact equality after rollout and browser
checks. All 109 table fingerprints remain unchanged in that final acceptance window.
The source, financial, portfolio and valuation records were not rewritten.

Normal backend/workers now run parser v5, with October 13 frontend unchanged.
Original PostgreSQL volume, schema `s1s1s1s1s1s1`, in-memory provider/auth settings
and localhost-only ports 3000/8000/5432 are preserved. Daily Brief scheduling
resumes; source refresh and pgAdmin stay stopped with restart=no. Old application
registrations are removed only after final acceptance; rollback images remain.
Protected environment files were never read by these recipes.

## User steering, resource scope and release gates

The user reconfirmed no encrypted off-device destination or genuine activity
records. They later requested no new disposable datasets and routine checks on
existing data. The completed local test stacks were stopped; their six temporary
registrations and two networks were removed without volumes. The prepared new
populated-backup rehearsal was not run. Existing records are preserved; checks
requiring database replacement remain open. Remote GitHub CI remains isolated
and consumes no local Docker resources.

The Mac firewall still reports disabled; FileVault status could not be determined.
No host settings or credentials were changed. Three normal-service samples total
617.7-618.0 MiB RAM and 0.43%, 0.30% and 31.33% Docker CPU, where 100% is one core.
The last sample is a brief activity spike, not proof of sustained idle load or a
future usage guarantee. Only the four normal services remain running.
Pruning unused build cache older than 24 hours reclaims 2.567 GB. Docker reports
24.34 GB images, 3.114 GB volumes and 8.068 GB cache afterward; images/cache share
layers, so these totals must not be added. The Mac reports 27 GiB available.
No persistent-volume or rollback-image prune was performed.

M10 preparation is under `output/milestones/m10/release-readiness-20261017`.
Its actual-use log has zero completed days and blank dates, with no scheduled
automation. Reviewed-input freeze, remaining rehearsal, five actual business days,
encrypted off-device recovery and final user acceptance remain open. These are
not engineering tasks that synthetic data or elapsed idle time can close.

## Publication

Publish only the two parser/test paths and seven affected current documentation
owners plus this checkpoint, through an isolated index. Preserve the shared index
and unrelated checkout changes. Keep the stacked [PR #2](https://github.com/Gittastic112/Marketagent/pull/2)
draft; the PR and local publication receipt own the final head and CI result.
No merge or public deployment is authorized by these local checks.

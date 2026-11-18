# Current State

Source and local installation updated November 18, 2026. Recorded results below identify
their exact revisions and environments; they do not certify an existing installation.

## Product position

An implemented local equity-research, valuation, and portfolio application with
source traceability and explicit review gates. The approved first release is
research/demo. It is not accepted as a finished daily-use product or ready for
public hosting. [Scope and limitations](limitations.md)

| Area | Delivered behavior |
|---|---|
| Research and evidence | Company identity, SEC/RSS intake, source documents, reviewed financial candidates, thesis notes, events, and stored-evidence search |
| Daily Brief | Source-linked deterministic brief, portfolio context, visible coverage limits, private text/PDF inbox, optional AI triage, and separate review queues |
| Valuation | Reviewed drafts, versioned FCFF and specialized models, scenario/sensitivity diagnostics, reverse DCF, and owner-reviewed peer comparisons |
| Portfolio | Recorded activity replay, dated snapshots, returns, attribution, benchmark comparisons, and fixed-weight price risk with incomplete-input states |
| Governance | Processing Runs, source/freshness metadata, explicit external-AI consent, exact-citation review, and retained decision receipts |
| Adapter Research Lab | Explicit market/source actions, optional financial/table libraries, hypothetical allocation/simulation, versioned reports and reference peer discovery; [setup and boundaries](adapters/README.md) |
| Runtime | Production-built Next.js/FastAPI/PostgreSQL services, local sign-in, signed internal identity, readiness checks, and backup/recovery tooling |

The [feature register](roadmaps/feature-register.md) owns detailed status. The
[architecture](architecture.md) and [code map](code-map.md) own implementation
boundaries. Experimental and unavailable methods remain labeled.

## Dated validation

Company price history uses a single stored closing-price series at a time. Moves of at least 5% are marked against the preceding comparable close within seven calendar days. Dated sources and event summaries give context. Private pins record the exact observation on the selected thesis. The original close remains readable on that thesis after a provider correction.

These are recorded results for the cited revisions and environments. Automated
cleanup checks do not extend financial, provider, installed-runtime, or daily-use
acceptance.

| Date and scope | Recorded evidence |
|---|---|
| November 18, final publication and cleanup | [PR 20](https://github.com/Gittastic112/Marketagent/pull/20) merged as `9bc78cc`; its tree matches checked head `ece06a6`. [All seven hosted gates passed](https://github.com/Gittastic112/Marketagent/actions/runs/44407169031): 2,256 core backend tests (37 profile skips), 137 installed optional-adapter tests, 422 frontend cases and 89 browser workflows, plus security and recovery checks. Both source histories remain intact and `main` stays default. Final cleanup supersedes the intermediate Docker totals in the receipt: four containers, four essential images totaling 3.726 GB, zero build cache, one 7,049,596-byte restore-tested backup set. About 7.0 GB reclaimed across images, stopped build containers, old backups, browser recordings and temporary copies. Original data/source evidence remains; 31 empty old backup directories remain because macOS denied directory removal, with no backup payloads inside. Private local configuration and credentials were excluded from publication; private GitHub author identity was verified and the browser was signed out. |
| November 18, next ten workflow repairs | Saved-receipt integrity, cursor history, audited failures, provider choices, input/receipt scope, company drafts, candidate links, benchmark units, revision conflicts and one-backup retention are installed. 2,273 backend checks pass, with 20 PostgreSQL checks separately; 422 frontend cases, TypeScript, 39 contracts, 103 repository checks and ten desktop/mobile browser cases pass. All 110 table and original-asset fingerprints are unchanged. The single current format-3 backup was restored and matches those fingerprints. [Latest receipt](../data/reviews/review-adapter-workflows-ten-sets-20261118.json) owns cleanup and publication status. |
| November 18, combined UI/adapters and source verification | Installed Geist/PR20 integration, accessibility/search repairs and PDF parser v8. 2,244 core backend tests pass (37 profile skips), plus 125 optional-adapter checks; 418 frontend tests, TypeScript, contracts, 109 repository checks, production builds and 20 disposable PostgreSQL checks pass. All 86 standard browser cases have passing final results across runs; 221 route/viewport/theme states and focused repair checks pass. The signed-in in-app browser verifies selected desktop/mobile workflows in both themes. Original-source runs verify peers, an SEC amendment/deduplication, an NSE action, ALFRED revisions, OpenFIGI ambiguity and native PDF/Camelot evidence. Installation fingerprints are unchanged; source additions preserve prior financial evidence, valuations and portfolios. The [receipt](../data/reviews/ui-adapter-release-20261118.json) owns exact identities, repairs, data changes, failures/rechecks and cleanup. [Remaining prerequisites](limitations.md#installed-adapters-and-remaining-source-prerequisites) stay held; GitHub remains deferred. |
| November 17, combined local source | Merged Geist and the ZIP's 173 PR paths with the later November 16 repairs. Search, navigation and the Research Lab share the same shell. See the [integration checklist](roadmaps/ui-adapter-worklist.md) for checks on this tree and release gates. |
| November 17, upstream adapter branch | [CI run 44228408999](https://github.com/Gittastic112/Marketagent/actions/runs/44228408999) passed for PR head `33df697`. The [adapter receipt](adapters/verification.md) identifies the optional-library fixtures, provider samples and runtime scope. |
| November 16, research/recovery repairs | Remaining nine R7/R8 repairs plus D1/D2 installed locally. 2,127 backend, 400 frontend and 12 PostgreSQL checks pass; all 80 browser cases have passing final results across recorded runs. Installed read-only checks confirm the readable thesis review layout. Original records in 109 data tables, stored assets, settings, volumes and existing backup are preserved through the additive migration. One pre-change archive is validated, not restored. GitHub remains deferred. [Receipt](../data/reviews/review-research-recovery-nine-sets-20261116.json) |
| November 16, evidence/workflow repairs | Ten further repairs installed locally; backend, frontend, concurrency and production-build checks pass. All 73 browser cases are verified across the full run and three documented reruns. Existing data and essential recovery material are unchanged. GitHub publication is deferred by the user. [Receipt](../data/reviews/review-evidence-workflows-ten-sets-20261116.json) |
| November 15, review releases | Both ten-repair batches are installed and merged in [PR 18](https://github.com/Gittastic112/Marketagent/pull/18) and [PR 19](https://github.com/Gittastic112/Marketagent/pull/19). All seven hosted gates pass on the final source: 2,101 backend tests (15 skipped), 395 frontend tests, 71 browser workflows and seven PostgreSQL checks. Today places the portfolio overview, daily brief and alerts before the six-item research queue; installed desktop/mobile checks pass. All 110 tables, asset bytes, settings and volumes are preserved; no PostgreSQL restart or new backup. [Release and cleanup checkpoint](archive/checkpoints/2026/review-financial-integrity-release-2026-11-15.md) |
| November 15, returned code-review intake | All 39 primary findings checked against main at `6505082`; review severities retained as 1 critical, 13 high and 25 medium. Five finding IDs locally reproduced with isolated Mock Data or shell argument inspection: A3-1, A1-F9, A2-1, A2-8 and A4-2. The migration metadata forms one connected 73-revision chain; this does not prove populated upgrade safety. No HTTP authentication, PostgreSQL restore, browser or deployed-data incident proof was added at intake. All repairs were open at that checkpoint; the [ledger](limitations.md#returned-code-review) owns current status. [Sanitized evidence receipt](../data/reviews/code-review-intake-20261115.json) |
| November 14, dependency and full-suite follow-up | OpenTelemetry API 1.45.2 and Soup Sieve 4.1.1 are installed. Hash-verified dependency audit reports no known vulnerabilities; 1,963 backend tests pass, seven PostgreSQL-only cases skipped in this isolated SQLite run. Four rate/industry-mix tests now exercise explicit refresh and verify that reopening preserves existing inputs. Draft return-link sizing and bounded thesis-table scrolling are repaired and checked in the installed browser; 393 frontend tests, type checking and production build pass. Nine browser specs follow current navigation and explicit actions without weakening their assertions. All 110 tables, settings and recovery material remain unchanged; four containers/four essential images remain, with zero build cache. [Receipt](../data/reviews/dependency-security-20261114.json) · [Hosted checks on PR 17](https://github.com/Gittastic112/Marketagent/pull/17) |
| November 14, ten workspace slices | Dated evidence, annual period/basis snapshots, draft readiness, saved-model preview/version history, bounded Today/holdings queues, thesis selection and library/secondary navigation. 263 backend checks, 27 final focused checks and seven PostgreSQL checks pass, including concurrent duplicate saves; 393 frontend tests, type checking and production builds pass. The [receipt](../data/reviews/research-workspace-ten-sets-20261114.json) records browser verification, installation and preservation. These are bounded slices, not completion of every P2-P5 acceptance case. |
| November 13, research workspace P2.1/P2.2 | Explicit draft/discovery commands, atomic annual-period guards, separate missing-date confirmation, visible revisions, and corrected SEC filing listing are installed. 145 backend checks plus 25 focused filing checks pass; 383 frontend tests, type checking and production builds pass. Isolated Mock Data browser creation/retry/promotion and signed-in normal-app desktop/mobile checks pass. All 110 normal database tables are unchanged; no new backup or permanent stack. [Receipt](../data/reviews/research-workspace-p2-20261113.json) |
| November 13, research workspace P0/P1 | Four primary destinations, five company sections, bounded company summaries, compact financial amounts with exact disclosures, visible quote timing, and saved-model-first valuation pages are installed. 378 frontend tests, type check, production build and authenticated desktop/phone checks pass. All existing records are preserved; one existing Filings discovery audit was added with zero imports. All 110 tables are unchanged through installation. Four containers/four essential images/two volumes remain; build cache is zero and no new backup was made. [Receipt](../data/reviews/research-workspace-p1-20261113.json) |
| November 13, November 12 valuation basis | User date recorded; eight issuer filings and four dated company research notes added. 33 numeric facts, eleven exact passages, seven Nasdaq historical prices and one ECB rate support 23 calculations. Facts, estimates and held values remain separate. All prior records and 107 unrelated tables are unchanged; annual facts and saved valuations are preserved. Display status and paragraph formatting use existing note controls. [Receipt](../data/reviews/valuation-inputs-asof-20261112.json) |
| November 13, dated source follow-up | Four original filings added through two successful Processing Runs. Five exact passages and four period-specific XBRL facts verified; no annual values promoted. All prior source/run rows and 108 unrelated tables unchanged. The original-source link now works on unparsed document pages and existing candidate evidence. 372 frontend tests, type checking, production builds and five signed-in browser checks pass; all 110 tables unchanged through the frontend-only installation and browser checks. [Receipt](../data/reviews/financial-source-followup-20261112.json) |
| November 12, remaining five inputs | All twenty company/input slots examined. 47 original-source facts/calculations added; twelve annual values close four slots. Apple/NVIDIA reach 10/13 source-linked fields per year; Meta/Alphabet remain 8/13. 85 numeric-cell checks, twelve source-passage checks, twelve cross-checks and 120 normalization comparisons agree. Eight signed-in UI checks pass. All 591 prior candidates, 409 metrics, 409 revisions and sixteen original documents remain unchanged; 103 unrelated tables match, and all 110 tables remain unchanged through browser verification. [Receipt](../data/reviews/financial-five-input-review-20261112.json) |
| November 12, authorized Docker cleanup | 151 stopped containers and obsolete images/cache removed; four running containers and four images remain. Data from inactive volumes and container evidence retained in verified archives. All 110 database tables unchanged; retained images execute and the runtime remains healthy without restart. Host free space increased by about 50.9 GB during cleanup. [Receipt](../data/reviews/docker-storage-cleanup-20261112.json) |
| November 12, financial completion review | All eleven selected holds resolved: eight original-filing zeros promoted and three ambiguous debt mappings rejected while retaining their principal values separately. Another 143 source-linked historical facts/calculations are added. Thirty-six source cross-checks and 108 normalization comparisons agree. 372 frontend tests, 56 focused backend tests, 29 contract checks, type checking and production builds pass. All 448 prior candidates, 258 prior metrics and 258 prior source revisions are retained; only the intended eleven candidate review fields change. Saved models and 104 unrelated table fingerprints remain unchanged. [Receipt](../data/reviews/financial-review-completion-20261112.json) |
| November 12, source review and installed repairs | 181 initial promotions plus five original-report follow-ups; 75 comparable normalized checks agree for NVIDIA, Meta and Alphabet. 56 focused backend tests, 370 frontend tests, type checking and production builds pass. Signed-in checks cover 19 main pages at desktop and mobile sizes plus selected evidence, financial and valuation workflows. Unique Compose registration and unchanged fingerprints for all 110 tables verify deployment preservation. [Checkpoint](archive/checkpoints/2026/handoff-review-2026-11-12.md) |
| November 9, PR9 clean checkout | 1,936 backend tests passed, six skipped; 365 frontend tests, TypeScript, production builds, six PostgreSQL integration tests, and 71 browser workflows passed. Five GitHub jobs passed on the reviewed head. [Run](https://github.com/Gittastic112/Marketagent/actions/runs/42667448574) |
| November 9, local product follow-up | 87 focused backend tests plus a 15-test preview follow-up; fifteen desktop/mobile observations with targeted preview/thesis checks. Initial failed attempts remain in the [checkpoint](archive/checkpoints/2026/portfolio-ui-2026-11-09.md) |
| November 9, installed stack | Scoped rollout preserved database/asset fingerprints, mounts, settings, and localhost ports. One explicitly refreshed brief remained unreviewed. [Analyst evidence](archive/checkpoints/2026/analyst-workflows-2026-11-09.md) |
| November 7, dependency/container/recovery | Recorded repository gates, dependency checks, OS-image scans, and isolated recovery passed. Unfixed scan findings remain disclosed; this is not a clean security certification. [Checkpoint](archive/checkpoints/2026/product-development-2026-11-07.md) |
| October 17, recovery | Format-3 concurrent-write recovery checked both PDF stores and 109 tables. Later populated-backup rehearsal remains unrun; same-disk copies do not prove off-device recovery. [Checkpoint](archive/checkpoints/2026/release-readiness-2026-10-17.md) |
| November 11, efficiency PR13 | All seven CI jobs passed at `27c0e007`; merged source tree is identical at `44be93b9`. 1,934 backend tests passed, six skipped; 363 frontend tests, six PostgreSQL integration tests, 71 browser tests, TypeScript/builds, security and recovery checks passed. [Run](https://github.com/Gittastic112/Marketagent/actions/runs/43100927562) · [Checkpoint](archive/checkpoints/2026/repository-efficiency-2026-11-11.md) |
| November 10, cleanup PR10 | All five CI jobs passed at `dab84f01`: repository checks, full backend/frontend baseline, browser workflows, dependency/container security, and isolated recovery. [Run](https://github.com/Gittastic112/Marketagent/actions/runs/42952104760) · [Cleanup checkpoint](archive/checkpoints/2026/repository-presentation-2026-11-10.md) |

Earlier financial/provider reviews and normal-browser observations remain in
[dated checkpoints](archive/checkpoints/2026/README.md). Mock Data browser tests
do not establish genuine portfolio accuracy, source completeness, or actual use.

The [November 11 maintenance follow-up](archive/checkpoints/2026/repository-maintenance-2026-11-11.md)
records subsequent documentation/tooling cuts, source inventories, and CI changes.
It changes no financial acceptance gates.

## Latest product changes

- The [adapter batch](adapters/README.md) adds owned, hashed research run exports,
  bounded compute/extraction workers, explicit provider inspection, generated
  adapter contracts and optional locked dependency profiles. It adds no migrations
  or automatic financial approval. Next.js is patched to 16.4.5. The combined
  release is installed with the analysis and Camelot profiles. Original-source
  validation candidates remain unapproved; prior reviewed histories and saved
  valuation inputs are unchanged. The PDF v8 repair retains incorrect new v7
  share-count candidates as rejected evidence rather than rewriting them.
- All four companies have three selected reviewed annual histories. No selected
  candidate remains pending; Apple/NVIDIA operating checklists are 10/13 source-linked
  per year and Meta/Alphabet remain 8/13. The [current ledger](limitations.md#selected-company-review-follow-up)
  separates every remaining source gap from date/methodology choices.
  Original borrowing, lease, cash-flow, share/award and business-revenue components
  retain precise accounting scope. The evidence UI exposes claim types, periods,
  review limits and source links. Local repairs preserve new override history and
  User Assumption labels after promotion; lost historical origin is not fabricated.
  Installed source-history contracts also accept User Assumption.
  Unparsed document detail pages also expose the original-source link. Later filings
  retain their own dates and periods; existing saved valuations remain unchanged.
- Research lists sort newly ingested documents separately from publication dates.
  Event search links select their record, narrative impact uses the 100-point
  scale, and missing scores stay unavailable. Company/source names, compact
  numbers, collapsible intake forms and mobile wrapping improve the installed UI.
- The dashboard defaults to a funded owned portfolio, supports a URL selection,
  and distinguishes uncalculated impact from zero. Values retain snapshot dates.
- Daily Brief separates Sample provenance from missing inputs. Unmatched filing
  sections are informational baselines; optional intake/schedule controls are collapsed.
- Thesis categories, importance, falsification criteria, and paragraph breaks
  round-trip through the editor. Fractional cash uses storage-consistent rounding.
- Three-year financial review plans link gaps and conflicts to existing review
  actions. Source counts do not certify financial completeness.
- Macro calculations use explicit finite, chronological inputs. Constant factors
  and incomplete full-company totals stay unavailable.
- AI review adds bounded numeric/period/instruction cues and required reasoning
  for flagged claims. Citation edits reset approval and retain the prior receipt.

## Research and runtime evidence

Sample research and hypothetical holdings must stay labeled. Sourced valuations
remain Estimates with explicit assumptions. Automated checks do not establish
complete disclosures, genuine transactions, or current installation status.

The source migration head is documented in the [schema map](database-schema.md).
[Operations](operations.md) owns installed-runtime and recovery procedures.
Keep original sources, review receipts, backups, and historical evidence.
The independent knowledge base retains its immutable originals and audit ledger.

## Acceptance and next priorities

M01-M04 are accepted: **40 of 100 milestone gate points**, not 40% of engineering
effort. M05 remains next. The [completion tracker](roadmaps/completion-tracker.md)
preserves exact gates and explicit deferrals. No new acceptance points are earned
by reorganizing documentation.

Next: address the residual boundaries in the
[review sequence](roadmaps/product-roadmap.md#review-repair-sequence). GitHub publication is authorized for the installed combined tree; the latest receipt supersedes earlier deferrals.
Preservation, financial validation, ownership and recovery defects precede new features.
P0/P1 and bounded P2-P5 slices remain delivered, with the newly recorded limitations;
passing earlier suites did not cover these cases. Saved-version export now uses an owner-scoped raw archive endpoint, separate
from the current read-time interpretation. Historical calculations remain unverified.
The [workspace plan](roadmaps/research-workspace-plan.md) resumes after the repair gates;
dated source proposals, initial-model preview and wider period support remain open.
No acceptance gates advance from this review or its documentation integration.
Continue supported financial/model reviews within the selected scope. New provider
coverage requires permitted inputs before expansion.
Actual-use acceptance remains outstanding. Host/off-device protection and genuine
portfolio proof retain their separate scope boundaries.

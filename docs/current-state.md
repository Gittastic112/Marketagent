# Current State

Documentation reconciled November 10, 2026. Product validation below keeps its
original dates. [PR9](https://github.com/Gittastic112/Marketagent/pull/9) merged on
November 9 at `9f17dd6a`; the local checkout contains additional uncommitted history.

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
| Runtime | Production-built Next.js/FastAPI/PostgreSQL services, local sign-in, signed internal identity, readiness checks, and backup/recovery tooling |

The [feature register](roadmaps/feature-register.md) owns detailed status. The
[architecture](architecture.md) and [code map](code-map.md) own implementation
boundaries. Experimental and unavailable methods remain labeled.

## Dated validation

These are recorded results for the cited revisions and environments. Documentation
cleanup does not rerun or extend product, provider, security, or financial validation.

| Date and scope | Recorded evidence |
|---|---|
| November 9, PR9 clean checkout | 1,936 backend tests passed, six skipped; 365 frontend tests, TypeScript, production builds, six PostgreSQL integration tests, and 71 browser workflows passed. Five GitHub jobs passed on the reviewed head. [Run](https://github.com/Gittastic112/Marketagent/actions/runs/42667448574) |
| November 9, local product follow-up | 87 focused backend tests plus a 15-test preview follow-up; fifteen desktop/mobile observations with targeted preview/thesis checks. Initial failed attempts remain in the [checkpoint](archive/checkpoints/2026/portfolio-ui-2026-11-09.md) |
| November 9, installed stack | Scoped rollout preserved database/asset fingerprints, mounts, settings, and localhost ports. One explicitly refreshed brief remained unreviewed. [Analyst evidence](archive/checkpoints/2026/analyst-workflows-2026-11-09.md) |
| November 7, dependency/container/recovery | Recorded repository gates, dependency checks, OS-image scans, and isolated recovery passed. Unfixed scan findings remain disclosed; this is not a clean security certification. [Checkpoint](archive/checkpoints/2026/product-development-2026-11-07.md) |
| October 17, recovery | Format-3 concurrent-write recovery checked both PDF stores and 109 tables. Later populated-backup rehearsal remains unrun; same-disk copies do not prove off-device recovery. [Checkpoint](archive/checkpoints/2026/release-readiness-2026-10-17.md) |
| November 10, repository cleanup | Documentation and file-hygiene checks only. Exact results and unavailable checks are recorded in the [cleanup checkpoint](archive/checkpoints/2026/repository-presentation-2026-11-10.md) |

Earlier financial/provider reviews and normal-browser observations remain in
[dated checkpoints](archive/checkpoints/2026/README.md). Mock Data browser tests
do not establish genuine portfolio accuracy, source completeness, or actual use.

## Latest product changes

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

The latest authorized research scope, recorded November 9, is four technology
companies with hypothetical holdings and Sample analyst research. The sourced
Apple valuation is a separate Estimate. Three-year input checks do not establish
every disclosure or real transactions. This page does not inspect today's database.

The historical 12-company universe and eleven scenarios were removed November 5.
Sixty named historical backup archives were deleted with explicit approval on
November 9. Historical review counts remain evidence, not current data or setup
instructions. Newer backups, sources, and receipts remain retained.

The source migration head is documented in the [schema map](database-schema.md).
The last recorded installation uses the existing PostgreSQL volume and the
November 9 application images; [Operations](operations.md) owns those details.
The independent knowledge base retains its immutable originals and audit ledger.

## Acceptance and next priorities

M01-M04 are accepted: **40 of 100 milestone gate points**, not 40% of engineering
effort. M05 remains next. The [completion tracker](roadmaps/completion-tracker.md)
preserves exact gates and explicit deferrals. No new acceptance points are earned
by reorganizing documentation.

Next work follows the [roadmap](roadmaps/product-roadmap.md): complete supported
financial/model reviews within the selected scope, establish permitted provider
inputs before expansion, and record actual research use and final acceptance.
The user-reported zero actual-use days remain unresolved. Host/off-device
protection and genuine portfolio proof retain their separate scope boundaries.

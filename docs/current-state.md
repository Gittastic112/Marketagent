# Current State

Source validation updated November 11, 2026. Recorded results below identify
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
| Runtime | Production-built Next.js/FastAPI/PostgreSQL services, local sign-in, signed internal identity, readiness checks, and backup/recovery tooling |

The [feature register](roadmaps/feature-register.md) owns detailed status. The
[architecture](architecture.md) and [code map](code-map.md) own implementation
boundaries. Experimental and unavailable methods remain labeled.

## Dated validation

These are recorded results for the cited revisions and environments. Automated
cleanup checks do not extend financial, provider, installed-runtime, or daily-use
acceptance.

| Date and scope | Recorded evidence |
|---|---|
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

Next work follows the [roadmap](roadmaps/product-roadmap.md): complete supported
financial/model reviews within the selected scope, establish permitted provider
inputs before expansion, and record actual research use and final acceptance.
Actual-use acceptance remains outstanding. Host/off-device protection and genuine
portfolio proof retain their separate scope boundaries.

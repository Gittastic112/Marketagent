# Provider, Assumed Portfolio and Architecture Checkpoint

Date: 2026-09-21. Current limits remain in the [single ledger](../../../agent_capabilities_and_limitations.md).

## Scope and authority

The user requested a Gemini-key check, accepted up-to-20-minute Google Sheets
quotes, requested an AAPL/GOOGL portfolio and prioritized product integrity and
architecture. They explicitly chose 200 shares each at January 2, 2024 closing
prices and confirmed a matching initial deposit, zero fees, no later trades and
dividend exclusion. These are User Assumptions, not broker executions.

The existing large dirty worktree and untracked files were preserved. Changes
span more than ten files because the work crosses provider transport/configuration,
audited ingestion/routes, private downstream ownership, contract compatibility,
regression tests and their current operating documentation. These are separate
behavioral increments, not a cosmetic folder reorganization. No new dependency,
schema revision or public deployment was introduced in this batch.

## Structural issues and repairs

- Gemini's hardcoded model returned 404 despite a valid key. Model selection now
  uses GEMINI_MODEL; the local setting is gemini-3.5-flash-lite. All generation
  methods share a header-authenticated transport, join public text parts, reject
  unfinished output and sanitize failures without exposing key-bearing URLs.
- A configured key was being treated as provider capability. The explicit fixed
  probe now records provider/model, prompt version, input hash, timing and safe
  failures. Health uses current-model probe evidence and does not recognize
  unsupported OpenAI/Anthropic keys as an implemented AI adapter.
- Quote/history and quote-only routes duplicated workflow logic. A single
  market_data/ingestion service owns run creation, fetch, persistence and
  caller-owned price alerts. Configuration failures are audited, same-date
  writes are flushed before duplicate lookup, and downstream failure rolls back
  prices while retaining a failed run. History requests accept 1-3,650 days.
- The one-adapter factory no longer reports a misleading fallback wrapper.
- Price divergence used globally latest private models/portfolios. It now scopes
  models, deduplication and impacts to the caller, rejects stale/weak/mismatched
  evidence, and describes a saved-estimate gap rather than an opportunity.
- Portfolio contracts were buried in the legacy HTTP facade. Thirty-four
  classes and one Literal alias now live in app/schemas/portfolio.py without HTTP,
  ORM or service dependencies. Legacy imports re-export identical classes.
- Additional regressions reproduced global private context in internal portfolio
  valuation, mismatched explicit callers, cross-owner event-alert impacts and
  unrelated company/change-log references. Calculations now derive the persisted
  portfolio owner; event alerts derive the model owner and validate relationships.
  Existing historical outputs/alerts were not rewritten.

## Normal-runtime evidence

Gemini Processing Runs 20-22 record the failed old-model probe, successful model
discovery and successful new-adapter probe. Run 27 succeeded in the rebuilt normal
backend, and provider health reported working for that configured model. Only
fixed connectivity prompts were sent, never company or private portfolio data.
Connectivity is not research-quality, citation or future-quota certification.

Authenticated market imports 23/24 added AAPL and GOOGL history. GOOGL Class A is
company 13, separate from GOOG Class C. The shared issuer identifier is retained
as regulatory_id, without violating the current unique Company.cik constraint or
mixing share-class prices. Issuer/security separation remains architectural debt.

| Saved item | Confirmed basis |
|---|---|
| Portfolio 1 | User Assumption: AAPL + GOOGL, Jan 2024; USD |
| AAPL purchase | 200 shares at USD185.64; MarketPrice 206 unadjusted close 185.639999 rounded to cents |
| GOOGL purchase | 200 shares at USD138.17; MarketPrice 869 unadjusted close 138.169998 rounded to cents |
| Activity | January 2, 2024 deposit USD64,762.00 and two buys; zero fees, no later activity, dividends excluded |
| Cash | USD0 after the two purchases |
| Snapshots | January 2, 2024 and September 18, 2026; both complete |
| Audit | Run 25 assumption setup, run 26 snapshot calculation; transaction IDs 1-3 and snapshot IDs 1-2 |

Source raw-price precision was retained; rounded purchase costs are explicitly
derived assumptions. Snapshot values are USD64,761.9994 and USD137,134.0028 before
display rounding. The period API reported complete TWR, MWR and attribution;
historical risk was complete while aggregate risk/DCF comparison correctly stayed
partial because no trusted company DCF was invented. No benchmark was selected.

Initial coverage, SEC review candidates and existing valuation records were
preserved. Google Sheets research did not create a Sheet or implement a bridge;
the explicitly selected personal Yahoo adapter remains in use. Its latest-quote
timing is unknown, not guaranteed real-time or a guaranteed 20-minute delay.

## Verification and recovery

- Portfolio extraction compared all 266 OpenAPI paths and 476 schema definitions
  exactly. The comparison baseline follows the deliberate market-window validation
  change, not the start of all September development.
- The full backend suite passed after the final ownership increment; the final
  aggregate count is recorded in [Current State](../../../00-current-state.md).
  Focused final owner/portfolio/event/ingestion regressions passed 29 tests.
- Frontend: 214 tests and TypeScript passed. Production frontend, backend and
  scheduler builds passed; normal runtime checks are separate from build evidence.
- Playwright CLI used only the disposable market-intel-architecture-e2e project
  on localhost ports 14000/14001, with a separate tmpfs database and test login.
  Authenticated Mock Data risk reconciled 44 price IDs, 22 FX IDs and two DCF IDs;
  returns, attribution and benchmark responses were complete on the fixture dates.
  UI labels blocked Mock Data from genuine-input certification. Desktop 1280px
  and mobile 390px layouts were inspected, without page overflow or console errors.
  Initial screenshots timed out or captured a stale resized frame; foregrounding
  and reloading resolved capture. Final images remain under output/playwright/
  architecture-2026-09-21. This is focused browser proof, not every-route coverage.
- Backup 20260921T203226Z-market-intelligence passed checksums and dump inventory.
  It independently restored to architecture_restore_check in the disposable
  PostgreSQL service: all 107 table counts matched and revision was p7p7p7p7p7p7.
  It contains 1,549 prices, two holdings, three transactions, two snapshots and
  26 Processing Runs. The later runtime AI probe is outside its snapshot.
  No binary assets existed, so nonempty-asset/off-device recovery is not proved.
- Final backend/scheduler images were deployed after the ownership regressions.
  Authenticated read-only checks returned ready, working AI health, 200 shares of
  each requested stock, USD64,762 cost basis, USD0 cash and complete TWR/MWR.
  Normal ports remain localhost-only and the persistent PostgreSQL volume is
  unchanged. The task-owned browser/recovery containers and tmpfs databases were
  removed; normal data, all backups and screenshots were retained. Documentation,
  secret, workflow and diff-whitespace gates passed after the final source work.

## Remaining boundary

This is not a claim that all product work is complete. The ledger retains
issuer/security separation, historical holding replay, risk-series freshness,
reviewed financial/India coverage, Google Sheets integration and broader
security/evaluation/architecture gaps. No fake facts or silent review promotion
were used to clear those gaps. No commits or unrelated file cleanup were made.

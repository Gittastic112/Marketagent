# Personal Research Release

Verified: 2026-09-21. This is a release receipt, not a claim that the entire
project is finished. Current status lives in [Current State](../../../00-current-state.md);
remaining work and user requirements live in the [single ledger](../../../agent_capabilities_and_limitations.md).

## Scope and implementation

The user selected personal research, US/India, USD portfolio reporting and five
companies per market, with daily closes acceptable and latest prices preferred.
The initial selection uses a dated market-cap snapshot, not an investment ranking.

This batch spans more than ten files because evaluation requires matching
contracts, persistence, ownership, API, UI and migration changes, while valuation
display trust and operational recovery need separate regression boundaries.
It preserves existing module ownership rather than introducing a new framework.

### Specialized valuation workspace

- `frontend/components/advanced-workspace.tsx` removes unreviewed bank/distress
  presets, requires relevant equity inputs for banks, exposes hidden invalid
  controls and discloses currency, monetary scale and common-equity recovery.
- `frontend/lib/valuation-output-state.ts`, `scenario-display.ts` and
  `components/valuation/scenario-range-panel.tsx` apply model-specific display
  gates instead of rejecting bank outputs for missing FCFF operating inputs.
- `frontend/lib/valuation-projections.ts` and
  `components/valuation/saved-projections.tsx` render saved, trusted projections
  with bank-specific labels and relative years. Wide tables scroll inside a
  keyboard-focusable region rather than expanding the mobile page.
- Regression coverage includes projection labels, scenario eligibility and the
  existing saved-output invariants. Saved historical calculations are unchanged.
- `frontend/app/page.tsx` sends creation links to the existing company/thesis forms.

### Executable extraction evaluations

- New backend contracts/service live in `app/schemas/evaluation.py` and
  `app/services/extraction_evaluation.py`. The HTTP router validates/authorizes;
  the service compares a non-writing local text-extractor preview with an exact
  source hash and independently reviewed, complete reference rows.
- Owner-scoped reports persist source/reference hashes, extractor/report versions,
  exact comparisons, precision/recall and numeric/unit/period/locator accuracy.
  Explicit reference review and Mock Data classification are required. No source
  facts are promoted or modified, and no external provider or AI is called.
- Migration `p7p7p7p7p7p7` adds nullable owner/report fields to existing runs.
  Historical unowned rows are preserved, not exposed as another user's reports.
- `/evaluations`, `components/evaluation-workspace.tsx` and `lib/api/evaluation.ts`
  provide the form, source-basis validation, owned history and persisted reports.
- `backend/tests/test_evaluation_execution.py` covers execution, ownership,
  stale references, review, malformed references, classification and atomicity.
  The current text extractor's missing units correctly produce failed matches.

### Personal-use prices and provider configuration

- The pinned yfinance 0.2.37 adapter failed for NVDA and NSE Reliance. An isolated
  1.7.0 comparison succeeded, followed by a clean image with the existing pandas
  pin and the full backend suite. `backend/requirements.txt` now pins 1.7.0.
- `app/providers/market_data/yfinance_provider.py` requests and filters history
  strictly before the current UTC date. Current-day bars cannot be mislabeled as
  completed daily closes; the conservative cutoff is disclosed on each result.
- Latest quotes remain `unknown` timing, with no invented source timestamp or
  delay. The source remains unofficial/personal-use, not guaranteed real-time.
- `backend/tests/test_yfinance_provider.py` covers the cutoff, empty usable history
  and timing honesty without network calls. The two cutoff cases failed before
  the repair and passed afterward.
- Provider health now calls the same SEC contact validator as ingestion. Two
  regressions demonstrated that placeholder emails previously looked configured.
  Before the user supplied the SEC contact, deployed health correctly reported
  SEC/AI as unconfigured and personal prices as working. SEC is now configured;
  AI remains unconfigured. The contact was stored only in ignored local settings,
  not checked-in source, documentation or processing-run metadata.
- The ignored local provider setting was explicitly changed to `yfinance_personal`
  for the user's confirmed personal-use scope. General defaults were not changed.

### Recovery and local network boundary

- Normal and disposable Compose published ports now bind `127.0.0.1`.
  `scripts/test_local_compose.py` protects these bindings.
- A restore drill exposed Docker consuming the input of table-count shell loops.
  Both backup/restore scripts now isolate that input. Restore independently reads
  the restored table inventory and rejects incomplete legacy count manifests
  before restarting the app.
- `scripts/test_backup_workflow.py` uses a fake Docker executable only. Four
  regression cases cover all-table backup, all-table restore, count mismatch and
  incomplete legacy manifests. Failing verification must not restart the app.
- CI and the release-baseline script run the new operational checks. Shell syntax
  checks pass. No normal database restore/drop/reset or volume removal occurred.

## Verification

- Final backend suite: **1,073 passed**, network disabled with read-only edited
  source/data mounts. Five upstream Starlette/anyio and openpyxl warnings remain.
- Frontend: **214 tests** and TypeScript pass. Backend, scheduler and standalone
  frontend production builds pass. The provider update was rebuilt and deployed.
- Static gates: 16 unit tests, 73 active Markdown files and 546 local links,
  secret scan, 11 project workflows and patch formatting pass.
- Fresh PostgreSQL/readiness and a populated predecessor migration pass. The
  populated fixture preserved all old evaluation values, nullable legacy ownership
  and report state, and the new foreign key/index.

The Playwright workflow drove actual forms in a disposable browser environment:

- A Mock Data INR bank saved zero earnings/ROE without irrelevant operating fields.
  Required hidden controls were revealed and focused. Saved output and scenarios
  retained the bank-specific basis and currency.
- A Mock Data distressed case started with blank failure/recovery assumptions.
  Explicit zeros saved a new version with a USD 16 per-share result; the prior
  blank version remained unchanged.
- An evaluation executed through the UI and survived reload. Numeric accuracy was
  100% but exact precision/recall were zero because the real text parser omitted
  units. The report retained Mock Data classification. Missing-source failure and
  recovery were exercised without source/candidate mutations.
- Desktop 1280px and mobile 390px screenshots were inspected. The evaluation form
  has usable full-width controls; the projection table has contained scrolling,
  readable cells and no page overflow.
- Dashboard Write Thesis navigated to the real Add Thesis Note form, not a 404.

Artifacts are under `output/playwright/completion-2026-09-21/` and are local QA
evidence, not financial-source certification. These checks do not certify every route.

## Normal runtime and data

The verified preflight recovery baseline is
`backups/20260921T190042Z-market-intelligence`. Its checksums and dump inventory
passed; it restored into a new disposable PostgreSQL database and upgraded from
o6o6o6o6o6o6 to p7p7p7p7p7p7. All 107 table counts and document-asset count/bytes
matched. There were no binary document assets to exercise.

The earlier `20260921T185153Z` backup has only the first table in its count
manifest. Its database dump was intact, but it is not the verified recovery
baseline. Both backup directories were retained; pruning was disabled.

The normal runtime was upgraded additively and recreated. Its existing persistent
volume remained `market-intelligence-md-filescopy_marketintel_postgres_data`.
Backend, frontend and PostgreSQL health passed; scheduler and pgAdmin were running.
Published ports 3000, 8000, 5432 and 5050 were verified on localhost only.
Before company setup, contents of all 107 tables matched the upgraded backup copy.

Then the authenticated company API added NVDA, AAPL, GOOG, MSFT, AMZN,
NSE:RELIANCE, HDFCBANK, BHARTIARTL, ICICIBANK and SBIN. Existing companies were
preserved. Processing Run 3 records selection sources, the User Assumption scope,
and five failed SEC identity lookups caused by placeholder contact configuration.
No CIKs, financial statements, industry mappings or valuation assumptions were invented.

Processing Runs 4-13 successfully fetched prices for all ten companies through
the canonical ingestion API. The 30-day requested windows produced 205 stored
price rows: 195 completed daily prices and ten latest quotes with unknown timing.
Provider names, USD/INR, observation times and warnings were verified in storage.
The research catalog now has 12 companies, including the two pre-existing rows.

After price setup but before SEC configuration, 103 table-content fingerprints remained identical to the upgraded
backup. Only `companies`, `company_market_data`, `market_prices` and
`processing_runs` differed. Financial, valuation and portfolio tables were unchanged.

The user then supplied a real SEC contact identity. One bounded official ticker
request resolved all five US CIKs; Processing Run 14 records the response hash,
source and identifier updates without storing the contact. Authenticated extraction
requests produced five companyfacts snapshots and these candidate counts:

| Company | Run | Selected fiscal years | Candidates | Missing core metric warning |
|---|---|---|---|---|
| NVDA | 15 | 2022-2026 | 35 | None |
| AAPL | 16 | 2021-2025 | 39 | FY2021 debt |
| GOOG | 17 | 2021-2025 | 38 | FY2021 diluted shares |
| MSFT | 18 | 2022-2026 | 40 | None |
| AMZN | 19 | 2021-2025 | 35 | None |

All five runs succeeded. The 187 candidates remain `needs_review`, with units,
source payload hashes and accession evidence. No normalized snapshots were
created for these companies, no candidates were promoted and no assumptions or
holdings were fabricated. Absence of a core warning is parser coverage, not
complete-statement certification. Provider health reports SEC as configured;
its filing-ingestion status does not aggregate these XBRL extraction runs.
No external AI requests occurred; the Gemini key is absent locally.

Post-ingestion backup `backups/20260921T195839Z-market-intelligence` includes the
prices and SEC sources/candidates at p7p7p7p7p7p7. Its dump is 2,074,878 bytes;
the count manifest has 107 rows. Checksums/dump inventory passed. It has not
independently been restore-tested; the earlier preflight restore proof remains
separate. Pruning stayed disabled. Final readiness returned HTTP 200 with no
missing schema objects; backend/frontend/database remained healthy.

## Handoff

The dedicated browser session and `market-intel-completion-e2e` stack were removed,
including temporary fixtures and restored database copies. Screenshots, the
original database volume and all local backups were retained. Only disposable
test data was removed; original records were not deleted.

The broad dirty worktree was preserved and no commits were created. This release
does not finish every coding/data requirement. Continue from the short handoff
and the single limitations ledger, not from historical task counts.

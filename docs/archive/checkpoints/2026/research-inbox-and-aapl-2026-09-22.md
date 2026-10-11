# Private research inbox, company context and AAPL proof

Date: September 22, 2026. Scoped delivery, not a Bloomberg/Capital IQ feature or
data-coverage certification. Current priorities remain in the handoff and the
single limitation ledger.

## Delivered boundaries

- Daily Brief accepts pasted text and text-based PDFs into immutable, owner-private
  `brief_sources`, not the shared filing catalog. Original PDF bytes, text, hashes,
  source date/URL, extraction method, selected pages and warnings are retained.
- Explicit AI scanning discloses the transmitted source text/date, public company
  name/ticker and valuation-field catalog. It does not send stored holdings, thesis
  notes or valuation values. Every import and scan has a Processing Run; AI output
  retains provider/model, prompt version, input hash, owner and review status.
- Findings are ranked and checked for exact source passages. Fourteen core input
  names are allowlisted; links open and focus the relevant draft field. No source
  approval, numerical edit or saved-model mutation follows from a scan.
- Failed/invalid output is blocked and retryable. Completed scans are idempotent;
  interrupted scans can be retried after two minutes. Exact matching is not
  semantic verification of the model's interpretation or financial definitions.
- Company and portfolio views show bounded, dated annual Item 1 excerpts with
  source links. A dedicated Comps tab exposes the existing reviewed-peer workspace.
  No new market-data subscription or invented peer multiples were introduced.

## Architecture and owning files

Intake/AI workflow, PDF extraction, contracts, HTTP routing and persistence have
separate owners: `services/brief_sources.py`, `services/brief_source_extraction.py`,
`schemas/brief_sources.py`, `api/routers/brief_sources.py`, and
`models/brief_source.py`. Migration q8q8q8q8q8q8 is additive. Registrations,
runtime readiness and binary-response contracts were updated together.

Frontend ownership is `components/brief-source-inbox.tsx`,
`components/brief-source-findings.tsx`, `app/daily-brief/sources/[id]/page.tsx`,
`lib/api/brief-sources.ts` and `app/research.css`. The authenticated proxy permits
45 seconds only for explicit source scans; ordinary requests keep their shorter
timeout. Valuation draft deep links open parent sections but do not write values.

Company business context uses `services/company_research.py`, its narrow router,
`lib/api/company-research.ts` and shared `components/company-research-cards.tsx`.
One windowed query selects only requested identities and bounded excerpts, not
whole filing/ORM graphs. Quarterly Item 1 statements are not business profiles.
Comps navigation uses longest-path matching so Valuation is not also selected.

No dependencies were added. Existing pdfplumber and provider infrastructure were
reused. Real Apple input exposed an indirect PDF stream reference that fixtures
had not covered; extraction now resolves it and has a regression test. Huge page
ranges are rejected before allocating their expanded range. Gemini rejected the
combined nested enum/array provider grammar; the request now uses structural JSON
grammar while local Pydantic validation retains the full strict field contract.

## Real-source and calculation evidence

- Demo mode was already off. Real configured `gemini-3.5-flash-lite` successfully
  scanned Apple's four-page FY2025 statement PDF in both the isolated browser
  workflow and normal runtime. Normal source ID 1 / AI output ID 2 has five
  findings, valid exact citations, `is_mock=false` and pending review.
- Only the public Apple source was transmitted. The normal result links revenue,
  operating margin, cash/non-operating assets, borrowings and diluted shares.
  Directions compare reported source context, not the user's undisclosed model.
- Official annual business filings were imported and parsed without generating
  financial candidates or approving facts: Apple document 8 (47 sections) and
  Alphabet document 9 (79 sections). Profile selections are section 16 and 64,
  filed October 31, 2025 and February 5, 2026 respectively. Two audited source
  import runs succeeded; broad profile/India coverage remains incomplete.
- The deterministic Quick Valuation engine ran three non-saving Apple cases.
  The central illustrative result is USD106.01/share, with USD120.76 and USD94.31
  when starting/terminal WACC and terminal ROIC move together to 8% and 10%.
  Reported FY2025 inputs were reconciled to visually inspected statement pages.
  Forecasts, tax, discount rate and accounting simplifications are explicit
  assistant-selected estimates, not user-approved assumptions or current fair value.

The [AAPL report](../../../../output/playwright/research-inbox-2026-09-22/AAPL-valuation-proof.md)
and [exact inputs/results](../../../../output/playwright/research-inbox-2026-09-22/aapl-illustrative-valuation.json)
record units, fiscal basis, share definition, forecasts and sensitivity scope.
No saved model, reviewed input, draft or portfolio record was changed by the run.

Official sources:

- [Apple FY2025 statement PDF](https://www.apple.com/newsroom/pdfs/fy2025-q4/FY25_Q4_Consolidated_Financial_Statements.pdf)
- [Apple FY2025 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)
- [Alphabet FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)

## Validation and recovery

The source-mounted, network-disabled full backend suite passed 1,178 tests with
five upstream deprecation warnings. Frontend passed 223 tests and TypeScript.
Production backend, frontend and both worker builds succeeded and were deployed.
Normal readiness reports q8q8q8q8q8q8 with no missing schema elements; published
ports remain bound to 127.0.0.1. Static/documentation checks are recorded in
Current State. No broad accessibility or AI-interpretation score is asserted.

The isolated Playwright CLI browser checked:

1. Real PDF intake, original text/page/hash inspection and explicit scan consent.
2. Real Gemini failure display, retry and successful ranked findings, without a
   mock fallback. Earlier failed PDF/provider requests remained visible in the
   browser console and audits; these were diagnosed and fixed, not hidden.
3. Signed-in original PDF retrieval: HTTP 200, application/pdf, private/no-store,
   exactly 4,919,649 bytes and the expected PDF signature.
4. A finding link opened `#starting_revenue`, expanded its parent section and
   focused its input. The fixture's existing zero remained zero, not AI-filled.
5. Mobile pasted-source submission: 1,499 trimmed characters, HTTP 200,
   `not_scanned`, no analysis. Saving alone made no AI call.
6. Comps opened independently of a saved DCF and was the sole active company tab.
7. Portfolio cards rendered for two labeled Mock Data holdings with explicit
   missing business descriptions and company-specific research links.
8. Desktop 1440px and mobile 390px intake/findings checks had no page-wide
   horizontal overflow. Captures were inspected; this is scoped visual evidence.

Evidence files are under `output/playwright/research-inbox-2026-09-22/`.
Public Apple source proof is distinct from synthetic portfolio fixtures.

Preflight backup `backups/20260922T195021Z-market-intelligence` was independently
restored into a disposable database and upgraded from p7 to q8. Fresh q8 schema
also passed. Post-change backup `backups/20260922T202140Z-market-intelligence`
was independently restored: all 108 tables have identical row counts/content
fingerprints, including original PDF bytes, extracted text and AI findings.
Two saved models, four assumption sets, two holdings and three transactions
also retain identical fingerprints to the pre-inbox backup. No backups pruned.

The earlier `market-intel-source-refresh-e2e` test stack was deleted as requested.
The new bounded `market-intel-research-verify` stack was also removed after checks,
including its temporary restored databases. Normal data, backups and captures
remain. This proves local database/PDF recovery, not off-device disaster recovery.

## Remaining work

See the [single limitation ledger](../../../agent_capabilities_and_limitations.md)
for source archive/search, scheduled-brief integration, OCR/visual-table limits,
semantic review, company coverage and valuation-certification boundaries.
The next high-value extension is a coherent multi-source research workflow,
not more isolated valuation engines or silent AI approval.

# W2 source adapters

Baseline: `371b58c02cfd2b80429f28dbc13629165b5e392d`. Work is confined to the W2 allocation. No production database, provider credentials, external provider calls, trades, or deployment were used.

## Implemented boundaries

1. EdgarTools parses bounded SEC CompanyFacts JSON through its actual `EntityFactsParser` API in a single-use worker. Existing SEC acquisition retains issuer validation and SEC identity. Namespace-qualified fact objects map to existing financial candidates with explicit annual/duration, currency, source period, filing date, accession, raw-response hash, and review requirements. Selection excludes later filings from the requested cutoff. Reviewed candidates are not rewritten and no metrics are promoted automatically.
2. Camelot, Docling and Marker have optional PDF extraction adapters over original stored assets. Camelot stream extraction was exercised with the installed package. Model-based parsers require an explicitly provisioned model directory and can run through a separately configured Python executable. Worker output is bounded neutral table/page JSON. The application reuses its existing financial interpretation and period guards. Original PDFs are hash-checked and retained; only new review candidates are written.
3. The original FredProvider gains ALFRED revision retrieval with bounded pagination, as-of and initial-release modes, missing-value preservation, inconsistent-page rejection and explicit partial coverage. The consuming workflow preserves a versioned raw-document snapshot; it does not replace values in the unversioned current macro table.
4. EarningsCall v4 and FMP stable transcript adapters use fixed official endpoints with bounded reads, no redirects/proxies, sanitized provider errors, and no implicit fallback. Call time, publication time and local observation time are separate. Unknown timezone/publication times remain unknown; original fields remain in the payload. Speakers, sections and relative word timings remain traceable. Corrected content creates a new document linked to its predecessor; identical repeats reuse the original. FMP is restricted to a resolved supported US listing before any fetch; international bare-symbol mapping is not assumed.
5. India filing intake normalizes user-supplied original NSE announcement/financial-results and BSE announcement payloads. Company identity, ISIN where present and BSE scrip code are checked. Submission/dissemination times, fiscal period, consolidation/audit flags, original fields and attachment references are retained. Date-only values stay in the original payload with precision warnings and never become invented midnight publication times. No website scraper, BSE authentication scheme or undocumented feed endpoint was added. BSE attachment filenames alone do not produce guessed download locations. Existing manual PDF intake remains the route for original document bytes.

All source actions have an authenticated consuming route and a Processing Run carrying user/company/adapter scope, counts, evidence IDs and safe failures. Each run freezes bounded, whitelisted request options and the company listing snapshot before execution, including failed/duplicate runs and PDF extraction with no candidates. Credentials and raw request bodies are excluded. SEC resolves the effective default cutoff once. A repeated partial ALFRED snapshot remains `partial_success` with truthful fetched/created/duplicate counts; partial actions without usable evidence become unavailable/failed. All outputs use the existing API envelope. Capability reads describe configuration/package readiness, not proof of live access.

## Integration contract

The coordinator registers `app.api.routers.source_adapters.router` and owns Settings/dependency profiles. New Settings are `earningscall_api_key`, `source_adapter_model_dir`, and `source_adapter_python`. The last is an optional absolute server-configured executable used only for Docling/Marker, never a request argument. Its package metadata is checked by a fixed five-second subprocess probe. No installation or model download occurs during requests.

Routes:

| Method | Path | Input |
|---|---|---|
| GET | `/api/source-adapters` | None |
| POST | `/api/companies/{company_id}/source-adapters/sec-facts` | `as_of`, `max_years` |
| POST | `/api/companies/{company_id}/source-adapters/india-filings` | `exchange`, original `records` |
| POST | `/api/companies/{company_id}/source-adapters/transcript` | `provider`, `fiscal_year`, `fiscal_quarter`, optional resolved `exchange`, `level` |
| POST | `/api/source-adapters/fred-vintage` | `series_id`, `as_of`, observation bounds, mode/page budget |
| POST | `/api/companies/{company_id}/source-adapters/documents/{document_id}/extract` | explicit `adapter`, selected original `pages` |

The pure request/result contracts are in `backend/app/schemas/source_adapters.py`. The independent source router is covered in isolated authenticated API tests before coordinator registration.

## Worker constraints

Linux `libseccomp.so.2` is required. `app.providers.extraction.worker.deny_network()` denies socket creation/connect/send syscalls and fails closed if isolation cannot be installed. Other workers can import that function without adopting extraction-specific limits. The extraction worker also has 4 GiB address space, 45-second CPU, 60-second wall, 12 MiB output, 40 MiB input and 20 selected-page limits. Only one extraction is active per API process. No database/provider secrets enter the worker environment. This does not claim a general filesystem sandbox.

Docling/Marker inference is not claimed verified: model artifacts were not provisioned. Missing packages/models produce explicit unavailable errors. The separate interpreter avoids changing core dependency versions merely to satisfy OCR dependencies. The current published Marker 2.2.0 / Surya 0.23 dependency stack conflicts with the coordinator's approved Pillow 13.0.0 and filelock 4.2.12 floor. Marker is excluded from the approved OCR profile. Its wrapper remains implemented, but preflight probes the selected interpreter's Marker, Surya, Pillow and filelock versions and reports `EXTRACTION_DEPENDENCY_CONFLICT` for missing, unsafe or incompatible combinations before model execution. Capabilities report `dependency_conflict` for such installed combinations and describe the known blocker even when Marker is absent. No forced installation or dependency override is performed. Marker merged HTML tables are intentionally not mapped until span normalization can be verified. Unsupported/ambiguous PDF periods remain held by the existing review/promotion guards.

## Evidence and upstream interfaces

The inspected and exercised packages were EdgarTools 6.3.0 and Camelot 2.0.0. Optional source interfaces were checked against Docling 2.150.1 and Marker public converter/config/JSON renderer interfaces; the coordinator verified Marker 2.2.0 as the published release (the repository's 2.2.1 was not published).

Primary interface references:

1. [EdgarTools parser](https://github.com/dgunning/edgartools/blob/main/edgar/entity/parser.py).
2. [Camelot API](https://camelot-py.readthedocs.io/en/stable/api.html).
3. [Docling converter](https://docling-project.github.io/docling/reference/document_converter/) and [pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/).
4. [Marker converter example](https://github.com/datalab-to/marker) and [JSON renderer](https://github.com/datalab-to/marker/blob/master/marker/renderers/json.py).
5. [EarningsCall versioning](https://earningscall.biz/docs/versioning) and [transcript shapes](https://earningscall.biz/docs/transcript).
6. [FMP stable transcript endpoint](https://site.financialmodelingprep.com/developer/docs/stable/search-transcripts).
7. [NSE results payload](https://github.com/BennyThadikaran/NseIndiaApi/blob/main/src/samples/financial_results.json), [NSE announcements](https://github.com/BennyThadikaran/NseIndiaApi/blob/main/src/samples/announcements.json), and [BSE announcements](https://github.com/BennyThadikaran/BseIndiaApi/blob/main/src/samples/announcements.json).
8. [FRED observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html).

This code implements narrow interfaces and mappings; it does not vendor the upstream applications. Preserve package license notices through the coordinator's dependency records.

## Validation

Tests use isolated SQLite and labeled Mock Data fixtures. They cover original/corrected transcripts, missing publication time, speaker/word alignment, NSE/BSE identities and timestamps, real NSE financial-results key casing, atomic failure, repeat imports, ALFRED revisions/missing values/partial pages, source-byte integrity, authentication, audits, safe HTTP failures, missing optional artifacts and selected-interpreter probing. Real installed EdgarTools and Camelot execute against synthetic local evidence inside the bounded child. A separate child verifies kernel network denial.

Recorded checks on November 18, 2026: the follow-up source suite contains 47 tests, including regressions for date-only NSE/BSE values, FMP listing scope, partial duplicates, exact request context, and Marker dependency blocking. A combined source/FRED/SEC/schema-boundary/Processing Run visibility run passed 96 tests. The original 14 selected cross-review regressions failed against the prior implementation before the fixes. Documentation scanner unit tests pass (24); `git diff --check` is clean. `scripts/check_docs.py` in the isolated W2 worktree reports only the coordinator-owned source-router mapping and router-count updates; integration documentation is maintained in the root worktree. No central file was changed from W2.

Test environment: shared Python 3.14.10 virtual environment, source cwd `backend`, dummy PostgreSQL URL for module import, isolated SQLite fixtures, no live database connection. Actual package versions were queried from the installed environment. The model-based parser code and missing-artifact paths are present, but no Docling/Marker inference success is claimed. Transcript intake is an explicit call request; no background transcript polling or automatic guidance approval was added.

The coordinator must reconcile central documentation and run registered-route/security/OpenAPI checks after integration. Genuine filings/OCR quality, paid provider entitlements, live provider compatibility and PostgreSQL concurrency remain distinct from this fixture proof.

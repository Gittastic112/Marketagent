# Research adapters and Research Lab

The three adapter router groups expose 22 operations for market data, source intake and Research Lab. The local application runs the analysis and Camelot profiles. A capability can be implemented while a specific account lacks the entitlement or an installed worker lacks the assets to execute it. [API inventory](#api-inventory) · [Release evidence](../current-state.md#dated-validation)

An adapter can retrieve or parse evidence. A review decision determines whether a financial candidate enters the company's reviewed history. Research Lab uses supplied returns for its calculations. The [16-package worklist](../roadmaps/ui-adapter-worklist.md#implementation-backlog-from-the-zip) identifies the remaining integration work.

## What is implemented

| Area | Implementation | Current boundary |
|---|---|---|
| SEC financial facts | EdgarTools 6.3.0 parses preserved CompanyFacts through a bounded worker and maps eligible annual facts into the existing candidate workflow | Candidates require review; supported concepts and filing cutoffs do not establish complete financial statements |
| PDF tables | Camelot 2.0.0 extracts selected pages; Docling supports separately provisioned OCR dependencies/models; a Marker wrapper is present | Docling inference is unverified here. Marker 2.2.0 is blocked because its Surya dependency requires vulnerable Pillow/filelock versions. Original evidence and review rules remain authoritative |
| FMP market data | US equity profile, quote and explicit dated history | Requires a configured key and suitable provider plan; split-adjusted close is not dividend-inclusive total return |
| Massive | US security reference, last trade, dated daily aggregates, splits and dividends | Entitlements and upstream coverage remain provider-specific; no substitution of a prior close for a missing last trade |
| Official NSE MCP | Protocol initialization, tool-schema validation, JSON/SSE handling, quote/history, dated quote and corporate actions | Dated quotes use actual history-row dates; EQ settlement series only; gaps and unadjusted prices remain explicit |
| India filing metadata | Normalizes supplied NSE/BSE metadata, matches company identity and preserves original disclosure details | Offline metadata intake; no invented BSE account endpoint, scraping, or automatic document approval |
| ALFRED/FRED | As-of and initial-release observations, revision intervals and vintage-specific original units, frequency and seasonal adjustment. Missing vintage metadata yields partial coverage | The original observation pages and dated series responses are hashed together. Initial releases use their own dates, with up to ten metadata dates per request. [FRED series specification](https://fred.stlouisfed.org/docs/api/fred/series.html) |
| EarningsCall/FMP transcripts | Explicit call retrieval with speaker/section locators and corrected versions | Call date, publication availability and first observation are separate; no automatic polling or guidance approval |
| OpenFIGI | Explicit mapping candidates with exchange/MIC and unlisted-equity selection | Ambiguity remains visible; no identity merge or historical-mapping certification |
| Exchange calendars | `pandas_market_calendars` 5.6.1 schedules, finite supported coverage, timezone/early-close handling and source-labeled overrides | Special/weekend Indian sessions need explicit overrides; schedule coverage is not inferred outside the adapter's bounds |
| Portfolio allocation | PyPortfolioOpt minimum variance, maximum Sharpe, HRP, and native equal weights | Fully invested long-only hypotheses; explicit annual expected returns for maximum Sharpe; no use of DCF upside as annual return |
| Simulation | Native compounded buy-and-hold/constant-weight simulations and a real `bt` cross-check | Fixed caller-supplied universe; estimated turnover costs in native mode; `bt` cross-check requires zero costs; no broker execution |
| Return reports | QuantStats statistics plus escaped, self-contained HTML and JSON exports | Explicit supplied return/benchmark series; undefined ratios remain null; no implicit price download |
| Peer discovery | Hash-verified FinanceDatabase CSV snapshot, fixed-commit download CLI, bounded local discovery | Returns review candidates only; no peer-set promotion or proof of historical universe membership |
| Interface | Research Lab, explicit source/market controls, capability states, saved runs, metrics/curves and exports | Existing app authentication; no provider requests merely by opening a page |
| Research navigation | Cmd/Ctrl+K palette with separate company lookup and stored-evidence search | Searching does not create a company or a watchlist; response races are scoped |
| Memo display | Markdown/GFM, safe links, evidence-linked citation resolution and artifact-bound Markdown download | Canonical memo text and saved basis remain separate; this does not close the broader saved-editor/reconciled-export review findings |
| Price/FX review | Row filtering, error navigation and exact-file preview/apply behavior | This is the existing price/FX evidence importer, not a brokerage transaction importer |
| Contracts/configuration | Strict Pydantic inputs, adapter OpenAPI subset, generated TypeScript, pinned profiles and saved run manifests | Generated types supplement runtime validation; credentials are never embedded in requests or exports |

The existing market provider factory remains the only selection authority. `MARKET_DATA_PROVIDER` explicitly selects `alphavantage`, `fmp`, `massive`, `nse_mcp`, or `yfinance_personal`. There is no silent fallback provider. The inspection APIs preserve evidence but do not write accepted current prices, holdings, or security identities. Existing market ingestion remains the write workflow.

## Start in the application

Open `/research-lab` in the signed-in app. Select the operation, provide its explicit inputs, inspect capability and coverage messages, and submit. Research calculations save an owned Processing Run with normalized inputs, output, hashes, adapter identity, dependency versions and qualifications. Saved JSON downloads carry the same input/output pair shown in the result.

The lab accepts research return matrices. Each row describes one shared start/end interval for every asset. Returns must already be in the declared base currency. Missing observations are not filled, mismatched intervals are rejected, and currency conversion is not guessed. A declared `total_return` series is a caller assertion; the app does not establish it from a split-adjusted price label.

Allocation requires at least two assets and at least `max(20, number_of_assets + 1)` observations. Maximum 40 assets and 2,600 observations are accepted. Equal weights work with the core dependencies. PyPortfolioOpt supplies the other three methods through the optional research profile.

Inputs and outputs are research scenarios. The lab never edits the actual portfolio ledger, approves financial candidates, places trades, or requests an AI interpretation.

For a first controlled run, upload [hypothetical-returns.json](examples/hypothetical-returns.json) into the dataset field and select equal weights. It contains 80 intervals for three explicitly synthetic assets. For simulation, use weights `{"SYNTH_A":0.4,"SYNTH_B":0.3,"SYNTH_C":0.3}` and decision date `2025-01-02`. [hypothetical-report-returns.json](examples/hypothetical-report-returns.json) supplies a labeled report series. These files were validated through the actual bounded workers; they are Mock Data, not investment evidence.

## Dependency profiles

### Core and optional analysis/table profiles

The core Python 3.14 lock remains unchanged. The analysis and table-extraction profiles are independently hash locked while preserving every overlapping core version. OCR has a separate interpreter and separately resolved lock:

| Profile | Direct packages | Use |
|---|---|---|
| `backend/requirements-adapters.lock` | PyPortfolioOpt 1.6.0, SciPy 1.16.3, bt 1.4.1, QuantStats 0.0.86, pandas_market_calendars 5.6.1, EdgarTools 6.3.0 | Allocation, independent simulation check, report statistics, calendars and SEC parsing |
| `backend/requirements-extraction.lock` | Camelot 2.0.0 | CPU PDF table extraction |
| `backend/requirements-ocr.lock` | Docling 2.150.1, Pydantic 2.14.0, Pillow 13.0.0, filelock 4.2.12 and resolved dependencies | Separate optional OCR interpreter only; Marker is excluded because its published dependency requirements conflict with the patched versions |

The SciPy pin is intentional: PyPortfolioOpt 1.6.0 HRP uses a private hierarchy constant absent in SciPy 1.18.1. The selected version was executed in the adapter tests. FinanceDatabase's newest package requires pandas 3, whereas the app pins pandas 2.3.3. The reference adapter therefore consumes a pinned upstream CSV snapshot instead of upgrading the core dataframe stack.

For an existing isolated Python 3.14 development environment, install from the repository root:

```bash
python -m pip install --require-hashes -r backend/requirements.lock
python -m pip install --require-hashes -r backend/requirements-adapters.lock -r backend/requirements-extraction.lock
```

The backend Dockerfile adds Linux `libseccomp2` and accepts explicit build arguments:

```bash
docker build -f backend/Dockerfile \
  --build-arg INSTALL_RESEARCH_ADAPTERS=true \
  --build-arg INSTALL_TABLE_ADAPTERS=true \
  -t marketagent-adapters .
```

Normal Compose builds also accept `INSTALL_RESEARCH_ADAPTERS` and `INSTALL_TABLE_ADAPTERS` from private settings. Both arguments default to false. Use the existing installation's Compose project and the [operations procedure](../operations.md) for any eventual rollout. Building an image is separate from replacing running services.

### Separate OCR environment

Do not install the OCR lock into the API environment. Docling requires a newer openpyxl than the core lock; model runtimes add substantial dependencies. Create a separate environment and install its complete lock:

```bash
python3.14 -m venv /absolute/path/to/marketagent-ocr
/absolute/path/to/marketagent-ocr/bin/python -m pip install --require-hashes -r backend/requirements-ocr.lock
```

Set `SOURCE_ADAPTER_PYTHON` to that interpreter and `SOURCE_ADAPTER_MODEL_DIR` to a preprovisioned model directory. The exact model artifacts/checkpoints must match the chosen Docling version. Weights have their own upstream terms. This batch does not download weights or assert working OCR inference. The lock resolves on Python 3.14, but model provisioning and inference are a separate verification step.

The Marker wrapper remains explicitly unavailable with its current published dependency set. Marker 2.2.0 requires Surya 0.23, which constrains Pillow below 11 and filelock below 4. Exact-version advisory metadata identified known issues in those resolved versions. Adding patched Pillow 13.0.0/filelock 4.2.12 makes that combination unsatisfiable. The adapter checks dependency metadata and reports the conflict. Do not bypass the dependency resolver or claim a verified Marker installation from the presence of its wrapper.

The OCR lock includes platform model dependencies and can be large. It is not an instruction to add GPU drivers to the API process. Any CPU-specific dependency profile requires a separately resolved lock and verification; do not selectively remove hashed entries and call the original profile reproduced.

### Provider configuration

Configure server-side values through the existing settings mechanism. Blank credentials return explicit unavailability, never fabricated success.

| Variable | Purpose |
|---|---|
| `SEC_USER_AGENT` | Existing SEC identity with a contact address |
| `FMP_API_KEY` | FMP prices/reference/history/transcripts |
| `MASSIVE_API_KEY` | Massive data and entitled endpoints |
| `OPENFIGI_API_KEY` | Optional higher-rate OpenFIGI access; public access remains distinct |
| `EARNINGSCALL_API_KEY` | EarningsCall transcript access |
| `FRED_API_KEY` | Existing FRED/ALFRED observation access |
| `MARKET_DATA_PROVIDER` | Explicit selected provider for existing market ingestion |
| `SOURCE_ADAPTER_PYTHON` | Optional server-controlled OCR interpreter |
| `SOURCE_ADAPTER_MODEL_DIR` | Preprovisioned local OCR model assets |
| `RESEARCH_PEER_SNAPSHOT_PATH` | FinanceDatabase CSV with its adjacent `.manifest.json` |

In Compose, the default peer snapshot is `/workspace/data/reference/financedatabase.csv` on the existing read-only data mount. Place the CSV and its adjacent manifest under `data/reference/` on the host. Override the path for another snapshot or set it explicitly empty to disable discovery. The snapshot CLI makes both public files readable by the backend's separate user. An OCR interpreter and model files must also be provisioned inside the runtime or mounted explicitly.

Capability responses describe configuration and dependency readiness. Provider entitlement, source completeness, current network access and successful extraction are established by individual attempts.

## FinanceDatabase snapshot setup

This CLI downloads only fixed-host, fixed-commit exchange CSV files. It follows no redirects, bounds bytes/rows/time, retains original-file hashes, and writes the combined CSV plus manifest. The explicit example revision was inspected in this batch:

```bash
PYTHONPATH=backend python -m app.services.research_lab.snapshot_cli \
  --revision 93b872f0e4b4e05e8d35b7f0a39efe9245bcc2c1 \
  --exchange NSE --exchange BSE --exchange NMS --exchange NYQ \
  --output /absolute/path/to/reference/financedatabase.csv
```

Set `RESEARCH_PEER_SNAPSHOT_PATH` to that output. A live download of those four files produced 17,886 rows with combined SHA256 `09b148a4cc6ef3d65b67c9e1d6998668f9c59cfd221e3a1c553dfd2b662b98a6`. The observed upstream sector label is `Information Technology`. Filters use exact case-insensitive country/sector/industry values; query text matches ticker/name. Listing identity is retained across exchanges. Delisted entries are excluded from candidate output, which does not establish historical investability.

The snapshot is reference data, not verified valuation comparables. The result includes upstream revision, observation time and hashes. Every discovery request rechecks the manifest and runs in the same bounded calculation worker as other research operations.

## API inventory

All routes below use the existing authenticated backend boundary and `ApiResponse` envelopes, except attachment downloads. Browser code uses the existing same-origin `/api/backend` proxy. Opening capabilities/history does not initiate a provider fetch.

### Market, identity and calendar

| Method/path | Purpose |
|---|---|
| `POST /api/data-adapters/{provider}/quote` | Inspect a typed current quote |
| `POST /api/data-adapters/{provider}/history` | Inspect inclusive dated history with explicit adjustment selection |
| `POST /api/data-adapters/{provider}/dated-quote` | NSE quote derived from an actual history row/date |
| `POST /api/data-adapters/{provider}/corporate-actions` | Preserve corporate actions as separate evidence |
| `POST /api/data-adapters/{provider}/reference` | Massive reference metadata |
| `POST /api/data-adapters/identity/openfigi` | Mapping candidates, with ambiguity retained |
| `POST /api/data-adapters/calendars/schedule` | Calendar sessions and explicit overrides |

`provider` is `fmp`, `massive`, or `nse_mcp`. An unsupported provider/operation pair returns an explicit error. Each successful inspection returns a Processing Run, preserved original document IDs, typed result, observation time and warnings. Missing/partial histories remain missing/partial.

### Source evidence

| Method/path | Purpose |
|---|---|
| `GET /api/source-adapters` | Dependency/configuration status |
| `POST /api/companies/{company_id}/source-adapters/sec-facts` | Preserved SEC CompanyFacts into annual review candidates |
| `POST /api/companies/{company_id}/source-adapters/india-filings` | Supplied official metadata into versioned source evidence |
| `POST /api/companies/{company_id}/source-adapters/transcript` | Explicit transcript retrieval and version preservation |
| `POST /api/companies/{company_id}/source-adapters/documents/{document_id}/extract` | Selected stored-PDF pages through a chosen parser |
| `POST /api/source-adapters/fred-vintage` | ALFRED vintage snapshot |

Source responses report raw document IDs, candidate IDs, counts/status, warnings and Processing Run identity. Annual eligibility, unit/period safeguards and existing review requirements apply after extraction. An extracted value is not an approved fact.

### Research calculations and exports

| Method/path | Purpose |
|---|---|
| `GET /api/research-lab/capabilities` | Installed/configured adapters and limits |
| `POST /api/research-lab/allocation` | Hypothetical weights and risk/return diagnostics |
| `POST /api/research-lab/simulation` | Compounded research wealth path, rebalance record and cost assumptions |
| `POST /api/research-lab/report` | Supplied return/benchmark statistics |
| `POST /api/research-lab/peers` | Local reference candidates |
| `GET /api/research-lab/runs` | Caller-owned run history |
| `GET /api/research-lab/runs/{run_id}` | Exact saved result after hash verification |
| `GET /api/research-lab/runs/{run_id}/export` | JSON attachment with normalized inputs, manifest and output |
| `GET /api/research-lab/runs/{run_id}/report.html` | Escaped standalone report attachment |

Request definitions live in [research_lab.py](../../backend/app/schemas/research_lab.py), [source_adapters.py](../../backend/app/schemas/source_adapters.py), and [data_adapters.py](../../backend/app/schemas/data_adapters.py). These schemas are the authoritative field/enum/bounds reference.

## Research semantics

### Allocation

Minimum variance and maximum Sharpe use explicit bounds and optional group constraints. A baseline allocation can impose gross L1 turnover for minimum variance; equal weights are checked against the same constraints. HRP rejects unsupported group/bounds/turnover inputs. Maximum Sharpe rejects missing annual expected returns and unsupported turnover constraints. Results preserve solver precision and are revalidated for full investment and all constraints.

Historical covariance is an estimate, not a recommendation. No expected-return vector is synthesized from current DCF gaps. Small samples, price-only returns and unverified availability remain visible.

### Simulation

Returns compound multiplicatively. Rebalance decisions occur at interval starts before the interval return, using a caller-declared weight decision date no later than the first interval. Monthly/quarterly/yearly/each-period schedules operate on the supplied interval boundaries. They do not infer a verified exchange calendar.

Native costs equal pretrade NAV times gross absolute weight changes times the supplied cost rate, including initial entry. This is an explicitly labeled proportional estimate. Native and `bt` zero-cost paths are independently reconciled. A rebalance cannot buy an asset after its complete loss. Bankruptcy, delisting, changing-universe reconstruction, real transactions, tax lots and broker execution are not supplied by this simulation.

Drawdown includes initial capital, so a loss in the first interval is retained. Undefined ratios are null. The report rejects differing benchmark dates instead of silently aligning/filling them.

### Reproducibility and knowledge times

Saved research receipts retain normalized requests, input/output SHA256, adapter versions, relevant dependency versions, creation time, window end, and source qualifications. Pure user-supplied returns are explicitly `user_supplied_unverified`; public-information and application-observation cutoffs remain null rather than inventing historical availability. A present-day source snapshot does not become a point-in-time dataset by changing the requested date.

Both input and output hashes are checked on retrieval/export. Owner filters apply to history and downloads. Source adapters separately retain original evidence, call/publication/observation distinctions, source-specific versions and Processing Runs.

## Execution limits

| Worker | Limits |
|---|---|
| Research | 2 concurrent jobs per API process; 40 seconds wall time; 25 CPU seconds; 3 GiB address space; 4 MiB request; 8 MiB output |
| Extraction | 1 concurrent job per API process; 60 seconds wall time; 45 CPU seconds; 4 GiB address space; 40 MiB input; 12 MiB output; at most 20 selected PDF pages |

Workers receive a reduced environment without application credentials, run in temporary directories and deny network syscalls through Linux seccomp. These are bounded trusted-library workers, not a general filesystem sandbox. Missing Linux isolation fails closed. The original normal PDF path retains its existing separate bounds.

Failed dependency, configuration, provider, parsing or calculation attempts are recorded as failures. They never become Mock Data success. The frontend shows error messages and successful receipt IDs. Failed action messages currently omit their Processing Run ID; server-side run records remain available for diagnosis.

## Generated API types

The read-only exporter derives the three new route families and their reachable schemas from the registered FastAPI application:

```bash
PYTHONPATH=backend python backend/scripts/export_adapter_contracts.py \
  --output frontend/lib/api/generated/adapters.openapi.json
```

Use the existing valid development settings when importing the app; exporting schemas does not query the database or providers. `--check` compares the snapshot without writing. The frontend generation/check scripts consume this snapshot and preserve runtime response validators.

## Verification and remaining limits

Detailed evidence is retained per workstream:

1. [Source adapters](../workstreams/evidence/adapters-20261117/W2/implementation.md).
2. [Market, identity and calendar adapters](../workstreams/evidence/adapters-20261117/W3/README.md).
3. [November 17 adapter verification](verification.md).

The packaged tests exercised PyPortfolioOpt, bt, QuantStats, exchange calendars, EdgarTools and Camelot on controlled inputs. The November 18 installed checks then verified six specific cases:

| Adapter | What was observed |
|---|---|
| FinanceDatabase | A pinned snapshot yielded separate reference listings for Infosys. The result is a candidate peer set. |
| SEC annual facts | An original annual filing and amendment retained accession and cutoff, and repeating intake deduplicated the same facts. |
| NSE MCP | The installed workflow retained an Infosys dividend observation with its source locator and hash. |
| ALFRED | Stored GDP observations on opposite sides of a revision matched their respective as-of responses. |
| OpenFIGI | An Infosys mapping request returned distinct listing candidates and retained the ambiguity. |
| Camelot | Six selected cells came from the original Apple report. Currency and statement completeness remain separate review questions. |

The remaining provider proofs require US corporate-action entitlement, a transcript entitlement plus a real correction, or a compatible OCR worker, approved local models and a genuine scan. [Original-source receipt](../../data/reviews/ui-adapter-release-20261118.json) · [Exact prerequisites](../limitations.md#installed-adapters-and-remaining-source-prerequisites)

The Next.js dependency was patched from 16.4.1 to 16.4.5 for the two upstream root-parameter cache advisories. This is a source dependency repair, not a claim of an observed leak in this app.

## Remaining roadmap work

This batch implements the concrete adapters above and the consuming lab. It does not claim every acceptance item in the research roadmap is complete:

| Roadmap area | Remaining work |
|---|---|
| Unified company workspace | Full resizable model/source panes, PDF navigation integration and persistent named lists |
| Transcript intelligence | Recurring overlap polling, reviewed guidance extraction and comparisons between calls |
| Hybrid retrieval | Labeled retrieval evaluation, embedding model/version management and pgvector integration |
| Durable workflow pilot | DBOS integration with interruption/cancellation/idempotency verification on PostgreSQL |
| Presets and replay | Named persistent presets and one-click replay; exact request exports already preserve normalized inputs |
| Agent evaluation | New provider fixtures are present; a Promptfoo model/prompt evaluation pipeline is not added because these adapters make no LLM calls |
| Security identity | Candidate mapping and ambiguity are implemented; accepted bitemporal issuer/security/listing migrations remain separate |
| Portfolio inputs | Direct conversion of owned portfolio histories into lab datasets, total-return reconstruction and changing-universe simulations |
| Optional deployment | Analysis and Camelot are installed. Additional paid sources need the named entitlements. OCR needs a separately compatible environment, approved model files and a genuine scanned page. |

OpenBB, Riskfolio, skfolio, vectorbt and backtesting.py are alternatives for later specific needs, not additional copies of the selected provider/optimization/simulation stack. Ghostfolio, Wealthfolio and OpenStock informed workflow choices; their whole applications were not embedded. Dependencies and references are listed in [third-party notices](../../THIRD_PARTY_NOTICES.md).

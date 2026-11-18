# Adapter integration verification

Batch: November 17, 2026. Branch: `feat/research-adapters-20261117`.
Baseline: `371b58c02cfd2b80429f28dbc13629165b5e392d`.

This is source-level implementation evidence. It does not certify an existing installation, a public deployment, paid-provider entitlements or real OCR inference. The [implementation guide](README.md) describes setup and boundaries; [limitations](../limitations.md) remains the current limitations ledger.

## Results

| Check | Observed result | Scope |
|---|---|---|
| Full integrated backend suite | **2,231 passed, 15 skipped**, 263 warnings, 150.45 seconds | CPython 3.14.10, core test lock plus installed analysis/table profiles; isolated test fixtures |
| Frontend utility suite | **409 passed, 0 failed** | Actual final frontend source tree |
| Frontend TypeScript | Passed | Existing typecheck command |
| Generated TypeScript staleness | Passed | Regeneration from the committed adapter OpenAPI snapshot |
| Host frontend production build | Passed | Node 24.22.1; Next 16.4.5 |
| Frontend dependency audit | **0 vulnerabilities** | Actual `npm audit --json` result |
| Repository check unit tests | **107 passed** | Complete repository static-gate unit-test set |
| Python dependency audit | **No known vulnerabilities found in all four profiles** | Actual pip-audit 2.10.1 on baseline test, analysis, table and separate OCR locks; 60-second socket timeout |
| Optional Python advisory metadata | **193 distinct exact versions checked; 0 query errors; 0 returned known-advisory findings** | Official PyPI JSON metadata for the selected analysis, table and Docling profiles |
| Live FinanceDatabase reference snapshot | Downloaded, hash verified and parsed | Four exchange files at one fixed upstream commit; 17,886 combined rows |
| Local custom browser harness | **Blocked before page creation** | Chromium could not create a socket in this environment; separate from hosted browser checks |
| Local Docker, PostgreSQL migration and container release gates | **Not run here** | Docker unavailable locally; hosted checks are recorded separately |
| Normal installed application | **Not accessed or changed** | No user's running database, holdings or service installation was modified |

The backend run above included the final source-adapter request-context, identity, date-precision and Marker dependency guards. After that full run, allocation/simulation results were given their existing input `source_label` for visible Mock Data provenance; the research suite was rerun separately. See the [coordinator receipt](../workstreams/evidence/adapters-20261117/W5/README.md) for that final focused result and repository checks.

The final frontend tree is `f4a8e90b2df3eb21d8cd63bf30edb5831fc3883e`; the integrated and isolated UI worktrees match. The 409-test suite and TypeScript check passed on that tree. The host production build used tree `1a62c0ec90704ecb3b1dc93fbe2ba3fb1fc7ee10`; the only subsequent frontend change narrows an E2E selector, with runtime UI code unchanged. A host production build is not a browser test.

### Hosted follow-up

The first complete hosted run on head `788855f` passed repository checks, the container-security job and the PostgreSQL recovery drill. It exposed three verification issues: a default PyPI timeout, optional calendar tests executing without their optional dependency, and NSE fixtures outside the baseline test image. The browser job ran 71 workflows: 70 passed and one stopped on an ambiguous Search-button selector. These findings produced the bounded timeout, test-packaging and exact-selector corrections below; no gates or assertions were removed. The [PR checks](https://github.com/Gittastic112/Marketagent/pull/20/checks) provide subsequent hosted status.

W3's repaired tests passed **44/44** with the optional profile. A separately installed hash-locked core/test-only environment, using a staged backend tree without any documentation directory, produced **40 passed and exactly 4 calendar skips**. Every NSE test passed there. Calendar skips apply only when the distribution is absent; an installed but broken package still fails. The [browser follow-up](../workstreams/evidence/adapters-20261117/W1/hosted-browser-20261118.md) records the precise selector correction and the existing desktop/mobile memo workflows that passed.

## Reproducing the backend test environment

From the repository root, install the hash-locked test dependencies and the optional analysis/table profiles into an isolated Python 3.14 environment. Then, from `backend/`, run:

```bash
env DATABASE_URL=postgresql+psycopg://test:test@localhost/marketagent_test \
  SEC_USER_AGENT='Marketagent Tests adapter-tests@marketagent.test' \
  APP_ENV=test PYTHONPATH="$(pwd)" \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python -m pytest -q -p no:cacheprovider
```

The PostgreSQL URL initializes the app's configured engine; test fixtures use isolated SQLite sessions rather than connecting to a normal application database. Explicit `PYTHONPATH` is needed by existing subprocess tests. The suite does not establish PostgreSQL migration correctness. Fifteen skipped tests remain skipped, not passed.

The full run's 263 warnings included upstream NumPy/ffn and openpyxl deprecations. They were not suppressed or represented as failures. Existing tests and integrity gates were retained.

## Actual library execution

| Integration | What ran | What the evidence establishes |
|---|---|---|
| PyPortfolioOpt 1.6.0 | Minimum variance, maximum Sharpe and HRP on controlled return matrices | Finite, fully invested weights; group/turnover/bounds validation; real solver invocation |
| Native simulation and bt 1.4.1 | Buy-and-hold and constant-weight schedules against the same explicit input returns | Multiplicative compounding and independently reconciled zero-cost wealth paths; estimated costs remain native-only |
| QuantStats 0.0.86 | Supplied return-series reports | Finite/null metric handling, initial-loss drawdown and protection against implicit price/return inference |
| FinanceDatabase CSV reference | Real four-file fixed-commit download and bounded peer lookup | Actual parsing, manifest/hash verification and country/sector filtering, not verified valuation comparability |
| pandas_market_calendars 5.6.1 | Exchange sessions including daylight-saving, early-close and explicit weekend override cases | Declared calendar behavior and coverage checks, not proof of every historical special session |
| EdgarTools 6.3.0 | Preserved synthetic SEC CompanyFacts parsed by the real package in a bounded worker | API compatibility, annual candidate mapping and retained source context; not a complete company audit |
| Camelot 2.0.0 | Real extraction of a labeled synthetic PDF table in a bounded worker | Selected-page execution, neutral structured output and integration with existing review candidates |
| Docling | Wrapper, separate lock, metadata/preflight and worker boundaries | **No model inference executed**; model assets were not provisioned |
| Marker | Wrapper and metadata dependency guard | Current incompatible published dependency chain fails explicitly before model execution |

Controlled examples are labeled Mock Data and are not market evidence. The supplied [return matrix](examples/hypothetical-returns.json) and [report series](examples/hypothetical-report-returns.json) were also validated through the actual bounded allocation, simulation and report workers.

### FinanceDatabase observation

The inspected revision is `93b872f0e4b4e05e8d35b7f0a39efe9245bcc2c1`, with NSE, BSE, NMS and NYQ files. Combined SHA256:

```text
09b148a4cc6ef3d65b67c9e1d6998668f9c59cfd221e3a1c553dfd2b662b98a6
```

The combined file contains 17,886 rows. A bounded local request for India / Information Technology returned 518 matching reference candidates with a five-row display limit. The source snapshot is not committed as application data and does not establish a historical investable universe.

### Provider observations and limits

Official NSE protocol initialization, tool discovery and representative public samples succeeded through the permitted research connection. The production app uses its separate proxy-free transport; that transport did not complete a live call in this environment. These are different verification claims. Captured tool schemas and samples informed the implementation and its fixtures.

In particular, NSE's date lookup sample contains a bare price rather than a date-bearing observation. The dated-quote adapter therefore derives an actual dated row from history. Settlement-series ambiguity is rejected rather than silently mixing EQ and T0 rows.

No paid FMP, Massive or EarningsCall account was exercised. Live OpenFIGI mapping, authenticated ALFRED retrieval and complete production provider round trips remain runtime checks. India filing intake consumes supplied metadata; no BSE account endpoint or scraper was introduced.

## Regression and boundary checks

Independent review identified and fixed the following concrete defects before handoff:

1. A fully lost asset could be repurchased by a later rebalance. The simulator now rejects that unsupported resurrection; buy-and-hold retains the zero asset value.
2. Peer discovery initially bypassed the bounded worker. It now uses the same limited, network-denied calculation process; the configured filesystem path is server context rather than user input or a persisted request field.
3. Date-only India filing metadata acquired invented timestamp precision. Original dates are preserved with uncertainty instead.
4. FMP transcript matching could attach a ticker from an unsupported market. The route now requires a supported, resolved US listing before fetching.
5. A repeated partial source intake could produce a failed Processing Run even when the evidence already existed. It now retains partial completion and actual fetched/created/duplicate counts.
6. Effective SEC cutoff, PDF page selection and other request choices were not always durable after deduplication. Sanitized immutable request context is recorded before execution.
7. The frontend discarded market freshness metadata carried only in the API envelope. It now preserves those warnings and stale-state notices.
8. FMP transcript controls offered unsupported detail levels. They now expose only level 1.
9. New attachment routes were missing from the response-contract registry. Both download routes are explicitly declared and covered by the contract checks.
10. A nested market test fixture module shadowed baseline fixtures during full-suite collection. A package boundary fixes collection without weakening the tests.

Other coverage includes cross-user run isolation, input/output hash tampering, rejected nonfinite or mismatched series, annual-return requirements, constraint infeasibility, exact-file import identity, escaped report/memo content, failed dependency behavior and Linux network-denial enforcement.

## Dependency decisions

The core runtime and baseline test locks remain unchanged. The analysis and Camelot profiles preserve overlapping core versions. OCR is separately resolved because Docling requires newer spreadsheet/model dependencies than the core application.

Real HRP execution failed with SciPy 1.18.1 because the selected PyPortfolioOpt version relies on a removed private hierarchy constant. SciPy 1.16.3 is intentionally pinned and was executed successfully. This is recorded rather than assuming a successful install proves runtime compatibility.

Marker 2.2.0 requires the Surya 0.23 series, which constrains Pillow below 11 and filelock below 4. Exact-version advisory metadata showed known issues in the corresponding resolved versions. A combined profile with patched Pillow 13.0.0 and filelock 4.2.12 could not resolve. The shipped OCR lock therefore contains Docling and patched dependencies; Marker remains blocked. The dependency resolver was not bypassed.

Initial `pip-audit` attempts timed out on package-service requests at its default 15-second timeout, both locally and in the first full hosted run. Retrying with the supported 60-second socket timeout completed successfully for the baseline test lock and all three optional profiles, with no known vulnerabilities found. CI uses that timeout while retaining its failure behavior. Results are retained in the [coordinator receipt](../workstreams/evidence/adapters-20261117/W5/README.md#runtime-and-dependency-evidence).

A separate exact-version query of official PyPI JSON vulnerability metadata also completed for all 193 distinct selected optional-profile versions, with no query errors or returned findings. The [compact result](../workstreams/evidence/adapters-20261117/W5/python-advisory-metadata.json) records the method and profile counts. No local container OS vulnerability scan was performed; hosted status is evaluated separately.

Next was upgraded from 16.4.1 to 16.4.5 after the host build reported its upstream root-parameter cache advisories. The final build and npm audit passed. The [frontend receipt](../workstreams/evidence/adapters-20261117/W1/README.md#security-patch) links the maintainer advisories. This does not assert that an exploit occurred in this application.

## Remaining verification

| Gate | Required evidence |
|---|---|
| Docker release baseline | Build the normal and optional-profile images; execute existing isolated backend, frontend and PostgreSQL migration gates |
| Browser workflows | Run the retained Mock Data harness and application workflows in a permitted Chromium environment, including keyboard use, responsive layout and accessibility |
| Actual installed app | Configure selected dependencies/providers, open Research Lab, inspect real capabilities and complete explicit end-to-end operations |
| Paid and public provider connectivity | Verify configured credentials, entitlements, limits and real company/listing responses through the app transport |
| OCR | Provision compatible local Docling assets and run representative documents within the stated resource limits; Marker remains unavailable until the upstream dependency conflict is resolved |
| Hosted CI | Inspect the draft PR's checks; local results do not imply hosted checks passed |

No deployment, main-branch merge, portfolio change, evidence approval, trade or external AI request is part of this batch. The remaining product roadmap is listed in the [implementation guide](README.md#remaining-roadmap-work).

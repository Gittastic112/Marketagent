# Coordinator integration receipt

Batch: November 17, 2026. Baseline: `371b58c02cfd2b80429f28dbc13629165b5e392d`.
Integration branch: `feat/research-adapters-20261117`.

The authorized cross-cutting scope covers three new adapter API families, their consumers, bounded research execution, optional dependencies and current documentation. Separate worktrees reserved UI, source ingestion and market adapters; shared integration and the Research Lab backend were coordinated at root. The batch [ownership manifest](../../../adapters-20261117.tsv) contains 69 disjoint reservations.

## Observed checks

| Check | Result |
|---|---|
| Full integrated backend suite | 2,231 passed, 15 skipped, 263 warnings in 150.45 seconds |
| Final research suite after adding visible source labels | 33 passed, 28 warnings in 3.41 seconds |
| Repository checker unit tests | 107 passed in the complete static-gate unit-test set |
| Secret scan | Passed |
| Documentation consistency | Passed across active Markdown files and local links |
| Dependency-lock consistency | Passed: core 66, baseline test 70, optional analysis 89, table extraction 16, separate OCR 122 |
| Ownership manifest | Passed: 5 owners, 69 disjoint reservations |
| Backend-derived OpenAPI snapshot | Matches registered application; 22 paths and 63 schemas |
| Whitespace/error diff check | Passed |
| Frontend tests/typecheck/generated types/build | Passed; final test-selector follow-up leaves runtime UI code unchanged |

The final frontend tree is `f4a8e90b2df3eb21d8cd63bf30edb5831fc3883e`; 409 utility tests and TypeScript passed after the exact Search-button E2E selector correction. Its runtime UI code is unchanged from the production-built tree `1a62c0ec90704ecb3b1dc93fbe2ba3fb1fc7ee10`. Detailed evidence is retained in [W1](../W1/README.md) and its [hosted follow-up](../W1/hosted-browser-20261118.md). Source and market evidence are in [W2](../W2/implementation.md) and [W3](../W3/README.md).

The final source-label edit only echoes the already-preserved allocation/simulation input label into the result consumed by the existing UI. Assertions were added to existing calculation tests. It changes neither the public schema nor the frontend tree.

## Runtime and dependency evidence

Actual PyPortfolioOpt, bt, QuantStats, calendar, EdgarTools and Camelot execution passed on controlled fixtures. The supplied Mock Data files were also executed through the real bounded worker entry point. The FinanceDatabase fixed-commit snapshot and bounded discovery call used real upstream reference data.

Actual pip-audit 2.10.1 completed successfully with a 60-second socket timeout for the [baseline test lock](pip-audit-core.txt), [analysis](pip-audit-adapters.txt), [table extraction](pip-audit-extraction.txt) and [separate OCR profile](pip-audit-ocr.txt). All four returned no known vulnerabilities. Initial requests had timed out at the default 15 seconds, locally and in hosted CI. The workflow changes only that timeout; failed audits still fail the gate.

The complete selected optional dependency set was also queried against exact-version PyPI JSON metadata. The [compact advisory result](python-advisory-metadata.json) records 193 distinct versions, zero query errors and zero returned known-advisory findings. Neither check is a container OS scan.

Marker's current dependency conflict is surfaced explicitly. The OCR lock contains separately resolved Docling dependencies, not an unsafe forced Marker installation. Model provisioning and OCR inference remain unverified.

## Integration changes and preserved boundaries

All three routers are registered behind existing authentication. The two raw research downloads are declared in the response-contract allowlist. Existing provider status/configuration paths recognize FMP, Massive and official NSE selection. Optional dependencies remain opt-in; the core and baseline test locks are unchanged.

The new CI steps audit all three optional lockfiles, build an optional analysis/table test image, run its adapter suites without network, verify backend OpenAPI freshness and check generated TypeScript. They extend the existing gates. Hosted execution and Docker results are not claimed locally.

Independent reviews fixed provenance, listing, timestamp, partial-run, stale-response and simulation issues described in [integrated verification](../../../../adapters/verification.md). The user-facing guide, route/API inventories, current state, handoff and limitations were reconciled against the integrated source.

No normal application database, evidence approval, holdings, live installation, deployment or main branch was modified. Local custom-harness browser execution was blocked before page creation. These limits remain explicit in the [verification report](../../../../adapters/verification.md#remaining-verification).

The first complete hosted run passed repository checks, container security and PostgreSQL recovery. Its other findings were corrected: full-patch EOF formatting; the pip-audit socket timeout; optional calendar tests in the core-only image; NSE fixtures missing from that image; and the ambiguous browser Search selector. W3's fix passed 44 tests with optional dependencies and 40 tests plus exactly 4 expected calendar skips in a separately installed core-only environment without docs. The [PR checks](https://github.com/Gittastic112/Marketagent/pull/20/checks) show subsequent hosted execution; local custom-harness results remain separate.

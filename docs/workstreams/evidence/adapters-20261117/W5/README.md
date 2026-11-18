# Coordinator integration receipt

Batch: November 17, 2026. Baseline: `371b58c02cfd2b80429f28dbc13629165b5e392d`.
Integration branch: `feat/research-adapters-20261117`.

The authorized cross-cutting scope covers three new adapter API families, their consumers, bounded research execution, optional dependencies and current documentation. Separate worktrees reserved UI, source ingestion and market adapters; shared integration and the Research Lab backend were coordinated at root. The batch [ownership manifest](../../../adapters-20261117.tsv) contains 69 disjoint reservations.

## Observed checks

| Check | Result |
|---|---|
| Full integrated backend suite | 2,231 passed, 15 skipped, 263 warnings in 150.45 seconds |
| Final research suite after adding visible source labels | 33 passed, 28 warnings in 3.41 seconds |
| Repository checker unit tests | 38 passed |
| Secret scan | Passed |
| Documentation consistency | Passed: 100 active Markdown files and 1,309 local links |
| Dependency-lock consistency | Passed: core 66, baseline test 70, optional analysis 89, table extraction 16, separate OCR 122 |
| Ownership manifest | Passed: 5 owners, 69 disjoint reservations |
| Backend-derived OpenAPI snapshot | Matches registered application; 22 paths and 63 schemas |
| Whitespace/error diff check | Passed |
| Frontend tests/typecheck/generated types/build | Passed in the isolated UI worktree; integrated tree is byte-identical |

The exact frontend tree is `1a62c0ec90704ecb3b1dc93fbe2ba3fb1fc7ee10`. Its detailed results, including 409 passing tests, the production build and npm audit, are retained in [W1](../W1/README.md). Source and market evidence are in [W2](../W2/implementation.md) and [W3](../W3/README.md).

The final source-label edit only echoes the already-preserved allocation/simulation input label into the result consumed by the existing UI. Assertions were added to existing calculation tests. It changes neither the public schema nor the frontend tree.

## Runtime and dependency evidence

Actual PyPortfolioOpt, bt, QuantStats, calendar, EdgarTools and Camelot execution passed on controlled fixtures. The supplied Mock Data files were also executed through the real bounded worker entry point. The FinanceDatabase fixed-commit snapshot and bounded discovery call used real upstream reference data.

The complete selected optional dependency set was queried against exact-version PyPI JSON metadata. The [compact advisory result](python-advisory-metadata.json) records 193 distinct versions, zero query errors and zero returned known-advisory findings. Standard pip-audit requests timed out here; CI retains pip-audit checks. This is not a container OS scan.

Marker's current dependency conflict is surfaced explicitly. The OCR lock contains separately resolved Docling dependencies, not an unsafe forced Marker installation. Model provisioning and OCR inference remain unverified.

## Integration changes and preserved boundaries

All three routers are registered behind existing authentication. The two raw research downloads are declared in the response-contract allowlist. Existing provider status/configuration paths recognize FMP, Massive and official NSE selection. Optional dependencies remain opt-in; the core and baseline test locks are unchanged.

The new CI steps audit all three optional lockfiles, build an optional analysis/table test image, run its adapter suites without network, verify backend OpenAPI freshness and check generated TypeScript. They extend the existing gates. Hosted execution and Docker results are not claimed locally.

Independent reviews fixed provenance, listing, timestamp, partial-run, stale-response and simulation issues described in [integrated verification](../../../../adapters/verification.md). The user-facing guide, route/API inventories, current state, handoff and limitations were reconciled against the integrated source.

No normal application database, evidence approval, holdings, live installation, deployment or main branch was modified. Browser execution was blocked before page creation. These limits remain explicit in the [verification report](../../../../adapters/verification.md#remaining-verification).

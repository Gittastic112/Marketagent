# Architecture and documentation audit

Date: September 22, 2026. Scope: current application documentation, contract
boundaries and restore-writer coordination. This is not a claim that all product
limitations or legacy architectural debt have been eliminated.

## Findings and repairs

| Finding | Repair and owning files |
|---|---|
| Shared response types lived inside the large legacy HTTP schema module, loading domain services even for error handling | Extracted `backend/app/schemas/common.py`; preserved exact facade exports and generic class identity. Twenty envelope-only routers plus error/AI-error helpers import the pure module directly |
| Restore stopped the web app but left scheduled database writers active | `scripts/restore_local.sh` snapshots running/restarting worker state, stops both known workers before replacement, and resumes only previously active workers after verification and migration. Explicit custom names are supported |
| README incorrectly claimed all-interface Docker exposure | Reconciled README/setup/architecture with checked-in localhost bindings and the distinction between source settings and existing containers |
| Route inventory omitted the private-source detail page | Added the page and corrected the count to 48; the documentation checker now verifies every page source and the count |
| Link checker split angle-wrapped paths containing spaces and treated tilde-fenced examples as real links | Fixed destination parsing and both fence styles; regression fixtures reproduce the previous failures |
| Schema-head prose could drift independently of runtime readiness | Documentation checker compares the declared current head with the source readiness constant without executing application code; Alembic tests remain responsible for the actual migration chain |
| Ingestion/setup docs omitted the separate private inbox and scheduled source worker; price docs incorrectly said on-demand only | Documented the actual intake/privacy/review boundaries and separate deterministic brief versus SEC/FRED/price workers |
| Methodology docs implied India-specific rates where the source labels Global weighted averages, and omitted US intake | Reconciled labels with the service and source registry, preserving country-specific priors, dated FRED USD proxy and required review |
| Roadmap marked the whole daily evidence loop completed | Retained delivered foundations but marked multi-source workflow, search/archive and scheduled-inbox integration open |
| Current docs mixed old milestone counts with present claims | Current State owns current validation; checkpoint bodies remain dated historical evidence; the handoff and navigation map remain bounded |

The changes span multiple files because the common contract has many consumers
and operational facts have distinct canonical documentation owners. Existing
uncommitted and untracked work was preserved. No source corpus, valuation
formula, provider configuration, public route, migration or saved record was
changed by the refactor. No new dependency was added.

## Compatibility and source verification

The complete canonical OpenAPI `paths` and `components` objects have the same
SHA-256 before and after extraction:

`7165df366ea28c40f91e79c47f5a67a2403f64aaa69b7053a5037a8390edca03`

Both inventories contain 274 paths and 486 component schemas. Boundary tests
also check legacy class identity, `ApiResponse[int]` identity, independent pure
imports, and error handlers that do not load application services/models.
The broader contract, authentication and response-inventory regressions pass.

Validation:

- Full source-mounted, network-disabled backend suite: 1,181 passed, with five
  upstream Starlette/anyio and openpyxl deprecation warnings.
- Focused contract/response/auth inventory suite: 15 passed.
- Frontend: 223 tests and TypeScript passed; no frontend runtime code changed.
- Static documentation/security/local-port/backup tests: 23 passed.
- Shell syntax, secret scan and 11 project-workflow checks passed.
- Knowledge-base integrity: 64 canonical files/catalog rows, 44 ledger rows,
  no pending inbox files; four audit-tool tests passed. Raw corpus untouched.
- Backend and both worker production images built successfully with existing
  dependencies. Frontend was not rebuilt because only its README changed.

New regression tests were first observed failing for the intended missing
boundaries, then passed after implementation. Restore tests use a fake Docker
executable and temporary files only. They verify stop-before-replacement ordering,
previously disabled workers, custom names, and failure paths that leave writers
stopped. No destructive normal-database restore was performed.

## Runtime verification

Code-only backend/worker rollout passed readiness at unchanged head q8q8q8q8q8q8
with no missing tables, columns or constraints. The deployed image resolves old
and new envelope imports to the same class. Saved-record content fingerprints
are identical across rollout: two models, four assumption sets, two holdings,
three transactions and the Apple research source. PostgreSQL and frontend were
not replaced, and published ports remain localhost-only.

No new browser or live-provider certification is claimed for this refactor. The
prior inbox/AAPL checkpoint retains its separate real-source, browser and
independently restored backup evidence. No test runtime remains from this task;
deterministic test containers use the runner's automatic removal.

## Audit boundary and next work

Current source/configuration references, documentation links, route inventory,
agent rules, roadmap and corpus integrity were inspected. Archived bodies and
immutable financial doctrine/source artifacts were preserved, not rewritten to
today's vocabulary. External provider terms and every domain's financial or
browser behavior were not re-certified in this documentation task.

The [single limitations ledger](../../../agent_capabilities_and_limitations.md)
retains remaining legacy contracts, large workflow owners, manual frontend type
synchronization, source-string-heavy UI tests, provider placement and recovery
limits. Other database writers/admin sessions still need manual quiescence;
live backup/count comparisons require a quiet maintenance window. Continue by
extracting one domain with behavioral proof, not by broadly renaming files.

# Saved-input and Reverse DCF integrity

Date: 2026-09-10. Scope: the next 15 steps selected from the current handoff.
No normal-runtime deployment, migration, source import or finance-default rewrite.

## Work plan and implementation

1. Audit saved form fields against contracts, persistence, callers and tests.
   Found omitted lifecycle inputs, duplicate net-income controls, missing common
   book equity, and projection count derived from output rows rather than inputs.
2. Add regressions for omitted fields, explicit nulls, zero values and immutable
   earlier versions. The omission tests failed against the preceding source.
3. Add a separate version-write command with an optional base ID and timestamp.
   Keep command fields out of calculation inputs and draft promotion.
4. Preserve omitted inputs from the owned server-side basis. Explicit clears and
   edited values still replace the corresponding saved fields.
5. Serialize model writers, reject obsolete/wrong-model bases with HTTP 409,
   validate merged inputs, and retain atomic rollback and change-log behavior.
6. Update both form callers and the payload adapter. Preserve omission versus
   clear, reject nonfinite numeric text, and send the displayed saved basis.
7. Make book equity available to every model, remove duplicate net income, use
   saved projection count, and stop substituting initial defaults during resaves.
   Comparison price remains optional for an ordinary DCF save.
8. Constrain Reverse DCF parameters, positive finite price/shares and valid IDs.
9. Enforce owned, non-stale, valid-unit/currency, explicit-core-input and saved
   diagnostic gates. Remove the one-share fallback.
10. Use the owned FCFF/distressed model type. Explicitly reject unsupported
    financial-services reverse analysis instead of silently running FCFF.
11. Apply flat growth across the entire projection horizon and report the actual
    saved reference value, preserving explicit zero and omitted-year semantics.
12. Require a bracket and actual convergence. A boundary/iteration failure must
    not become an apparently solved implied assumption.
13. Return actual calculated price, residual, saved identity/time, currency,
    model type, shares and calculation time. Include resulting diagnostics.
14. Extract an on-demand Reverse DCF panel with explicit price, saved currency,
    result identity checks, input-change invalidation and unmount cleanup.
15. Run full tests, production builds and isolated PostgreSQL/browser checks;
    update the handoff and single limitation ledger with verified scope.

## Validation record

Step 15 completed on 2026-09-14 through five verification tasks. Exact current
suite counts live in [Current State](../../../00-current-state.md).

1. Full source-mounted backend suite passed in the network-disabled test
   container, with only four upstream openpyxl deprecation warnings.
2. Backend, frontend and scheduler production images built successfully, using
   valid cache hits for unchanged inputs. Local frontend tests/TypeScript passed.
3. Signed-in production browser resaves preserved book equity 500, net income
   100, company age/target ROE/failure probability zero, distress proceeds 42,
   currency/reinvestment notes and the five-year horizon. Missing comparison
   price stayed null. A second UI save cleared book equity to null and changed
   net income to zero while retaining the previous values in earlier versions.
4. Reverse DCF opened with blank price/shares overrides. Explicit price 222.58
   USD solved to margin 0.219994, calculated price 222.572029 and residual
   -0.007971 USD, inside the 0.01 tolerance. Analysis created no saved version.
   Editing price cleared the result; a deliberately delayed real response could
   not restore it after another edit. An unreachable price of 1,000,000,000
   displayed no implied solution and retained the bracket diagnostic.
5. Five pairs of simultaneous authenticated PostgreSQL saves each returned one
   HTTP 201 and one HTTP 409/VALUATION_VERSION_CONFLICT. Version count grew from
   three to eight, not thirteen, and prior response records were unchanged.
   Submitting the actual outdated browser form displayed the reload/conflict
   message and did not create a ninth version. Browser console errors: none.

All browser fixtures were explicitly named Mock Data. The test stack migrated
to o6o6o6o6o6o6 and passed readiness. The digest of sorted Python source hashes
under backend/app matched between the running test container and the workspace:
`7ab8401192a4a18d79645400f6cfe2f924cd13782f73ef4e7e2b81d030a81af6`.
Browser snapshots and a visually inspected form viewport screenshot remain in
`output/playwright/.playwright-cli/` (September 14, 19:59 through 20:04 UTC).

September 13 verification was interrupted by Docker availability and an
approval-service usage error. Lost command sessions were rerun, not inferred
successful. No normal database was used as a fallback.

The first backend command was blocked because normal Compose settings carried
the shared database URL. No test ran through that blocked invocation. Verified
in-memory fixture overrides, then used a separate network-disabled container,
disposable SQLite default and read-only source/data mounts. Added a maintained
docker-compose.test.yml so this boundary is explicit and reproducible.

The first broader run caught a route-level monkeypatch that needed to follow the
new service owner and version-command fields leaking into draft promotion.
The version contract was separated from the existing calculation-write contract;
the affected promotion and rollback tests then passed without weakening them.
An old reverse-math test explicitly waived convergence; it now uses a reachable
target and asserts the actual price residual. The initial Docker Node metadata
lookup timed out; the retry succeeded without changing dependency manifests.

## Disposable environment

The disposable browser project was
`valuation-integrity-browser-20260910`, configured in
`/tmp/valuation-integrity-20260910.F3OKNK/browser-compose.yml`.
Its database used disposable tmpfs, and the frontend binding was loopback port
13110. It was resumed for September 14 verification, without any normal-runtime
deployment. The frontend, backend and tmpfs database containers plus their
project network were removed after verification. Only disposable Mock Data was
discarded; normal containers and data were untouched. Browser session
`valuationverify` was closed; local evidence artifacts were retained.
The temporary unit-test project was `valuation-integrity-tests-20260910`, with
configuration in the same temporary directory's `compose.yml`; its runs used
`--rm`. Later tests used the maintained `market-intelligence-tests` project.
Both unit-test project inventories were empty at final inspection. Do not touch
normal `market_intel_*` containers, database volumes or unrelated projects.

## Boundaries

- These are source and Mock Data checks, not genuine company or portfolio proof.
- Existing versions are not rewritten. A full API creation without a version
  basis keeps its legacy behavior; protected UI resaves include the basis.
- Core DCF zero/default semantics and Real Options are separate next audits.
- Reverse bisection has bounded searches and no uniqueness/global-root guarantee.
- Source facts, benchmark coverage, live providers and normal deployment are
  not certified by this batch. Remaining issues live only in the limitation ledger.

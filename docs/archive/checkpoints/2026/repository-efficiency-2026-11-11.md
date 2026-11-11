# Repository efficiency pass: November 11, 2026

## Source scope

This pass starts from the published ef094c9c revision after PR12. It changes
repository tooling, stylesheet ownership, and their documentation. Financial
calculations, source datasets, migrations, dependencies, and API contracts are
unchanged. The preceding [maintenance checkpoint](repository-maintenance-2026-11-11.md)
records the earlier content cuts.

## Temporary scanner storage

The scanner keeps its database and exported images in one temporary directory
per invocation. Multiple images reuse that database. The exit trap removes it on
success or failure; JSON reports remain outside the temporary directory.
Two fake-Docker workflow tests cover both outcomes without network access.
Source reports, review receipts, backups, and failed evidence remain retained.
Machine-specific removal and preservation records stay in the local audit.

## Conservative CI selection

Repository checks always run, including documentation, source credential
patterns, dependency-lock consistency, ownership, and tooling regressions.

Only recognized Markdown-only changes skip the five expensive application,
browser, dependency, container, and recovery jobs. Missing/empty comparisons,
unknown paths, code, configuration, workflow changes, and tags run the full suite.
Comparison uses the whole event range and disables rename collapsing, so an
earlier runtime change or runtime-to-document rename cannot be hidden.

The final ci-result job rejects missing, failed, cancelled, or unexpectedly
skipped required jobs. Branch protection can require this stable result.
[Scope tests](../../../../scripts/test_ci_scope.py) cover classification,
multi-commit comparisons, renames, and incomplete job results.

## Stylesheet ownership

The 3,102-line global stylesheet becomes a 12-line import entry point.
Eleven [style modules](../../../../frontend/styles/README.md) own the rules.
Their original selector/declaration order is unchanged, including responsive
overrides. Existing source-integrity assertions follow the actual imports.
The documentation checker includes the style guide. The command inventory
includes ci_scope.py; each new command and style file has a mapped owner.

## Verification

Local verification: 363 frontend tests passed; TypeScript checking passed;
scanner shell syntax passed. A normalized CSS syntax-tree comparison is
identical before and after extraction (SHA-256
8d8192eb0c72aef5e5efdd2353d10e3655b6fdabee416f75edb9692d6906f909).

The full application, browser, security, recovery, and Python tooling checks run
through GitHub CI. Exact code and documentation-only outcomes are recorded after
verification. Software checks do not advance financial, provider, installed
runtime, or daily-use acceptance. Host-specific reconciliation records and
preservation inventories remain local.

The workflow follows GitHub's
[workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
and Trivy's [cache configuration](https://trivy.dev/docs/latest/configuration/cache/).

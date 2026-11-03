# Release preflight and browser-test isolation, October 28, 2026

The completion request continues the approved local research/demo scope. GitHub
publication is deferred to a later prompt. M01-M02 remain the only accepted gates;
this source-tooling repair does not close financial review or actual-use gates.
October 24 remains the latest installed UI and normal-browser verification.

## Defects and correction

The browser runner implicitly loaded the normal environment through Compose,
required normal settings or exported credentials, and checked occupied ports only
after destructive cleanup of its fixed test project. Playwright also explicitly
loaded the repository-root environment file and defaulted to normal port 3000.
These paths conflicted with the protected-file and disposable-test boundaries.

- The runner now uses `--env-file /dev/null` and dedicated disposable credential
  defaults. Explicitly exported test credentials still reach both services and
  browser login. Normal settings are never required or automatically loaded.
- Occupied ports are checked before cleanup and before installing its cleanup
  trap. A rejected invocation leaves an existing test project alone.
- Playwright only consumes explicit process settings and defaults to test port
  13000. The runner requests the installed Playwright package with `--no-install`.
- Failure after startup still returns the browser's failure code and invokes
  cleanup only for the intended disposable project.

Four Python command-fixture tests exercise default/explicit authentication,
occupied ports and failed browser cleanup. A TypeScript test evaluates the actual
configuration with filesystem imports and environment-file reads forbidden. The
new checks fail against the original behavior and pass after the corrections.
All command fixtures are Mock Data, with no Docker socket or database access.

## Verification and evidence limits

- Eleven Compose/runner tests pass, including the four new cases.
- All 61 repository tests pass, including documentation, secret fixtures,
  backup/recovery, dependency locks, container scans and retired-evaluator checks.
- All 320 frontend tests and full TypeScript pass using Node 24 with the existing
  installed dependency tree. The type check disables incremental output so the
  read-only source is preserved. Installed Playwright reports version 1.62.0.
- A fresh comparison checks 98 required packages and confirms the same six
  mismatches recorded October 25. Optional native packages are not certified.
  Frontend tests therefore do not certify a fresh locked install or production build.
- No full backend suite, PostgreSQL fixture, normal-data browser walkthrough,
  dependency-security refresh, production build or rollout is claimed for this batch.

Logs, dependency comparison and the initial protected-path-excluded Git status are
under `output/milestones/completion-preflight-20261028/`. Source changes are limited
to the browser runner, its Compose tests, Playwright configuration and its new
regression test, plus affected current documentation and this checkpoint.

## Access and next execution boundary

The saved project permission profile initially allowed only localhost/127.0.0.1.
The user added `registry.npmjs.org` and `snapshot.debian.org` after the access
failure. Both entries are verified in the saved file. Subsequent HTTPS HEAD probes
still return `403 blocked-by-allowlist`, and the renewed npm escalation is rejected
as outside the active allowlist. No alternate download path bypassed this denial.

Reload the app/session configuration and verify those two destinations before
resuming the locked-dependency restoration, signed-OS build and October 25 local
rollout continuation. If a fresh session still rejects access, inspect the active
permission profile or administrator policy instead of broadening access silently.
Preserve the no-new-local-datasets boundary and all normal data/rollback evidence.

The operating-system Git/Python tools remain unavailable or restricted. Existing
network-disabled tooling images supply read-only Git inspection and isolated checks.
No normal service, database, volume, dependency manifest/lock, protected environment
file or Git index was changed. The user's permission edit is preserved separately
from the source-tooling repair. Financial/valuation reviews, coordinated private
credential setup and five actual business days of research/demo use remain governed
by the completion tracker and the single limitation ledger.

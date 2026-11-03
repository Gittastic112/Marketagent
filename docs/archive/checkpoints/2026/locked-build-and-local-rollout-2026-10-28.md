# Locked builds and local rollout, October 28, 2026

This completes the build/rollout continuation after the October 25 cleanup and
[October 28 browser-test isolation](release-preflight-isolation-2026-10-28.md).
The user's npm/Debian network allowances work in the resumed session. GitHub
publication remains deferred. No financial facts, saved models or milestone
acceptance states change in this release.

## Source and security correction

An explicit, environment-file-free build context contains 1,007 source files.
The supported Linux ARM64 frontend installs the unchanged lockfile: all 98
required and eight installed optional packages match; 60 incompatible optional
packages are absent. The six previously identified host-tree mismatches remain
on the Mac; they no longer block verification of the supported Docker images.

The first OS scan correctly blocks installation: `openssl` and `libssl3` carry
CVE-2026-84782. Both Dockerfiles advance their signed Debian snapshot from
October 11 to October 28, preserving signature checking and incomplete-update
failure. The rebuilt frontend contains `3.0.22-1~deb12u2`, the fixed Bookworm
version in the [Debian advisory](https://security-tracker.debian.org/tracker/CVE-2026-84782).
Application package versions, image-base pins and migrations are unchanged.

The final pinned Trivy scan reports zero available HIGH/CRITICAL fixes in each
supported image. All remaining findings are retained without suppression:

| Image | Low | Medium | High | Critical | Unknown |
|---|---:|---:|---:|---:|---:|
| Backend | 61 | 58 | 44 | 0 | 1 |
| Frontend | 85 | 87 | 56 | 1 | 1 |
| PostgreSQL | 138 | 109 | 61 | 1 | 8 |

Debian says the frontend's [zlib/MiniZip finding](https://security-tracker.debian.org/tracker/CVE-2023-45853)
does not affect the binary packages built from this Bookworm source. PostgreSQL's
[libxml2 finding](https://security-tracker.debian.org/tracker/CVE-2026-6653)
remains classified minor/no-DSA for Trixie despite the scanner's critical rating.
A passing update gate is not a clean security audit or proof of exploitability.

## Validation

- Fresh production frontend/backend and builder/test images build successfully.
- Final images pass 320 frontend tests, full TypeScript, 22 wire contracts,
  lock consistency, `pip check`, and 1,766 backend tests. Six separate PostgreSQL
  integration checks remain opt-in skips here; their earlier remote evidence is
  dated separately. Five dependency deprecation warnings remain.
- All 61 repository/operation tests pass using command fixtures and temporary
  files. These tests do not operate the normal database or restore a backup.
- `npm audit` reports no vulnerabilities. `pip-audit` reports none in 69 entries;
  the omitted pinned `packaging` 26.3 is separately checked against its exact
  PyPI version metadata, also with no reported vulnerabilities.
- Both application OS snapshots are rebuilt and rescanned. Initial failed
  network-disabled build attempts, the failing first scan, and helper attempts
  missing read-only manifest/cache mounts remain retained with their corrections.

## Installed runtime and browser proof

| Service image | Docker image identity |
|---|---|
| Backend and workers | `sha256:9c68f5e0c75ecf6f6d4d999d1a6b510037ed01af1a486063301c1f5e69a29fdf` |
| Frontend | `sha256:49fb5fb2a31b3897d1310f79099eaeb7fd81ffea042c86192992002bd1ad27d0` |

A quiesced 128,278,119-byte backup passes SHA-256 and PostgreSQL archive listing.
Its digest is `a66526506add41b834933e6bde7fef8f3e040aa05ef39709cbd40b79396822e3`.
This is a fresh dump, not a new restore rehearsal. The original PostgreSQL
container, volume, schema and runtime settings remain; settings are handled only
in memory. Ports remain bound to 127.0.0.1. Protected environment files are never
read directly or through Compose, settings or browser configuration.

Fourteen authenticated views pass at 1440px and 390px: fast Data Health, explicit
evidence/coverage/backfill diagnostics, Apple financials, valuation and portfolio.
The header matches the latest 100 returned runs and the table displays 25;
the limited window is disclosed. Mobile table focus and arrow-key scrolling
pass. There are no browser exceptions, backend writes, horizontal page overflow
or automated accessibility violations. Desktop/mobile coverage screenshots are
also visually inspected. The browser uses Playwright 1.62.0, axe 4.13.0 and
Chromium 151.0.7922.34. This is existing-data read-only proof, not a new fixture
workflow or current financial-input certification.

All 109 table and source-asset fingerprints match before/after installation and
browser checks. Installed backend source matches all 448 expected files; the
frontend build ID matches its tested builder. The database remains at the single
expected migration head `s1s1s1s1s1s1`. Three short idle samples show healthy
services and no restarts; they do not establish five business days of use.

Daily Brief scheduling resumes. Source refresh and pgAdmin remain stopped with
restart disabled. Four exact old containers are copied and byte-verified before
removing their obsolete Compose registrations; their files, logs, settings and
images remain recoverable. There are now 31 retained rollback copies outside the
six-service project. Compose discovers exactly the six current services and
successfully lists the retained dump through its normal PostgreSQL exec path.
The full backup script is not rerun because it creates a disposable restore
database, which the user has deferred.

Evidence and corrected execution recipes are under
`output/milestones/locked-rollout-20261028/`, including source/package manifests,
both scan sets, build/test/audit logs, backup receipts, browser results/screenshots,
runtime identity and rollback-copy receipts. Existing failed evidence and backups
are preserved. The [limitation ledger](../../../agent_capabilities_and_limitations.md)
owns remaining financial review, credential and acceptance work.

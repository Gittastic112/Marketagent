# Dependency and PDF evidence repair: October 21-22, 2026

The normal research/demo runtime now uses the security dependency updates and
correct table-cell PDF evidence links. No financial review decisions or data
change in this batch. Selected coverage stays at 32 periods, 871 facts, 911
revisions and 328 normalized values across the existing 11 securities.

## Failure, correction and validation

CI on `04aa15627ceac93b617d3e5771f4b824bac7cfd4` passed release-baseline,
recovery-quality-gate and container-security. Dependency-security found nine
advisories in Pillow/certifi; browser-quality-gate passed 63 of 64 workflows.
Original push/PR runs are `39659467985` and `39659475875`. Logs are retained.

Only Pillow 12.3.0 -> 13.0.0 and certifi 2026.7.22 -> 2026.10.19 change in the
66-package runtime and 70-package test hash locks. Python 3.14, pip 25.3 and
pip-tools 7.5.2 reproduce them. Both built images pass pip check. The audit returns
zero vulnerabilities in 69 dependency entries; it omits packaging, whose pinned
26.3 PyPI metadata is separately checked with zero advisories. This is a dated
result, not a guarantee about future findings or the earlier OS-level limitations.
Official references: [Pillow 13](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
and [certifi release](https://github.com/certifi/python-certifi/releases/tag/2026.10.19).

The browser failure exposed a real presentation defect: table candidates store
precise geometry in `cell_bbox`, while the helper only read `bounding_box`. Valid
table cells therefore opened the raw PDF and bypassed the rendered highlight page.
The helper now explicitly selects the coordinate field by locator type. It does
not substitute the entire table box when cell geometry is absent or invalid.
Event evidence retains its existing strict geometry path.

Two regression tests cover exact table-cell coordinates and invalid/missing,
nonfinite, wrong-page and wrong-coordinate-system fallback cases. The first test
fails before the fix; all 12 helper tests pass afterward. The existing PDF workflow
now asserts the evidence URL and visible image before decoding, preserving its
mobile Tab/ArrowRight/axe checks and unchanged timing budgets.

All 304 frontend tests, TypeScript and the production build pass. The updated
dependency image passes 106 pure PDF/coverage/derivation/resource-limit tests,
without a database fixture. Ten retained official PDFs reproduce all 784 candidates
exactly, including values, units, locations and warnings. One selected page from
each report matches the old renderer's dimensions and decoded RGB hash; two new
renders were visually inspected. The render baseline was freshly generated using
the prior installed Pillow version, not represented as an older screenshot.

October 22 CI on `fed0210de389d80ab9211d6c1748a947a618f0bf` passes all 64 browser
workflows, including the table-cell case, plus 1,701 backend tests and six separate
PostgreSQL integration checks. Six opt-in tests skip in the broad backend suite.
Existing normal data contains text-row locators; CI supplies the table-cell E2E proof.
The CI artifact URL download was blocked by the host policy even after escalation;
logs were retained and the failure was reproduced with the parser/helper regression.
No alternate download route bypassed that denial.

## Installed runtime and preserved data

Backend/workers: `market-intelligence-security-runtime:20261021`,
`sha256:d11412589ea22ad8c15015304fa37167b11f64fd7bcc1b3adf3936b5f9440505`.
Frontend: `market-intelligence-security-pdf-frontend:20261021`,
`sha256:ed0e4fb4b860268802ab4da3c2f0a84a2000822b03c529c536b2e054ae9a97e6`.
The original PostgreSQL container/volume and schema `s1s1s1s1s1s1` are unchanged.
Runtime settings travel in memory; no protected environment file is read or saved.
Published ports bind localhost. Daily Brief resumes; source refresh and pgAdmin
stay stopped with restart disabled.

A quiesced pre-rollout dump is 111,095,724 bytes, mode 0600, SHA-256
`4f4783ffbfea88da4201e5281b48729fabc52090c14b301401a5669a1e777599`.
Archive listing passes. No new restore or encrypted off-device proof is claimed.
No new dataset, database, trade or AI/provider scan is created.

Final normal-browser verification passes 16 desktop/mobile views, all 456 reported
value comparisons and 164 held-candidate checks. Mobile PDF/table keyboard scroll
works; no backend writes, browser errors, page overflow or axe violations occur.
Readiness is 409-3,943ms under the unchanged 15-second limit. All 109 table
fingerprints match the pre-rollout baseline. An earlier harness attempt started
before rollout readiness and received Docker 409; it is preserved separately.
The final harness requires the completed rollout receipt and healthy exact IDs.

Nine stopped rollback containers still carried active Compose labels. Each was
retained outside the active project on the same image, with 65 writable files
verified by bytes, modes and ownership, equivalent settings/read-only binds and
saved Docker logs. Replacements disable networking, ports and restart. Exact old
registrations were removed only after verification; no images or volumes were
deleted. All six normal container IDs are unchanged, and safe Compose discovery
lists exactly those six services. Intermediate failed archive attempts are retained;
the final receipt verifies every replacement. No byte savings are claimed.

A post-work sample records 0.61% combined CPU and 1,169.16MiB container working set,
excluding VM overhead. Docker reports 25.81GB images, 3.338GB volumes and 4.487GB
build cache. Shared layers make these totals non-additive. Host free space is about
27GiB. Backups, rollback images, volumes and failed evidence remain protected.

## Evidence and next gate

Receipts, test logs, locks, PDF parity, source manifests, screenshots, backups,
rollback verification and replay recipes are under
`output/milestones/dependency-security-20261021/`. The local skill folders and
unrelated dirty checkout/index are preserved and excluded from publication.

Six source files and five linked status documents form this cross-cutting batch:
dependency manifests/locks, evidence helper/tests and their installed-release
status. M09-07 remains open for the subsequent Next.js security update below. M05/M06
accounting/source-basis work continues. M01/M02 remain the only accepted milestones,
at 20 acceptance points. The [tracker](../../../roadmaps/completion-tracker.md) owns
gates and the [single ledger](../../../agent_capabilities_and_limitations.md) owns
operator and product limitations. Draft PR #2 owns the latest published source/checks.

## October 22 Next.js security follow-up

Both `fed0210` CI runs pass browser, baseline, recovery and container-security jobs.
The dependency job instead encounters Next.js advisories added to GitHub's advisory
database on October 22. [The official 16.4.1 release](https://github.com/vercel/next.js/releases/tag/v16.4.1)
provides the fix. Existing sharp 0.35.5 already satisfies the image-library advisory's
workaround; that finding does not establish this installed app's exploitability.
The App Router/Server Actions denial-of-service advisory requires the Next.js upgrade.

The declared minimum `^16.3.6` previously resolved to locked 16.3.8. Next.js is now
pinned exactly to 16.4.1; only it and its nine matching `@next` packages change.
React, sharp and every unrelated package version remain. Fresh npm ci, all 304 tests,
production build, TypeScript and a zero-vulnerability npm audit pass. The new image
is `market-intelligence-next-security-frontend:20261022`,
`sha256:6d1b305f81a0c52144369884cc145201f568e1609077a1c2ed5bcf51730a6c2c`.
Its runtime metadata confirms Next.js 16.4.1 and sharp 0.35.5. The backend image
above is unchanged. The build uses an explicit 340-file manifest excluding protected
environment files; only its package manifests and temporary build recipe differ.

Normal rollout/browser checks pass all 16 financial/PDF and six existing-portfolio
views. They retain 456 value comparisons, 164 held candidates, mobile keyboard access,
Mock Data/stale/partial/unavailable states, and no errors, writes, overflow or axe
violations. Four additional actual-viewport screenshots confirm mobile PDF geometry;
the full-page capture's sticky-header artifact remains separately recorded.
All 109 table fingerprints are unchanged. Their identical earlier baseline permits
reuse of the verified October 21 dump, avoiding another 111MB backup. Daily Brief
resumes; source refresh and pgAdmin stay disabled. No new dataset is created.

The prior frontend's files/logs/image are retained outside active Compose discovery,
bringing this batch's detached rollback total to ten. The active project still has
six services. Removing only the successful temporary builder stage reclaims exactly
849,703,505 Docker layer bytes; installed, rollback and prior verification images and all
volumes remain. Its source manifest, build log and recipes remain reproducible.
Post-work sampling records 1,258.11MiB working set and 0.77% combined container CPU,
excluding VM overhead. Images use 25.88GB, volumes 3.339GB and build cache 4.487GB;
these shared totals are not additive. The host has about 26GiB free. An earlier
sample during visual checks is separately retained and is not described as idle.

Receipts and retained setup failures live under `output/milestones/next-security-20261022/`.
This follow-up changes two package files and five linked status documents. Local
verification is complete; the full CI matrix for the new dependency source remains
pending. Prior-head success is not substituted for that gate.

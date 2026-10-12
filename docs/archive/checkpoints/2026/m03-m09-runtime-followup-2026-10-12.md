# M03-M09 recovery, runtime and workflow follow-up

October 12, 2026. The macOS backup blocker is fixed and the integrated source is
installed in the normal local app. M01-M02 remain the only accepted milestones.
This checkpoint closes specific checks without replacing human review, genuine
inputs, off-device recovery or the remaining browser coverage with fixture proof.

## Backup repair and actual recovery

The prior failure happened after dump/content verification, when macOS rejected
renaming the entire partial directory. A harmless directory rename probe also
failed, including escalation; file rename worked. No immutable flag or capacity
problem explained it. The managed permission profile is a likely cause, not a
proven macOS TCC diagnosis. No Full Disk Access or broader permission change was made.

Format 3 creates the final private folder immediately, then publishes an atomic
COMPLETE file containing the exact manifest hash only after validation. Payload,
checksum and marker writes are flushed; this is not a full power-loss guarantee.
Restore rejects absent, altered or linked markers before touching the database.
Verified format-2 folders still work. Format 1 is explicitly count-only; old
partial folders remain incomplete and are retained. Retention skips incomplete,
unrelated, linked and legacy folders.

The regression first fails with directory rename unavailable, then passes the
new workflow. Twenty-nine recovery tests cover completion, corruption,
interruption, failure, retention and compatibility; all 54 repository-tooling tests
also pass. The real concurrent-write drill uses an owned tmpfs PostgreSQL project:
the dump retains three original sources while later writes reach 101, verifies
all 109 table fingerprints and both original public/private PDF bytes, and restores
private finding/review and portfolio relationships. Restore verification takes
10 seconds; the complete drill takes 35 seconds. The normal database is never
replaced by that test.

Complete normal backups include:

- Pre-rollout: backups/20261012T042014Z-24165-market-intelligence.
- Final quiesced preflight: backups/20261012T050944Z-29914-market-intelligence,
  dump SHA-256 9ebb4cc56f3ac0cb35316b8919be6e5aa380779b04d5181cac9efea0edaffd62.
- Standard Compose backup after registration repair:
  backups/20261012T051122Z-24714-market-intelligence.
- Final standard backup after browser verification and scheduler resumption:
  backups/20261012T051457Z-29702-market-intelligence.

Directories/files retain 0700/0600 permissions. The failed service-selection
attempt is retained without COMPLETE in
backups/20261012T050715Z-6464-market-intelligence. No incomplete folder was
manually blessed. No backup, normal volume or immutable source was deleted.
These same-disk copies do not close encrypted off-device recovery.

## Source and workflow changes

| Milestone | Change and evidence |
|---|---|
| M04-05 | Five official India source links are checked October 12. The read-only checklist matches NSE market, ISIN and local symbol before displaying the issuer link, checked date, target periods and required reports. Unmatched/missing checklist data returns no official guide. Existing manual PDF/excerpt/page/currency/scale review remains; selecting a source approves no value |
| M04 support truth | Capability availability follows the selected price adapter and its own key. Personal Yahoo is available without an unrelated key; FMP stays unsupported even with a key. SEC requires a valid contact and FRED reflects configuration. Missing default catalog entries are filled without overwriting existing notes. Data UI distinguishes configuration from coverage/freshness |
| M06-03 | Audited FCFF, financial-services, distress, explicit-input FCFE/DDM, scenario and reverse boundaries against their owning engines and regression suites. Finite/convergence/currency/zero/identity gates remain; historical outputs are not rewritten. A new real PostgreSQL pair saves from one basis: one creation, one conflict, exactly two versions, original story/output unchanged and explicit zero preserved |
| M06-06 | Saved options service and panel label the analysis experimental. Retained custom calculation/eligibility endpoints keep compatibility and aliases, add OpenAPI deprecation and explicit unchecked-basis warnings. No formula change or claim of certified options value |
| M07-07 | Import preview writes no prices; exact SHA mismatch rejects apply. Successful apply, duplicate-only disabled UI/API idempotence, conflicting rows, clearing and mobile states pass. Late preview replies cannot follow navigation into another portfolio. Editing a recorded fee makes historical returns provisional while saved snapshots remain byte-identical |
| M08 evaluation boundary | Evaluation v3 exposes citation/policy-only scope and interpretation quality not evaluated. Four added adversarial Mock Data cases cover wrong numbers, wrong periods, unsupported causal inference and source instructions. Exact citations deliberately pass while human review remains pending. This is not a human-reviewed quality set or provider injection test |
| M09 review/session repair | Saving AI review refreshes its server-rendered metadata; both visible status displays agree. Request gates prevent late suggestion/validation/review effects after unmount. An invalidated local session receives 401 through the proxy and cannot reopen private pages |

Official selections were checked at
[Reliance](https://www.ril.com/investors/financial-reporting),
[HDFC Bank](https://www.hdfc.bank.in/about-us/investor-relations/annual-reports),
[Bharti Airtel](https://www.airtel.in/about-bharti/equity/results/annual-results),
[ICICI Bank](https://www.icici.bank.in/about-us/annual/2026), and
[SBI](https://sbi.bank.in/en/web/corporate-governance/annual-report-).
FY2025-26 report links are present. That does not establish extracted/reviewed
financial coverage. No normal source candidate, assumption or AI output was approved.

The M06 audit uses the valuation map and owning forecast, terminal, bridge,
financial-services, distress, FCFE/DDM, scenario, reverse and saved-version
services. Existing independent arithmetic/integrity tests pass in the full suite;
the follow-up adds concurrency and experimental-boundary proof. It does not close
the separate accounting/equity input, full narrative/export or genuine-input gates.

## Integrated validation

| Gate | Result |
|---|---|
| Backend | 1,502 passed, four PostgreSQL skips, five upstream warnings, 131.20 seconds |
| PostgreSQL | All four skipped integration checks pass separately in 2.11 seconds |
| Frontend | 264 passed; production build includes TypeScript validation |
| Browser | 33 passed, one worker, no retries, 3.7 minutes |
| Page matrix | All 50 routes at 1440px and 390px, 100 page screenshots/timing samples |
| Operations | 54 repository/recovery/lock/scan fixture tests pass |
| Contracts | 279 public paths, 511 schemas, 381 protected/public inventoried operations; compatibility, pure-schema and wire guards pass |
| Builds | Final standalone frontend and backend runtime build successfully |

The backend uses the network-disabled Linux test image with current source/data
mounted read-only. PostgreSQL uses the separate owned disposable database and
random test schemas, never normal records. Browser inputs are labeled Mock Data;
the final run writes artifacts inside its container before copying them out.
Temporary source staging excludes protected environment files and generated caches.

Earlier failures remain recorded: duplicate-only import was incorrectly expected
to enable apply; a test fixture double-counted holdings before a buy; a delayed
preview assertion matched a hidden React stream copy. Those fixture/assertion
errors were corrected without changing the product's trust gates. A three-repeat
race run then hit host-mounted artifact-directory ENOENT errors before execution;
container-local artifacts yield three passing repeats. The full final matrix passes.
Initial frontend unit runners omitted repository files; corrected read-only mounts
produce all 264 passes. A production TypeScript shadowed-variable error was fixed.

Artifacts: output/milestones/m09/followup-final-browser includes the 100 page
screenshots and functional evidence. Visual review confirms matching AI review
metadata and mobile import layout. Earlier failed runs remain in their separate
output folders. CI preserves browser evidence for seven days.

## Runtime rollout and Compose verification

The final normal deployment uses:

| Service | Image identity |
|---|---|
| Backend and both workers | market-intelligence-m09-followup-runtime:20261012, sha256:f07015be3fb5ce8514d1b154a26278ca39a2a695d161a707c37ab6d266c4adef |
| Frontend | market-intelligence-m09-followup-frontend:20261012, sha256:d8f71488cd3cfaa00c99030b3d1535a608c8e3f7289cc3ed36a80c841fa66c0e |
| PostgreSQL | pinned PostgreSQL 16, sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d |

The runtime's 443 backend/migration/script files match the environment-free build
snapshot: SHA-256 edc65400c1fe37c4c4f999df1b8b97237af58eeefd9cdfc3b5e4c144f858fc2e.
No schema change: head remains s1s1s1s1s1s1. PostgreSQL retains
market-intelligence-md-filescopy_marketintel_postgres_data. Settings are compared
in memory and remain identical; they are neither printed nor read from protected files.

The first manually recreated containers lacked Compose's discovery hash label.
A normal backup therefore selected an older stopped PostgreSQL registration.
The quiesced preflight uses the same dump/verification script against the explicitly
identified live container, then the rollout repairs registration. A deliberate
noncanonical config marker makes future reviewed Compose up reconcile its own
configuration instead of pretending this was a Compose-rendered hash.

Stopped containers still carrying the project labels could also be selected by
dependency startup. Nine redundant stopped registrations were therefore removed
only after checking current settings, mounts and writable changes. Those changes
were generated Next.js/Yahoo caches and init paths, not user data. Prior images
are explicitly tagged market-intelligence-local-rollback with dated generation/
service tags; no image or volume is removed. An unregistered old PostgreSQL
rollback container remains. Standard Compose backup, ps and scheduler start now
select the actual current stack. The failed startup was a port-binding rejection,
not a database restore or a second running database.

All 109 table fingerprints match immediately across final rollout. Final normal
browser verification covers 12 routes at 1440px/390px: 24 views, no browser errors,
no page overflow and two forbidden-Origin 403 checks. The maximum ready time is
628 ms. Official RELIANCE guidance and configuration disclaimers are visible.
No fixtures are seeded, AI is called or financial facts approved.

Those page reads add one missing FRED capability row, taking that catalog from
eight to nine, and two SEC discovery runs (45/46, ten fetched and zero created
each). The other 107 table fingerprints remain unchanged. Daily Brief scheduling
then resumes; source refresh and pgAdmin stay disabled with restart=no. All
normal restart counts are zero, web/backend/database are healthy, and ports
3000/8000/5432 bind only 127.0.0.1.

Normal artifacts: output/milestones/m09/followup-normal-browser/results.json and
24 screenshots. Recovery/build/runtime logs and metadata are under the local
/tmp/mi-architecture-20261010 evidence directory; backups are retained separately.

## Performance and resource boundary

Docker Desktop: eight vCPUs, ARM64, 4,106,604,544 bytes VM memory. The separate
first-visit/warm experiment uses four companies, 66 prices, one portfolio, four
transactions, two snapshots and one raw document. Four routes over six rounds
give 24 samples, maximum 389 ms, with an 886 ms performance-tab interaction.
Authentication warms shared code; database/OS caches are not cold.

| Final full-matrix viewport | Views | Median | p95 | Maximum |
|---|---:|---:|---:|---:|
| 1440 x 900 | 50 | 534.5 ms | 1,189 ms | 1,896 ms |
| 390 x 844 | 50 | 490 ms | 1,253 ms | 2,315 ms |

The existing 15-second route gate is unchanged. These measurements and passing
query/row-budget tests are not large-corpus, multi-user or fully cold-load proof.

After disposable cleanup, four normal containers use about 514 MiB in a quiet
sample, with combined CPU 0.33% on Docker's per-core scale. VM overhead is extra.
The bounded unused-cache cleanup reclaims another 2.513 GB. Docker reports
61 images/22.98 GB, seven containers/four running, 18 volumes/3.114 GB unchanged,
and 156 cache records/10.86 GB. Shared layers mean these sizes cannot be added as
physical disk use. No persistent cap, automatic prune or monitor was installed.

## Acceptance and publication

The tracker closes M04-05, M06-03, M06-06 and M07-07 and retains M09-07's integrated
gate with fresh evidence. M03-04/07 still require host/credential coordination and
encrypted off-device recovery. M05 and later genuine financial/portfolio/AI review
cannot be replaced by these fixtures. Remaining technical browser/control,
traceability and accessibility coverage is still explicit in the
[single ledger](../../../agent_capabilities_and_limitations.md).

Git publication follows implementation, rollout and documentation, as requested.
During clean-checkout CI review, the disposable browser Compose was found to lack
the two checked-in catalogs used by official India guidance. The normal runtime
already mounts them. Browser Compose now mounts only research-scope.json and
scoped-source-checklist.json read-only, preserving the image/data boundary.
Compose validation and all seven infrastructure checks pass. All three focused
filing/provider browser cases pass in 6.9 seconds using those two files rather
than a whole-data-directory mount. At ac601ef7, both GitHub browser runs passed
32 cases and failed only the missing-catalog guide; release, dependency, container
and recovery checks all passed. The [failed run and artifacts](https://github.com/Gittastic112/Marketagent/actions/runs/38262665999/job/114856874208)
are retained, and the resulting head reruns the complete clean-checkout suite.
The [draft PR](https://github.com/Gittastic112/Marketagent/pull/2) owns the resulting
head and fresh checks. An explicit-path isolated snapshot preserves the shared
checkout/index; no merge, force push, secret publication or broad staging is done.
The pre-follow-up PR head is 124531c3ea53d94427f922a42d906fc2a6fe6357.

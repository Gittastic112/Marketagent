# Financial input review and installed integrity repairs

November 2, 2026. Existing-data local research/demo scope under
AUTH-20261017-DELEGATED-REVIEW. Git/GitHub publication remains deferred.
This is delegated agent review, not personal or independent human certification.

## Financial decisions and actual effects

The [consolidated review](../../../../data/reviews/financial-input-review-20261102.json)
records 249 selected field reviews and 55 explicit unavailable-field decisions
across 11 securities, checked against ten retained original-report hashes and
current financial/source signatures. The [application receipt](../../../../data/reviews/financial-input-application-20261102.json)
identifies exact draft IDs, patches, source packets and evidence hashes. The
[decision register](../../../../data/reviews/research-demo-decisions.json) appends
11 decisions while preserving every earlier decision and five personal approvals.

- HDFC/ICICI/SBI common book equity excludes separately presented noncontrolling
  interests and award reserves. Parent reported profit is not certified recurring
  income or bank distributable capital. The low-confidence reference uses ten
  relative years, a 15% nominal INR equity hurdle/terminal ROE and 3% book growth.
- Six US security drafts distinguish carrying debt and finance leases, investment
  scope, parent equity and minority claims. Alphabet's USD3.4bn NCI already includes
  redeemable NCI. Explicit forecast and financing assumptions remain hypothetical.
  Operating-lease zero is only an already-expensed lease-policy choice, not a
  claim that no lease liabilities exist. NVIDIA's complete debt scope stays missing.
- Reliance/Airtel use reviewed historical proxies and a named stationary INR
  reference: flat revenue/margin, 25% assumed tax, 14% discretionary hurdle and
  zero terminal growth. This is not an issuer forecast or issuer WACC. Six
  unsupported risk components remain null; Reliance revenue-allocation gaps remain.
- Current prices, unsupported award values and valuation share denominators stay
  unavailable. Historical weighted-average EPS shares are not a current denominator.
  The retained-source follow-up is in the US packet's missing-inputs audit.

No saved model is promoted. No financial history, source original, portfolio,
existing assumption set, output or projection is rewritten. Application changes
only valuation_setup_drafts; 108 other tables and all source assets are unchanged.
Normal coverage remains 33 periods, 929 facts, 1,003 revisions and 336 normalized values.
The API records manual draft patches as User Assumptions with prior provenance in
`replaces`; dated review notes link exact source packets. These labels do not become
machine-certified source facts merely because an agent reviewed them.

## Defects found and repaired

A review-only save incorrectly supplied new-draft defaults, resetting Reliance's
scenario to Base. Nine company applications had succeeded before the assertion
caught the partial Reliance save; Airtel had not run. The failed receipt remains.
The update service now applies only explicitly supplied patch fields. Empty and
cash-only patches preserve scenario, horizon and reinvestment method. The retry
checks the complete known interrupted draft before restoring Reliance and applying
Airtel; the nine earlier successes are not reapplied.

Both forecast engines previously emitted `2024 + year_index` without a fiscal
anchor. New projections use null calendar dates; API serialization also withholds
legacy dates without changing their stored integers or calculation amounts.
Relative-year labels remain. Migration t2t2t2t2t2t2 follows s1s1s1s1s1s1 and only
allows null in the calendar_year column. Original application row fingerprints
remain identical across migration; only Alembic metadata changes. Downgrade will
refuse new null rows. Do not restart an old integer-only image against those rows
or force a downgrade by inventing dates/deleting data; use a reviewed forward repair.

## Verification and retained failures

- Locked production images build. 1,815 backend tests pass, six optional PostgreSQL
  tests skip, and five deprecation warnings remain. Frontend: 322 tests and full
  TypeScript pass. All 22 API contracts and dependency locks pass; 62 repository
  checks pass. No new disposable PostgreSQL or seeded browser database is created.
- The initial regression invocation lacked a test SEC identity; its corrected run
  reproduced the save bug. The first calendar test also contained a wrong fixture
  keyword, then exposed real null persistence failure. Both failed logs remain.
  The first full suite passed 1,814 tests but found the migration test pinned to
  the old head. Its updated assertion and the full rerun pass.
- The first installation audit omitted the separate database revision metadata
  row when allowing the migration change. Exact inspection confirms only the two
  expected migration markers changed. The corrected audit passes without rerunning
  migration, rewriting application data or rolling back the healthy installation.
- Existing-data browser checks cover all 11 reviewed drafts at 1440px and 390px,
  with no detected accessibility violations, duplicate IDs, horizontal overflow
  or page errors. All 11 UI create buttons are disabled; real promotion requests
  return 409 for unresolved inputs. Ten existing forecast rows return null dates
  and preserve relative ordering. The first pass refreshes only provenance/source
  metadata on three bank drafts; all values, review selections, source signatures
  and 108 other tables remain unchanged. The retained failed read-only audit is
  followed by an exact effects check. The continuation adds six expanded bank,
  US and India form views and verifies rendered values/checkboxes. All 109 table
  fingerprints and assets remain unchanged across its 28 views and rejected writes.
- New quiesced PostgreSQL dumps pass archive listing and SHA-256 checks. These are
  retained same-disk backups, not a newly performed restore or off-device proof.

## Runtime and remaining boundary

Evidence is retained in output/milestones/financial-review-20261102. The release
subdirectory owns exact image IDs, source manifest, migration inventory, browser
results, retained-copy receipts and runtime proof. Backend/frontend/both workers
use the 20261102-financial images. The original PostgreSQL volume and runtime
settings are preserved in memory, without reading protected environment files.
The Daily Brief scheduler is restored; source scheduling and pgAdmin remain stopped
with restart=no. All published ports remain 127.0.0.1. Four additional rollback
copies are detached after byte/log/config checks, for 45 retained copies and six
normal project registrations. Images, volumes, failed evidence and backups remain.

Docker became unavailable after a chat interruption. The first final documentation
checks could not start; both attempted startup methods failed. The user reopened
Docker, then documentation validation passed: 117 active Markdown files, 930 local
links and 12 documentation tests. The completed reviews are additionally retained
in credential-backup/database.dump: 128,356,222 bytes, SHA-256
c8cbb7d99b875e0210f9ba512285655f84082ba29f10e23ddc3653eb374cf8b5.
Its archive/hash checks pass without claiming a new restore. The post-restart
runtime receipt separately verifies installed source, service state and unchanged
tables/assets after that backup; earlier receipts and failed checks remain intact.

Future Compose startup now requires a privately supplied database password and
has no fallback admin password. This does not rotate the running database role.
The [private maintenance procedure](../../../08-execution-runbook.md#rotate-the-local-database-password)
and current-image override are prepared. Actual private credential rotation is
operator work; credentials must not enter chat. The
[single limitation ledger](../../../agent_capabilities_and_limitations.md#ordered-operator-handoff)
owns remaining gaps. M03/M05/M06 acceptance is not inferred from these checks;
actual user-use days remain zero and GitHub stays deferred.

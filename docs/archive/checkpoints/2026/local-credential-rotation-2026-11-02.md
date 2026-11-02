# Local database credential rotation and scoped acceptance

November 2, 2026. The operator reports completing the private procedure. The
agent verifies its runtime effects without reading protected configuration files
or recording credential values. Git/GitHub remains deferred.

## Verification

Evidence is retained in output/milestones/financial-review-20261102:
The [acceptance receipt](../../../../data/reviews/local-security-acceptance-20261102.json)
binds the successful checks and dated prerequisite evidence by hash.

- credential-rotation/authentication.json verifies a fresh connection with the
  configured database credentials, rejection of the previous password and rejection
  of a random incorrect password. The PostgreSQL and all three database-client
  settings agree. Credentials pass only in memory; no values enter the evidence.
- credential-rotation/receipt.json verifies all 109 application-table fingerprints
  and both source-asset stores against the completed-review backup. The existing
  named PostgreSQL volume and verified image IDs remain. Published ports are local.
- credential-rotation/browser.json verifies anonymous API rejection, successful
  existing local sign-in, an authenticated database-backed company read, an existing
  valuation list and unchanged selected values/reviews in all 11 financial drafts.
  No page errors occur. browser-preservation.json verifies unchanged tables/assets.
- release/runtime-proof-after-rotation.json verifies 450 installed backend files,
  migration head t2t2t2t2t2t2, healthy app/database services, three runtime samples
  without unexpected restarts and preserved data after the operation. Daily Brief
  scheduling runs; source scheduling and pgAdmin remain stopped with restart=no.
  There are six normal project registrations and 45 stopped retained copies.

The initial audit expected only DATABASE_URL changes. It stopped before the
authentication tests because Compose also removed the old LOCAL_DEMO_MODE key
from the frontend. The key has no consumers in the current app or declaration in
normal Compose. A source check establishes this; existing login/provider secrets
are unchanged. The corrected audit permits only that exact removed legacy key
alongside the expected database-client changes. Both initial failures are retained.

The old password was used only for the negative authentication test. The agent did
not choose, change, print or store the new password, inspect protected file contents
or verify their current permissions. Application-login, provider and optional admin
credentials were not rotated. The existing completed-review backup remains valid
for unchanged application data; no new restore or off-device proof is claimed.
Retained old containers still carry their historical settings. Do not start them
without a reviewed current configuration and schema-compatibility plan.

## Acceptance under the existing research/demo scope

The [October 17 scope revision](../../../roadmaps/completion-tracker.md#scope-revision-approved-october-17-2026)
defers host protection and off-device recovery while retaining local application
authentication, local-only ports and coordinated database rotation in scope.
The [recovery](m03-recovery-2026-10-11.md), [normal recovery follow-up](m03-m09-runtime-followup-2026-10-12.md),
[security](m03-security-2026-10-11.md), and
[locked-runtime](locked-build-and-local-rollout-2026-10-28.md) evidence retain their
dated scope. This verified rotation closes M03's remaining in-scope blocker.

M04's seven recorded checks were already verified, with M03 as its sole open
prerequisite. The [identity/ingestion](m04-ingestion-2026-10-11.md) and
[consuming-page](m04-m09-coverage-2026-10-12.md) evidence remains applicable; the
current source suite and November browser checks introduce no unresolved M04
regression. No new live provider probe was made during password verification,
and historical connectivity does not establish current quote freshness.

M03 and M04 are therefore accepted for the agreed research/demo profile on
November 2: four of ten gates, 40 acceptance points, next M05. This is not a
percentage of engineering effort or final user acceptance. Original deferred
host/off-device checkboxes remain unchecked. Complete financial/model inputs,
actual-use days and subsequent milestone dependencies remain open. The user still
has zero recorded actual-use days; completing password maintenance is not a use day.

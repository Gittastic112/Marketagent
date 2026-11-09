# Portfolio visibility and research UI, November 9

The dashboard selected the oldest account regardless of whether it still held
anything. The requested Sample portfolio was already populated, but the empty
legacy account hid its value. The dashboard now orders owned accounts by nonzero
holdings or cash, offers an explicit URL selector, and reads the selected
account's latest stored snapshot. Explicit empty selections remain empty; missing
or foreign IDs fail without substituting another account. Snapshot dates, missing
prices, missing FX and valid zeros retain their existing meanings. No provider
calls, duplicate portfolio, migration or destructive data rewrite is needed.

Daily Brief places the briefing before private-source intake and scheduling.
Empty queues, source coverage and historical details can be expanded. Mock Data
is still visible, but provenance notes no longer mark otherwise complete price
calculations partial. Missing prices, old data, processing failures and excluded
input coverage still produce their actual states. Existing saved briefs are not
rewritten; an explicit deterministic refresh creates a new snapshot.

Unmatched filing sections were labeled as language changes and assigned severity
from their entire word count. They are now informational filing baselines with
source links, shown separately from comparable changes and explicit contradictions.
Company filtering occurs before the diff limit. Original section/diff rows are
preserved. A missing prior section is not evidence that wording changed.

Narrative creation and optional AI extraction use compact disclosure panels;
saved narratives remain prominent. Company exposure tags wrap instead of hiding
their text. Consent and source-review controls remain intact.

## Verification and publication boundary

- 87 focused backend tests pass, including ownership, response/schema boundaries,
  data-state distinctions and the preceding replay, thesis and readiness work.
- 365 frontend tests and standalone TypeScript pass. Locked frontend production
  compilation and the backend derivative build pass without dependency changes.
- Fifteen owned-Chromium desktop/mobile observations pass: dashboard selection and
  value, explicit empty account, portfolio holdings, deterministic brief refresh,
  private-source expansion, baseline evidence, narrative controls and company tags.
  No page errors, server 5xx responses or horizontal overflow were observed. Initial
  hidden-duplicate and navigation-timing selector attempts are retained.
- Local backend/frontend/workers use 20261109-dashboard. Rollout preserves all
  database/asset fingerprints, settings, mounts, localhost ports and worker states.
  A quiesced backup and the preceding containers remain. Browser verification then
  explicitly created a new unreviewed deterministic brief; no AI permission was granted.
- Initial test-command, fixture, contract-manifest and layout-guard failures are
  retained locally. The manifest was regenerated from the owning backend schemas;
  existing guards and browser tests were updated for explicit disclosure opening.
- The source pass includes the preceding [analyst-workflow changes](analyst-workflows-2026-11-09.md).
  The separate local audit directory is output/milestones/dashboard-portfolio-20261109.
  Screenshots, private portfolio details, runtime inventories and backups are not
  part of publication. The existing checkout/index and unrelated work are preserved.
- Publication uses codex/portfolio-ui-20261109 from PR8's merged default-branch
  commit 6f97c6f6. The user requested a PR to approve; this pass does not merge it.

The [limitation ledger](../../../agent_capabilities_and_limitations.md) retains
actual-use, recovery, source/disclosure and public-deployment boundaries. Cleaner
presentation does not certify financial completeness or approve AI output.

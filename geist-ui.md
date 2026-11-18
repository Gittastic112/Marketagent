# Marketagent Geist UI notes

**Historical patch handoff.** The source was subsequently integrated in this checkout. Use the [current UI notes](docs/geist-ui.md) and the [UI and adapter worklist](docs/roadmaps/ui-adapter-worklist.md) for the current status. The original handoff follows.

Updated November 17, 2026, America/New_York.

The UI is implemented in source commit `8ac48e54c729cb819b6fbbdf9fde4db3accf4d7d`
on `codex/geist-ui`, based on the original installation's `f4010d2`.
Documentation and this handoff accompany that source in the consolidated patch.
The original checkout and running app have not received the change. The
[current-state evidence](docs/current-state.md#dated-validation) records the failed
application attempt and checks; the [installation gate](docs/limitations.md#geist-ui-installation)
owns outstanding limits.

## What changed

| Area | Implemented behavior | Source owner |
|---|---|---|
| Typography | Bundled Geist Sans and Geist Mono, tabular figures, local font requests | [Foundation](frontend/styles/foundation.css), [font license](frontend/public/fonts/OFL.txt) |
| Shell | Neutral surfaces, thin borders, blue accents, compact sidebar and route breadcrumbs | [Navigation styles](frontend/styles/navigation.css), [sidebar](frontend/components/sidebar.tsx), [topbar](frontend/components/topbar.tsx) |
| Controls | Monochrome primary actions, secondary/disabled states, tighter forms and cards | [Shared styles](frontend/styles/components.css), [button](frontend/components/ui/button.tsx) |
| Theme | Light/dark selection stored as `marketagent:theme`, cross-tab preference sync, usable controls if storage is unavailable | [Theme switch](frontend/components/theme-switch.tsx), [helpers](frontend/lib/workspace-chrome.ts) |
| Search | Cmd/Ctrl+K opens `/search`; typing fields and active modal navigation retain their keys | [Topbar](frontend/components/topbar.tsx), [helper tests](frontend/lib/workspace-chrome.test.ts) |
| Valuation | Refined saved-model, scenario, peer, industry-mapping and version-history presentation | [Valuation styles](frontend/styles/valuation.css), [components](frontend/components/valuation/) |
| Older panels | Fixed light colors replaced with theme-aware tokens in financial review, source history, settings, events, macro and benchmark screens | [Style ownership](frontend/styles/README.md) |
| Production assets | Standalone image copies `public/`, including both fonts and their license | [Frontend Dockerfile](frontend/Dockerfile) |

## Relationship to the HTML prototype

The standalone HTML is a visual reference with illustrative data and browser-only
interactions. The application retains its existing routes, API contracts,
authentication, backend valuation calculations and review requirements.

Scenario and sensitivity outputs still use backend responses and saved input
identity. Unsaved edits do not become saved calculation evidence. Sources,
freshness, unavailable/error states and review status remain visible. Existing
exports and saved versions continue through their established application paths.
No mock prices, portfolio holdings, valuation math, new model types, provider
connections or database migrations were imported from the demo. This is a visual
adaptation, not a promise that every standalone-demo interaction is now a product
feature. GitHub publication remains deferred.

## Apply the consolidated source patch

Use a session with write access to the original project. The checked target is:

```text
/path/to/Marketagent
```

At inspection, that checkout was on `codex/review-research-recovery-20261116`
at `f4010d2`, with pre-existing edits only in `.codex/config.toml` and
`.env.example`. Preserve those edits. The UI patch does not touch either file.
The application check passed before and after the denied write; no UI changes
were left in the original checkout by that attempt.

The consolidated `Marketagent_Geist_UI.patch` replaces the earlier UI-only patch
and includes these documentation updates and binary font files. Apply it once.
If the check fails, inspect current changes before reconciling; do not force it,
reset the checkout, or discard user edits. If `8ac48e5` is already present, bring
over only the documentation follow-up instead of applying the complete UI again.

```bash
cd "/path/to/Marketagent"
geist_patch="/path/to/Marketagent_Geist_UI.patch"
git status --short --branch
git apply --check "$geist_patch" && git apply "$geist_patch"
git diff --check
git diff --stat
```

The patch changes working-tree files without staging or committing unrelated
work. Commit only the reviewed UI/documentation paths after validation. The
local branch also retains the original UI commit and the separate documentation
follow-up for Git-based integration when available.

## Verification before installation

Follow the [execution runbook](docs/execution-runbook.md#choose-the-right-environment).
Use Node 24 and the checked-in lockfile. In a writable, network-enabled project
environment, `npm --prefix frontend ci` restores the complete dependency tree.
Do not substitute fake Next.js modules, skip failing tests, or change dependency
versions to make an incomplete installation appear valid.

```bash
npm --prefix frontend test
npm --prefix frontend run typecheck
python3 -m unittest scripts.test_check_docs
python3 scripts/check_docs.py
git diff --check
```

Stop rollout if any required check fails. Build the frontend using the supported
Docker production path in [Operations](docs/operations.md#update-only-the-frontend).
Current test results live in [Current State](docs/current-state.md#dated-validation).
Missing-package failures are an incomplete verification gate, not passing tests.
The browser checks below have not been performed on this new UI.

## Browser acceptance

Use desktop 1440 x 900 and mobile 390 x 844 in both themes. The existing
[browser suite](frontend/e2e/accessibility-responsive.spec.ts) covers navigation,
semantics and overflow; it does not establish that every new dark-theme state has
been checked. Any isolated fixture work follows the existing data-scope rules;
do not create a new dataset as a side effect of this installation.

| Surface | Verify |
|---|---|
| Sign-in and navigation | Sign-in/out, breadcrumbs, all sidebar destinations, mobile open/close, Escape, focus return and active-route state |
| Fonts and theme | Both font URLs load, computed font family is Geist, theme survives navigation/reload, cross-tab updates work, contrast and initial paint are readable |
| Search and forms | Cmd/Ctrl+K opens search outside fields; inputs, selects, modals, focus rings and disabled actions retain expected behavior |
| Today and portfolio | Existing stored records render; headings, figures, notices and long tables fit the viewport |
| Financial review | Source links, units, dates, candidate/history panels and review controls remain readable; inspect without approving records merely for a visual test |
| Valuation | Saved model/version identity, assumption forms, scenarios, sensitivity, diagnostics and exports; do not save or alter live models just to prove presentation |
| Unavailable states | Readable loading, empty, partial, stale, error and not-configured states where available; use authorized isolated fixtures for failures |

Keep source/build results, fixture-browser results and installed-app observations
separate. A read-only observation of the old UI is not evidence for the new design.
Record the installed image ID, source revision, inspected viewports/themes and
remaining issues in [Current State](docs/current-state.md), then update the
[handoff](docs/HANDOFF.md) and [installation gate](docs/limitations.md#geist-ui-installation).

## Runtime handoff

The checked runtime override selects project
`market-intelligence-review-20261112-financial-history`, its existing external
network and preserved volumes. Its frontend image at inspection was
`market-intelligence-review-frontend:20261116-recovery-ui`; this is configuration
evidence, not a fresh container/image inspection because Docker access was denied.

Use the [frontend-only update procedure](docs/operations.md#update-only-the-frontend)
to build a new image, change only the frontend image selection, and replace only
that service. Reuse the established recovery set for this presentation change.
Retain the previous frontend image until the new one passes scoped verification.

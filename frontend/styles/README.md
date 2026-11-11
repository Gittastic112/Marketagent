# Styles

[app/globals.css](../app/globals.css) is the single application entry point.
Its imports define cascade order. Keep that order when changing ownership.

| File | Owns |
|---|---|
| [research.css](research.css) | Private source inbox, triage, and company research |
| [foundation.css](foundation.css) | Theme tokens, typography, and base elements |
| [workspace.css](workspace.css) | Initial shell, page headers, and metric cards |
| [data-health.css](data-health.css) | Provider health and runtime readiness |
| [components.css](components.css) | Panels, evidence, tables, forms, buttons, and badges |
| [briefing.css](briefing.css) | Daily brief, comparisons, citations, and score details |
| [navigation.css](navigation.css) | Shell refinements, navigation, shared layouts, and focus behavior |
| [company.css](company.css) | Company workspace, events, setup, and field layout |
| [valuation.css](valuation.css) | Drafts, industry mixes, source refresh, outputs, and their breakpoints |
| [feedback.css](feedback.css) | Route states, saved input basis, search, and loading feedback |
| [responsive.css](responsive.css) | Final mobile and tablet layout overrides |

Domain breakpoints stay beside their rules when already grouped there.
The final responsive imports intentionally override earlier shared rules.
The extraction preserves the previous selectors, declarations, and ordering;
it does not redesign the interface.

Source integrity tests follow local CSS imports through a
[test helper](../lib/test-support/read-styles.ts). Run frontend tests and typecheck
from the [execution runbook](../../docs/execution-runbook.md); shared style changes
also require the browser workflow.

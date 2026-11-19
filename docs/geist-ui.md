# Marketagent Geist UI

The installed research app uses bundled Geist fonts and the same theme and navigation across Today, company pages, valuation, portfolio review and Research Lab. The [user guide](user-guide.md) covers the controls. The [dated release evidence](current-state.md#dated-validation) records installed and hosted checks.

## What changed

| Surface | Behavior | Source |
|---|---|---|
| Type and theme | Bundled Geist Sans and Mono, tabular figures, neutral surfaces and persisted light/dark selection. A static head script reads the preference before rendering the body. | [Foundation](../frontend/styles/foundation.css), [layout](../frontend/app/layout.tsx), [font license](../frontend/public/fonts/OFL.txt) |
| Navigation | Compact sidebar, breadcrumbs without private record IDs, keyboard focus and mobile navigation. Advanced research links directly to Research Lab. | [Sidebar](../frontend/components/sidebar.tsx), [top bar](../frontend/components/topbar.tsx), [Advanced](../frontend/app/advanced/page.tsx) |
| Search | The top-bar search button and Cmd/Ctrl+K open the company and evidence palette. The sidebar opens the full evidence-search page. Escape restores focus. | [Palette](../frontend/components/research-command-palette.tsx), [shortcut tests](../frontend/lib/workspace-chrome.test.ts) |
| Valuation and review | Saved assumptions and scenarios, peer comparison, version history, evidence-linked Markdown memos and price/FX import review use the shared controls. | [Valuation](../frontend/components/valuation/), [portfolio evidence](../frontend/components/portfolio/portfolio-evidence-importer.tsx) |
| Today and price history | Today opens with portfolio context, then the brief and alerts. The company chart uses distinct shapes for a price move, dated source and private note. Inspect date and Key moments provide a keyboard path to point details. | [Today](../frontend/app/page.tsx), [price chart](../frontend/components/company-price-chart.tsx) |
| Research Lab | Explicit forms for allocation, simulation, reports, peers, source extraction and market evidence. Users can inspect capability messages, reopen an owned run and download its results. | [Research Lab](../frontend/app/research-lab/page.tsx), [adapter guide](adapters/README.md) |

The standalone HTML supplied the visual reference. Financial values and source status come from the application’s existing records and API responses. The [two example return datasets](adapters/examples/) are labeled Mock Data.

## Browser acceptance

| Workflow | What to verify on the combined build |
|---|---|
| Navigate and search | At 1440 × 900 and 390 × 844, open a route from the sidebar and from Advanced. Open the company/evidence dialog with the keyboard, move through results, press Escape and verify focus. Repeat from an input and with the mobile menu open. |
| Switch themes | Switch light/dark, navigate and reload. Verify first paint, cross-tab changes, readable focus and disabled states, both local font responses and no page overflow. |
| Company chart | Open a marked date with the pointer and with Inspect date, read both source dates, then open a pin from the thesis. Use disposable data for the save-and-reopen test. |
| Research Lab | Inspect capability states, run the labeled hypothetical dataset, switch tasks and reopen the saved run. Match export IDs and hashes. Opening the page alone should issue only reads. |
| Financial and portfolio review | Inspect source links, dates, units, candidate review and saved model identity. Verify supported, stale, empty and unavailable states. Exercise exact-file preview/apply only on disposable fixtures. |

The [browser suite](../frontend/e2e/accessibility-responsive.spec.ts), [search workflow](../frontend/e2e/search-workflows.spec.ts) and [dated verification](current-state.md#dated-validation) distinguish component checks from installed-app acceptance.

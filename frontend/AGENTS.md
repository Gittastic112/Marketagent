# Frontend Rules

Read the [root rules](../AGENTS.md). Next.js App Router owns route composition;
components own UI; backend services own financial calculations.

## Navigation and dependency boundaries

- app/page.tsx is the dashboard; app/companies/[id]/valuation contains the saved
  model workflow. app/actions/<domain>.ts owns server actions; app/actions.ts
  only re-exports them for compatibility. Shared action helpers stay server-only.
- lib/api/<domain>.ts contains domain contracts and browser endpoint helpers.
- lib/api/transport.ts owns browser HTTP, multipart, binary and parsing behavior.
- lib/api/contract.ts owns shared envelope types and ApiError identity.
- lib/api.ts only re-exports for compatibility. Do not add code there.
- Cross-domain contracts use import type. API domain modules must not import
  the facade, access process.env, or call fetch directly.
- lib/server-api.ts is the authenticated server-only client. Server components
  and server actions must use it, never cookie-blind browser helpers.
- app/api/backend/[...path]/route.ts is the authenticated same-origin proxy.
  Never forward raw session cookies or expose signing/provider keys to a client.
- Preserve await connection() before runtime settings/session reads in the server
  client. Do not reintroduce getServerSession in that path.
- lib/latest-request.ts and use-latest-resource.ts isolate responses by input
  scope. Reset/invalidate on identity/input changes; stale successes and failures
  must not overwrite the current UI.
- Reuse lib/formatting.ts, form-payloads.ts and existing validation helpers.

The [code map](../docs/code-map.md) identifies domain owners.
Keep API modules below 600 lines and do not create 800-line pages. Extract by
responsibility, not arbitrary line count. Do not rename routes as a cleanup.

## Request and data-state conventions

Use fetchApi/postApi for data-only results with thrown errors. Use
fetchApiResponse for metadata-aware GETs. The default compatibility api.get/post
returns the envelope and throws on HTTP failure; do not mix these return shapes.
Server equivalents live in server-api.ts. See [architecture](../docs/architecture.md).

Important data surfaces support Loading, Empty, Error, Stale, Partial,
Not Configured, Mock Data, and Success as applicable. Reuse DataStateNotices and
the components in components/ui/data-states.tsx. Catch failures without claiming
cached or mock data exists. Keep empty states actionable.

Saved output formatting/trust gates live in lib/valuation-output-state.ts.
They do not verify source facts. Never copy backend valuation math into cards.
Unsaved controls must not silently become saved-input calculation evidence.

## UI conventions

Dense, calm research UI: compact cards, tabular numerals, clear hierarchy,
source evidence, useful controls and visible freshness. Reuse existing tokens,
navigation, components and responsive patterns.

Avoid decorative gradients, gratuitous colors, huge empty cards, low contrast,
unlabelled charts, mock intelligence, and marketing layouts. Tables may scroll
inside bounded panels; pages must not overflow horizontally.

Charts need title, units, source, as-of date, tooltip, and truthful data states.
Avoid 3D charts and pie charts for complex exposure. Inputs need programmatic
labels; keyboard focus and mobile navigation must remain usable.

## Validation

From frontend: npm test and npm run typecheck.
Use the Docker production build for the supported Linux native dependency tree.
Use browser checks for changed workflows; compilation alone is not UI proof.

Utility tests use node:test with TypeScript stripping; imports they execute use
.ts extensions. Existing source-integrity tests are location-aware smoke guards,
not a substitute for behavioral tests. Update their owner paths during extraction
without dropping their assertions. api-boundaries.test.ts guards dependency flow,
module size, transport ownership, and the compatibility export surface.

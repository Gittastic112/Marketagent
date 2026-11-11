# Frontend Route Inventory

Source inventory reviewed: 2026-10-13. 50 App Router pages.

This indexes page entry points, not API handlers or browser-state certification.
Dynamic segments are placeholders, not portable database IDs. A source file's
presence does not prove loading, error, ownership or genuine-input correctness.
Use [Current State](current-state.md) for dated verification and the
[code map](code-map.md) for owning services and tests.

The [August state matrix](archive/assessments/route-state-inventory-2026-08-09.md)
is historical and is not a current all-route acceptance gate.
The [M09 matrix](archive/checkpoints/2026/m09-browser-validation-2026-10-11.md)
enumerates these 50 pages at desktop/mobile sizes using isolated Mock Data;
The [October 13 follow-up](archive/checkpoints/2026/m05-m09-workflows-2026-10-13.md)
reconciles controls/endpoints, adverse states, manual screenshot findings and
measured responsiveness. It separates full fixture coverage from normal-app reads
and genuine-input acceptance.

Regenerate the inventory from `rg --files frontend/app -g 'page.tsx'` after route
changes, then inspect behavior separately. The documentation checker verifies every
page source and the count. Auth/API routes are outside this page list.

| Route | Entry point |
|---|---|
| `/admin/damodaran` | [Page source](../frontend/app/admin/damodaran/page.tsx) |
| `/alerts/[id]` | [Page source](../frontend/app/alerts/[id]/page.tsx) |
| `/alerts` | [Page source](../frontend/app/alerts/page.tsx) |
| `/auth/signin` | [Page source](../frontend/app/auth/signin/page.tsx) |
| `/companies/[id]/decisions` | [Page source](../frontend/app/companies/[id]/decisions/page.tsx) |
| `/companies/[id]/evidence` | [Page source](../frontend/app/companies/[id]/evidence/page.tsx) |
| `/companies/[id]/filings` | [Page source](../frontend/app/companies/[id]/filings/page.tsx) |
| `/companies/[id]/fundamentals` | [Page source](../frontend/app/companies/[id]/fundamentals/page.tsx) |
| `/companies/[id]` | [Page source](../frontend/app/companies/[id]/page.tsx) |
| `/companies/[id]/setup` | [Page source](../frontend/app/companies/[id]/setup/page.tsx) |
| `/companies/[id]/thesis` | [Page source](../frontend/app/companies/[id]/thesis/page.tsx) |
| `/companies/[id]/valuation/[model_id]` | [Page source](../frontend/app/companies/[id]/valuation/[model_id]/page.tsx) |
| `/companies/[id]/valuation/draft` | [Page source](../frontend/app/companies/[id]/valuation/draft/page.tsx) |
| `/companies/[id]/valuation` | [Page source](../frontend/app/companies/[id]/valuation/page.tsx) |
| `/companies/[id]/valuation/peers` | [Page source](../frontend/app/companies/[id]/valuation/peers/page.tsx) |
| `/companies` | [Page source](../frontend/app/companies/page.tsx) |
| `/daily-brief` | [Page source](../frontend/app/daily-brief/page.tsx) |
| `/daily-brief/sources/[id]` | [Page source](../frontend/app/daily-brief/sources/[id]/page.tsx) |
| `/daily-brief/triage` | [Page source](../frontend/app/daily-brief/triage/page.tsx) |
| `/daily-brief/triage/reviews/[id]` | [Page source](../frontend/app/daily-brief/triage/reviews/[id]/page.tsx) |
| `/data-health` | [Page source](../frontend/app/data-health/page.tsx) |
| `/data` | [Page source](../frontend/app/data/page.tsx) |
| `/documents/[id]/ai` | [Page source](../frontend/app/documents/[id]/ai/page.tsx) |
| `/documents/[id]/event-evidence` | [Page source](../frontend/app/documents/[id]/event-evidence/page.tsx) |
| `/documents/[id]/financial-evidence` | [Page source](../frontend/app/documents/[id]/financial-evidence/page.tsx) |
| `/documents/[id]/sections` | [Page source](../frontend/app/documents/[id]/sections/page.tsx) |
| `/documents` | [Page source](../frontend/app/documents/page.tsx) |
| `/evaluations` | [Page source](../frontend/app/evaluations/page.tsx) |
| `/events/[id]/evidence-resolution` | [Page source](../frontend/app/events/[id]/evidence-resolution/page.tsx) |
| `/events` | [Page source](../frontend/app/events/page.tsx) |
| `/intelligence/review` | [Page source](../frontend/app/intelligence/review/page.tsx) |
| `/macro` | [Page source](../frontend/app/macro/page.tsx) |
| `/market-prices` | [Page source](../frontend/app/market-prices/page.tsx) |
| `/narratives` | [Page source](../frontend/app/narratives/page.tsx) |
| `/` | [Page source](../frontend/app/page.tsx) |
| `/portfolio/[id]` | [Page source](../frontend/app/portfolio/[id]/page.tsx) |
| `/portfolio/manage` | [Page source](../frontend/app/portfolio/manage/page.tsx) |
| `/portfolio` | [Page source](../frontend/app/portfolio/page.tsx) |
| `/portfolio/regime` | [Page source](../frontend/app/portfolio/regime/page.tsx) |
| `/research` | [Page source](../frontend/app/research/page.tsx) |
| `/research/sessions/[id]` | [Page source](../frontend/app/research/sessions/[id]/page.tsx) |
| `/research/sessions` | [Page source](../frontend/app/research/sessions/page.tsx) |
| `/search` | [Page source](../frontend/app/search/page.tsx) |
| `/settings` | [Page source](../frontend/app/settings/page.tsx) |
| `/social` | [Page source](../frontend/app/social/page.tsx) |
| `/sources` | [Page source](../frontend/app/sources/page.tsx) |
| `/thesis-notes/[id]` | [Page source](../frontend/app/thesis-notes/[id]/page.tsx) |
| `/thesis-notes` | [Page source](../frontend/app/thesis-notes/page.tsx) |
| `/valuation` | [Page source](../frontend/app/valuation/page.tsx) |
| `/valuation/quick` | [Page source](../frontend/app/valuation/quick/page.tsx) |

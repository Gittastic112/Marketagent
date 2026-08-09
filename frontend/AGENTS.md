# Frontend Operating Manual

# 10. Frontend Rules

## 10.1 Architecture

Frontend uses:

- Next.js
- app router
- reusable components
- centralized API client
- centralized types
- centralized formatting helpers

Target structure:

```text
frontend/
  app/
    dashboard/
    portfolio/
    companies/
      [ticker]/
    narratives/
    research/
    valuation/
    data-health/
    settings/

  components/
    layout/
    ui/
    finance/
    intelligence/
    charts/
    data/
    forms/
    tables/

  lib/
    api/
    formatting/
    validation/
    constants/
    scoring/

  types/
    api.ts
    company.ts
    portfolio.ts
    valuation.ts
    score.ts
    narrative.ts
    research.ts
    ingestion.ts
```

Do not create 800-line page files. If a page grows too large, extract components.

## 10.2 UI design principle

Use dense, calm, professional dashboard design.

Avoid:

- decorative gradients
- huge empty cards
- too many colors
- unlabelled charts
- low contrast text
- mock intelligence
- marketing-style UI
- random visual complexity

Prefer:

- compact layout
- clear active navigation state
- tabular numerals
- consistent card styles
- clear hierarchy
- evidence drawers
- data freshness badges
- loading/error/empty/stale states

## 10.3 Required data states

Every major data component should support:

- Loading
- Empty
- Error
- Stale
- Partial
- Not Configured
- Mock Data
- Success

Required components:

```text
EmptyState
ErrorState
LoadingState
StaleDataBanner
MockDataBadge
NotConfiguredState
PartialDataNotice
DataFreshnessIndicator
```

## 10.4 Empty states must be actionable

Bad:

```text
No active alerts.
```

Good:

```text
No active alerts.
Run ingestion or add companies to generate alerts.
[Run Ingestion] [Add Company]
```

Bad:

```text
0 companies
```

Good:

```text
No tracked companies yet.
Add a company or import a watchlist.
[Add Company] [Import Watchlist]
```

## 10.5 Chart rules

Every chart must show:

- title
- units
- source
- last updated
- tooltip
- loading state
- empty state
- error state
- stale state

Avoid:

- decorative charts
- pie charts for complex exposure
- 3D charts
- charts without units
- charts without timestamps

---

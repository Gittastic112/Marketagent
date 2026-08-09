# Route Inventory

**Updated:** 2026-08-09

This table tracks the implementation of standard data states across all frontend routes, as required by Stage 2.

| Route | Status | Loading | Empty | Error | Stale | Partial | Mock |
|---|---|---|---|---|---|---|---|
| `/admin/damodaran` | Built | Yes | No | Yes | No | No | No |
| `/alerts/[id]` | Built | No | No | Yes | Yes | Yes | No |
| `/alerts` | Built | No | Yes | Yes | Yes | Yes | No |
| `/auth/signin` | Built | No | No | No | No | No | No |
| `/companies/[id]/decisions` | Built | No | Yes | No | No | Yes | No |
| `/companies/[id]/evidence` | Built | No | Yes | No | No | No | No |
| `/companies/[id]/filings` | Built | No | Yes | Yes | No | No | No |
| `/companies/[id]/fundamentals` | Built | No | No | No | No | Yes | No |
| `/companies/[id]` | Built | No | Yes | Yes | Yes | Yes | Yes |
| `/companies/[id]/setup` | Built | No | No | No | No | No | No |
| `/companies/[id]/thesis` | Built | No | Yes | No | No | Yes | No |
| `/companies/[id]/valuation/[model_id]` | Built | No | No | No | Yes | No | Yes |
| `/companies/[id]/valuation/draft` | Built | No | No | No | No | No | No |
| `/companies/[id]/valuation` | Built | No | Yes | No | No | No | No |
| `/companies` | Built | No | Yes | Yes | Yes | No | Yes |
| `/daily-brief` | Partial | No | Yes | Yes | Yes | Yes | No |
| `/data-health` | Built | No | Yes | Yes | Yes | Yes | No |
| `/data` | Built | No | No | No | Yes | No | Yes |
| `/documents/[id]/ai` | Built | No | Yes | Yes | Yes | Yes | No |
| `/documents/[id]/event-evidence` | Built | No | No | Yes | Yes | Yes | No |
| `/documents/[id]/financial-evidence` | Built | No | No | Yes | Yes | Yes | No |
| `/documents/[id]/sections` | Built | No | Yes | Yes | Yes | Yes | No |
| `/documents` | Built | No | Yes | Yes | Yes | Yes | No |
| `/events/[id]/evidence-resolution` | Built | No | Yes | Yes | Yes | Yes | No |
| `/events` | Built | No | Yes | Yes | Yes | Yes | No |
| `/intelligence/review` | Built | No | Yes | No | Yes | Yes | No |
| `/macro` | Built | No | Yes | Yes | Yes | Yes | No |
| `/market-prices` | Built | No | Yes | Yes | Yes | Yes | No |
| `/narratives` | Built | No | Yes | Yes | Yes | Yes | Yes |
| `/` | Built | Yes | Yes | Yes | Yes | Yes | Yes |
| `/portfolio/[id]` | Built | No | Yes | Yes | Yes | No | No |
| `/portfolio/manage` | Built | No | Yes | Yes | Yes | Yes | No |
| `/portfolio` | Built | No | Yes | Yes | Yes | Yes | Yes |
| `/portfolio/regime` | Built | No | No | Yes | Yes | Yes | Yes |
| `/research` | Built | No | Yes | Yes | Yes | Yes | No |
| `/research/sessions/[id]` | Built | No | Yes | Yes | No | No | No |
| `/research/sessions` | Built | No | Yes | Yes | No | No | No |
| `/search` | Built | Yes | Yes | No | Yes | Yes | No |
| `/settings` | Built | No | No | Yes | Yes | Yes | No |
| `/social` | Built | No | Yes | Yes | Yes | Yes | No |
| `/sources` | Built | No | Yes | Yes | Yes | Yes | No |
| `/thesis-notes/[id]` | Built | No | Yes | Yes | Yes | Yes | No |
| `/thesis-notes` | Built | No | Yes | Yes | Yes | Yes | No |
| `/valuation` | Built | No | Yes | Yes | Yes | No | Yes |
| `/valuation/quick` | Built | No | No | Yes | Yes | No | Yes |

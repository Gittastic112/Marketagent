# Authenticated 20-Route Matrix Checkpoint

**Date:** 2026-08-25

## Scope

The current production frontend artifact was tested against an isolated E2E
backend and tmpfs PostgreSQL database at migration head `i0i0i0i0i0i0`.
Disposable local-auth credentials were supplied directly to the isolated
runtime. The protected project `.env` was not read.

The matrix covered these 20 routes at 1440 by 900 and 390 by 844:

1. Dashboard
2. Daily Brief
3. Alerts
4. Portfolio
5. Portfolio Manage
6. Market Regime
7. Companies
8. Research
9. Narratives
10. Events
11. Contradictions
12. Macro
13. Valuation
14. Documents
15. Data Management
16. Data Health
17. Sources
18. Damodaran Admin
19. Settings
20. Search

Each route passed:

- authenticated rendering;
- React server-stream completion;
- the 15-second route-ready budget;
- rejection of 5xx, application, and authentication errors;
- desktop and mobile horizontal-overflow checks;
- semantic names for interactive controls and labels for visible form fields;
- image alternative-text checks;
- body, title, panel-heading, and control typography minimums;
- keyboard focus entry; and
- full-page desktop and mobile screenshot capture.

## Extra Task

The mobile navigation test passed keyboard open and close, Escape dismissal,
and focus restoration to the navigation trigger.

## Command and Result

```text
frontend/node_modules/.bin/playwright test \
  --config frontend/playwright.config.ts \
  accessibility-responsive.spec.ts

2 passed (1.2m)
core route matrix: 55.0s
mobile navigation focus: 2.6s
```

## Runtime Note

Docker Hub timed out twice while resolving `node:24-slim`. The run therefore
used a temporary local image made from the healthy current frontend container,
plus the locally built E2E backend image. Both readiness endpoints were green
before Playwright started. This avoided external registry dependence without
changing application code.

Post-run inspection of the normal stack found that the scheduler container was
restarting because its older image could not locate database revision
`i0i0i0i0i0i0`. Only the scheduler image and container were rebuilt from current
source, using `/dev/null` as the Compose environment file. The healthy backend,
frontend, and database containers were not recreated. The scheduler then stayed
up and logged deterministic startup with a 60-second interval.

## Boundary

The E2E seed contains disposable reference records. This checkpoint proves
route, authentication, responsive, accessibility, and error-state integrity. It
does not prove genuine portfolio performance inputs, company financial facts,
or reviewed valuation assumptions. The genuine-input portfolio smoke remains
open until its read-only readiness audit reports `ready`.

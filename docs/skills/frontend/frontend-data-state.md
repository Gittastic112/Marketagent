# Frontend Data State Skill

## Purpose

Keep frontend pages honest about backend capability, source freshness, and missing data.

## When to use

- Building or auditing a frontend page.
- Wiring a component to backend data.
- Displaying provider, valuation, alert, financial, or research outputs.
- Replacing mock data.

## When NOT to use

- Backend-only changes.
- Static copy edits unrelated to data state.

## Prerequisites

- Inspect the page, components, API client, types, and relevant backend route.
- Check whether data is live, partial, mock, stale, not configured, or absent.

## Inputs

- API response and metadata.
- Frontend types.
- Existing UI components.
- Current backend capability.

## Outputs

- UI that shows loading, empty, error, stale, partial, mock, not-configured, and success states.
- No unsupported claims.
- Updated tests if a utility/client behavior changes.

## Workflow

1. Verify the backend route exists.
2. Use the owning domain under `frontend/lib/api/`, shared transport/envelopes and
   existing helpers. `frontend/lib/api.ts` is compatibility-only.
   Browser writes, including multipart uploads, must use the same-origin `/api/backend` proxy path. Server-rendered reads/actions must use the signed-identity server helper, never forward raw session cookies to FastAPI.
3. Reuse existing UI/data-state components.
4. Display source, freshness, warnings, and confidence where relevant.
5. If backend support is missing, show not available/not configured rather than fake data.
6. Run frontend typecheck or focused tests when available.
7. For financial coverage, show normalized count, trust-ready count, conflicts, and the exact periods needing action.
8. For auth configuration, expose only boolean readiness and missing variable names; disable sign-in while readiness is unknown or incomplete.
9. Filter provider controls by capability. RSS forms list active RSS sources;
   SEC forms list only CIK-backed eligible companies and allow server-side SEC
   source resolution.
10. Use metadata/summary endpoints for lists and pickers when detail records can
    contain large filing text or binary-adjacent payloads. Fetch the full body
    only in the detail workflow that needs it.
11. Server-rendered authenticated reads must cross the Next.js dynamic request
    boundary before reading runtime auth/API configuration. Transport and auth
    failures are unavailable states, not stale-data fallbacks.
12. Label lexical or AI-generated evidence matches as candidates. Selecting a
    candidate must not imply validation, approval, or semantic support.
13. Search results must show record type, claim type, shared/private scope,
    review state, mock state, source timestamp, and an unavailable state. Keep
    private excerpts bounded and provide a stable destination link.

## Acceptance criteria

- No page presents mock data as real.
- Empty states are actionable.
- Errors do not look like successful data.
- Valuation and intelligence outputs show assumptions/source context.
- Multipart requests do not set `Content-Type` manually and do not bypass the authenticated proxy.
- A successful normalized snapshot is not labeled valuation-ready when currency confidence or freshness is unresolved.
- Candidate, validated, reviewed, stale, mock, and unavailable states remain visually distinct.
- Shared, private, user-authored, and reviewed-AI results remain visibly distinct.

## Common mistakes

- Hardcoding dashboard numbers.
- Ignoring `ApiResponse.meta`.
- Adding cards without source/freshness labels.
- Creating a new UX pattern when existing components fit.

## Do not do

- Do not create landing-page style UI for operational tools.
- Do not hide missing providers behind polished visuals.
- Do not imply India/US provider coverage exists where the backend says manual-only or not configured.

## Related skills

- `backend-api-change`
- `market-intelligence-workflow`
- `valuation-workflow`

## References

- `docs/00-current-state.md`
- `docs/02-architecture.md`
- [Domain clients](../../../frontend/lib/api/)
- `frontend/lib/server-api.ts`
- `frontend/lib/data-state-meta.ts`

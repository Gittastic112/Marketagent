---
name: security-review
description: Use when a Market Intelligence App task touches external inputs, files, URLs, provider APIs, AI calls, secrets, auth, broker integrations, exports, proxy routes, or public deployment.
---

# Security Review

## Purpose

Run the project security checklist before changing risky surfaces. The canonical project workflow is `docs/skills/security/security-review.md`.

## When to use

- External APIs, SEC/RSS/provider ingestion, user-provided URLs, uploads, CSV import/export, AI calls, auth, broker integrations, proxy routes, or deployment.
- Any feature touches private portfolio, thesis, valuation, or source data.

## When NOT to use

- Pure copy edits with no behavior or data-flow change.

## Prerequisites

- Read `docs/06-security-threat-model.md`.
- If the task is in this repository, also read `docs/skills/security/security-review.md`.

## Inputs

- Changed files.
- User-controlled inputs.
- Secrets or credentials involved.
- External provider or AI calls.

## Outputs

- Security risks and required mitigations.
- Tests or manual checks.
- Threat-model updates when security assumptions change.

## Workflow

1. Check secrets and environment handling.
2. Check untrusted input rendering.
3. Check URL fetching and SSRF risk.
4. Check CSV/spreadsheet injection.
5. Check API errors/logs for secret leakage.
6. Check AI data sharing and provenance.
7. Check broker/auth/deployment boundaries.
8. Verify tests avoid live external APIs.
9. For uploads, verify size/type limits, hashes, duplicate handling, temporary-file cleanup, safe errors, and processing runs.
10. For readiness/diagnostic routes, verify they return state only and never secret values.
11. For generated diff markup, escape every source token and parse only generator-owned semantics into React text. Do not use `dangerouslySetInnerHTML`, including for legacy rows.

## Acceptance criteria

- No secrets are exposed to frontend or committed files.
- User-controlled URLs cannot fetch internal resources.
- Imported text is not rendered as trusted HTML.
- Private portfolio/thesis/valuation data is not sent externally without explicit design and audit trail.
- Public deployment remains blocked until production identity, authorization,
  and deployment security exist; local credential auth is not sufficient.
- Upload provenance never stores temporary paths, and auth readiness never returns credential values.
- Imported filing text cannot inject markup through diff or evidence rendering.

## Common mistakes

- Treating local-first as no security needed.
- Logging provider keys.
- Rendering RSS/AI/markdown as raw HTML.
- Storing broker passwords.

## Do not do

- Do not recommend `sudo chmod 666 /var/run/docker.sock`.
- Do not expose the app publicly without production identity/authorization,
  HTTPS, CSRF/CORS review, rate limits, and secret management.
- Do not call live external APIs in automated tests.

## Related skills

- `docs/skills/data-ingestion/data-ingestion-workflow.md`
- `docs/skills/backend/backend-api-change.md`
- `docs/skills/frontend/frontend-data-state.md`
- `docs/skills/operations/local-operations.md`

## References

- `docs/06-security-threat-model.md`
- `docs/skills/security/security-review.md`

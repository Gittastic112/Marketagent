# Security Review Skill

## Purpose

Review security risks for local-first investment research features.

## When to use

- External APIs, RSS, SEC, manual URLs, CSV/import/export, AI calls, auth, broker integrations, uploads, proxy routes, secrets, or deployment.
- Any feature touches private portfolio, thesis, valuation, or source data.

## When NOT to use

- Pure wording edits with no behavior change.

## Prerequisites

- Read `docs/security.md`.
- Inspect permitted config declarations, routes, input paths and sanitized logs.
  Respect denied secret-file paths, including examples if the session blocks them;
  verify configuration state without reading credential values.

## Inputs

- Changed files.
- Data sources.
- Secrets/credentials involved.
- User-controlled inputs.

## Outputs

- Security risk list.
- Required mitigations.
- Tests or manual checks.
- Documentation updates if threat model changes.

## Workflow

1. Check secrets and environment handling.
2. Check untrusted input rendering.
3. Check URL fetching and SSRF risk.
4. Check CSV/spreadsheet injection.
5. Check API errors/logs for secret leakage.
6. Check AI data sharing and provenance.
7. Check broker/auth/deployment boundaries.
8. Verify tests avoid live external APIs.
9. For upload routes, verify size/type limits, content hashing, duplicate handling, temporary-file cleanup, safe errors, and processing-run persistence.
10. For readiness endpoints, verify responses contain configuration state only, never environment values, and are not cached.
11. If generated diff markup is stored, HTML-escape every source token and parse only generator-owned semantics into React text. Do not use `dangerouslySetInnerHTML`, including for legacy rows.
12. For AI citation assistance, resolve the owned AI output first, accept only
    its declared source markers, scan stored text locally with finite limits,
    return bounded exact spans, and keep selection separate from validation and
    approval. Manual edits invalidate suggested offsets.
13. For server-rendered auth, decode supported standard, secure, or chunked
    session cookies at the request boundary and sign only the internal identity.
    Never forward or log the browser session cookie.
14. For unified research search, preserve every model's shared/private boundary,
    filter private rows by authenticated owner, bound excerpts, exclude generic
    assistant-message indexing, and admit AI output only after successful,
    approved, reviewed, and unblocked state.
15. Check browser mutations for same-origin enforcement, bounded bodies and safe
    forwarded headers. Check download/DNS/redirect and parser resource bounds at
    the actual client being changed; one safe client does not certify all providers.
16. Preserve private source/receipt ownership, append-only decisions and evidence
    hash/version conflicts. A matching quote proves text identity, not semantic
    truth; an analyst receipt does not approve AI output or numerical assumptions.

## Acceptance criteria

- No secrets in frontend or source control.
- User-controlled URLs cannot fetch internal resources.
- Imported text is not rendered as trusted HTML.
- Private portfolio/thesis/valuation data is not sent externally without explicit design and audit trail.
- Public deployment remains blocked until auth/security design exists.
- Uploaded workbooks do not leave persistent temporary paths or return parser stack traces.
- Auth readiness names missing variables without exposing their values.
- Filing/RSS/AI text cannot inject markup through diff, excerpt, or evidence rendering.
- Evidence suggestions cannot expose undeclared sources or mutate review state.
- Search cannot expose another user's private research or surface pending,
  blocked, failed, or unreviewed AI output.

## Common mistakes

- Treating local-first as no security needed.
- Logging provider keys.
- Rendering RSS/AI/markdown as raw HTML.
- Storing broker passwords.
- Returning secret values from diagnostic/readiness routes.
- Persisting temporary upload paths as document provenance.

## Do not do

- Do not recommend `sudo chmod 666 /var/run/docker.sock`.
- Do not expose the app publicly without auth, HTTPS, CORS review, rate limits, and secret management.
- Do not use live external APIs in automated tests.

## Related skills

- `data-ingestion-workflow`
- `backend-api-change`
- `frontend-data-state`
- `local-operations`

## References

- `docs/security.md`
- `skills/security-review/SKILL.md`

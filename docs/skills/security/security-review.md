# Security Review Skill

## Purpose

Review security risks for local-first investment research features.

## When to use

- External APIs, RSS, SEC, manual URLs, CSV/import/export, AI calls, auth, broker integrations, uploads, proxy routes, secrets, or deployment.
- Any feature touches private portfolio, thesis, valuation, or source data.

## When NOT to use

- Pure wording edits with no behavior change.

## Prerequisites

- Read `docs/06-security-threat-model.md`.
- Inspect `.env.example`, config, logs, routes, and user-input paths.

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

## Acceptance criteria

- No secrets in frontend or source control.
- User-controlled URLs cannot fetch internal resources.
- Imported text is not rendered as trusted HTML.
- Private portfolio/thesis/valuation data is not sent externally without explicit design and audit trail.
- Public deployment remains blocked until auth/security design exists.
- Uploaded workbooks do not leave persistent temporary paths or return parser stack traces.
- Auth readiness names missing variables without exposing their values.
- Filing/RSS/AI text cannot inject markup through diff, excerpt, or evidence rendering.

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

- `docs/06-security-threat-model.md`
- `skills/security-review/SKILL.md`

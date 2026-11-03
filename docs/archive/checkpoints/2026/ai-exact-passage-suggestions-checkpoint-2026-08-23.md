# AI Exact-Passage Suggestions Checkpoint

**Date:** 2026-08-23

## Delivered Boundary

- Owner-scoped `GET /ai-outputs/{id}/citations/suggestions` endpoint.
- Local-only matching against declared stored `raw_document` source markers.
- Claim extraction, bounded source segmentation, exact quote offsets, and
  numeric-aware lexical ranking.
- Up to five bounded candidates per source with confidence, matched-term
  coverage, source links, and limitations.
- Explicit states for undeclared markers, unsupported sources, missing text,
  missing claim text, and no relevant candidate.
- On-demand review UI with loading, unavailable, mock-context, and candidate
  states.
- One-click draft population that preserves exact offsets. Manual edits clear
  those offsets so the existing validator resolves the edited quote again.
- No automatic validation, review-status mutation, approval, external AI call,
  or thesis/valuation write.

## Validation

- Backend changed-file compile: passed.
- Frontend TypeScript: passed.
- Frontend tests: 122 passed.
- Project skill validation: 11 passed.
- Documentation validation: 62 active Markdown files and 279 local links passed;
  all four documentation-checker unit tests passed.
- Explicit skill frontmatter and `agents/openai.yaml` parsed successfully with
  implicit invocation enabled. The bundled Python quick validator itself could
  not start because PyYAML is absent, so equivalent schema checks were run with
  the system YAML parser.
- Focused backend tests were added for claim extraction, segmentation, numeric
  ranking, exact-offset validation, explicit unavailable states, and ownership.
  They remain runtime-pending because the agent host has no pytest and cannot
  access the Docker socket.
- The host production build remains environment-blocked by protected
  `frontend/.env.local` metadata and the non-writable Next SWC cache. TypeScript
  and frontend tests are green; no build pass is claimed.

## Runtime Command

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_ai_citation_suggestions.py tests/test_ai_citations.py
```

Passing this test proves exact storage and validation mechanics. It does not
prove semantic entailment, provider citation completeness, or investment
correctness.

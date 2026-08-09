# Documentation Architecture Checkpoint

**Date:** 2026-08-08

**Status:** shipped and validated

## Problem

Active documentation had grown to nearly 49,000 lines including archive
material. Current truth, dated checkpoints, cumulative handoffs, implementation
history, provider research, and multi-thousand-line plans were mixed together.
Agents had to read contradictory counts and stale next-task statements before
touching code.

## Delivered

1. Reduced the active `/docs` layer to 31 Markdown files and 3,489 lines,
   including the project skill library.
2. Replaced cumulative current-state, handoff, architecture, schema, runbook,
   and capability files with concise present-tense documents.
3. Replaced multiple active roadmaps with `product-roadmap.md` and
   `feature-register.md`.
4. Moved dated checkpoints, previous handoffs, old assessments, superseded
   product/provider/valuation plans, and research into categorized archives.
5. Reconciled root `README.md`, `AGENTS.md`, frontend docs, valuation docs,
   security docs, ingestion docs, local-development references, and project skills.
6. Corrected the stale APSEZ status: FY2023-FY2025 is promoted, reconciled, and
   certified; the representative US/India gate passes.
7. Documented the remaining hardcoded assumption-methodology fallback as
   technical debt instead of implying every default is source-backed.
8. Added `scripts/check_docs.py` with unit coverage for active Markdown links,
   inline Markdown paths, retired active-plan references, archive exclusion, and
   macOS path normalization.

## Archive Layout

- `archive/checkpoints/2026/`: dated delivery evidence
- `archive/handoffs/`: superseded cumulative handoffs
- `archive/assessments/`: old current-state and architecture snapshots
- `archive/plans/`: superseded product, provider, valuation, and platform plans
- `archive/research/`: dated provider/API research
- `archive/agent-instructions/`: old prompts and instruction drafts
- `archive/needs-review/`: material never promoted to current truth

## Validation

- Documentation checker: 60 active Markdown files and 271 local links pass.
- Documentation checker unit tests: 4 pass.
- Project skill validator: 11 skills pass.
- Active stale-path and stale-baseline searches return no unresolved current hits.
- Product test baseline was not rerun because this was documentation/tooling-only
  work and Docker Desktop was unavailable. The immediately preceding baseline is
  483 backend tests, 90 frontend tests, TypeScript, and production build passing.

## Maintenance Rule

Replace current status in place. Archive detailed evidence. Do not append another
phase history to the handoff or create another competing active roadmap.

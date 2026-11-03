# Documentation Workflow Skill

## Purpose

Audit, clean, archive, and relink project documentation without losing useful context.

## When to use

- Updating handoff, roadmap, architecture, or agent instructions.
- Consolidating duplicated docs.
- Moving stale docs into archive.
- Fixing doc/code mismatches.

## When NOT to use

- Product feature implementation.
- One-line typo fixes that do not affect meaning.

## Prerequisites

- Read `docs/README.md`, `docs/HANDOFF.md`, and `docs/00-current-state.md`.
- Check `git status --short` to avoid overwriting unrelated work.

## Inputs

- Existing docs.
- User request.
- Relevant code/tests when docs make capability claims.

## Outputs

- Updated canonical docs.
- Archived stale docs, not deleted.
- Updated links and doc index.
- Short report of what changed and what remains needs-review.

## Workflow

1. Inventory docs with `rg --files docs -g '*.md'`, including archive indexes;
   also inspect root/nested instructions, frontend guidance and knowledge-base docs.
2. Classify each doc: current, reference, roadmap, archive, needs-review, duplicate.
3. Preserve important context.
4. Move dated evidence into `docs/archive/checkpoints/YYYY/`, superseded plans
   into `docs/archive/plans/`, and uncertain material into `docs/archive/needs-review/`.
5. Keep the roadmap and feature register as product planning owners. An explicitly
   requested batch plan owns assignments/acceptance, not a competing product status.
6. Update `docs/README.md` and any direct references.
7. Run `python3 scripts/check_docs.py`.
8. Scan active docs for old paths and stale claims.
9. Record validation scope precisely: compile, unit, container, browser, and
   manual checks are different evidence. Keep a full-baseline count until the
   full baseline is actually rerun.
10. For command examples, verify whether paths are repository-relative or
    container-working-directory-relative. Correct operational commands in every
    affected current doc. Preserve historical checkpoint commands as dated
    evidence; link the runbook rather than turning old receipts into new instructions.
11. During parallel work, edit only the assigned evidence directory. Propose shared
    doc changes there; the coordinator reconciles current references after integration.
12. If a runtime is unavailable, record the exact blocked check and any narrower
    checks actually run. Do not refresh product verification dates or weaken a
    validator to obtain a pass. Existing archives/source originals stay preserved.

## Acceptance criteria

- Current docs are easy to find from `docs/README.md`.
- Archived docs are clearly labeled as not current guidance.
- No active Markdown links are broken.
- No stale moved-file references remain in active docs.
- Current status and handoff files replace old content instead of accumulating history.
- Checkpoints state pending runtime commands without presenting them as passed.
- Copied commands resolve from the working directory stated in the doc.

## Common mistakes

- Deleting stale docs instead of archiving.
- Updating an index without moving contradictory docs.
- Leaving absolute `file://` links.
- Treating archived prompts as current instructions.

## Do not do

- Do not rewrite all docs casually.
- Do not invent capabilities to make docs look complete.
- Do not bury known limitations.

## Related skills

- `architecture-overview`
- `local-operations`

## References

- `docs/README.md`
- `docs/HANDOFF.md`
- `docs/agent_capabilities_and_limitations.md`
- `docs/archive/needs-review/README.md`

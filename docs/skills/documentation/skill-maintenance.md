# Skill Maintenance Skill

## Purpose

Create, update, archive, and validate project skills without turning them into bloated docs.

## When to use

- Adding a new project skill.
- Updating a project skill after architecture or workflow changes.
- Auditing skill quality or missing required sections.
- Promoting a project skill into an installed `skills/<name>/SKILL.md` folder.

## When NOT to use

- Ordinary docs cleanup that does not change reusable workflows.
- One-off implementation notes that belong in a dated archived checkpoint.

## Prerequisites

- Read `docs/skills/README.md`.
- Read `docs/skills/skill-system-audit.md`.
- Inspect current docs/code before adding a skill.

## Inputs

- Repeated task or failure mode.
- Source docs where the workflow is currently hidden.
- Existing related skills.

## Outputs

- Concise skill file under `docs/skills/<category>/`.
- Updated `docs/skills/README.md`.
- Updated `docs/skills/skill-system-audit.md` when adding, merging, or archiving skills.
- Passing skill validation.

## Workflow

1. Confirm the workflow is reusable, not a one-off.
2. Check for an existing skill that should be updated instead.
3. Keep hard rules in `AGENTS.md`; keep reusable workflow in `docs/skills`.
4. Use the standard sections from `docs/skills/README.md`.
5. Keep detailed domain facts in canonical docs and link them.
6. Update the skill index and audit.
7. Run `python3 scripts/validate_project_skills.py`.
8. Run docs link and stale-reference checks.

## Acceptance criteria

- Skill has all required sections.
- Skill is concise and references canonical docs.
- Skill does not claim unverified capabilities.
- Skill index and audit are current.
- Validation script passes.

## Common mistakes

- Creating duplicate skills instead of updating related ones.
- Copying entire roadmap sections into a skill.
- Letting a skill drift from code reality.
- Making installed `skills/` folders for every project-specific doc skill before they are proven reusable.

## Do not do

- Do not add a skill for a one-off fix.
- Do not put implementation history in a skill.
- Do not delete stale skills without archiving or recording why.

## Related skills

- `documentation-workflow`
- `architecture-overview`
- `local-operations`

## References

- `docs/skills/README.md`
- `docs/skills/skill-system-audit.md`
- `skills/security-review/SKILL.md`

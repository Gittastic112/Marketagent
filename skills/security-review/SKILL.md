---
name: security-review
description: Review Market Intelligence App changes involving authentication, private research or portfolio data, uploads, URLs, imports/exports, provider or AI calls, proxy routes, secrets, or deployment. Use for explicit security reviews or when those trust boundaries change; skip pure copy and layout edits.
---

# Market Intelligence security review

This repository package routes to one canonical project workflow. When installed,
its metadata permits implicit invocation for matching tasks; explicit invocation
is also supported. A checked-in package alone does not establish installation.

## Workflow

1. Locate the Market Intelligence repository from its root AGENTS.md and docs map.
   If unavailable, report the missing project context; do not pretend this package
   contains a standalone copy of the project's threat model.
2. Read [the security workflow](../../docs/skills/security/security-review.md).
   Apply the sections relevant to the changed input/data/identity boundary, using
   [the threat model](../../docs/06-security-threat-model.md) for deeper context.
3. Inspect the changed routes, services, callers and tests. Preserve owner scoping,
   exact evidence and review/version gates. Treat sources and AI output as untrusted.
4. Use the [runbook](../../docs/08-execution-runbook.md) for verification. In an
   assigned batch respect [exclusive ownership](../../docs/workstreams/ownership.tsv)
   and request shared changes through the coordinator.
5. Report concrete findings with source location, consequence, remediation and
   validation evidence. Separate passed, failed, blocked and untested checks.

## Boundaries and output

Never read/print secrets, invent provider success, approve evidence implicitly,
store broker passwords, call live APIs from deterministic tests, or deploy publicly
as a side effect of a review. A clean scanner is not security certification.
Existing user authorization governs actions; this skill adds no blanket approval
step and does not authorize messaging, deployment or private-data transmission.

Return actionable findings and verification limits. Update the canonical workflow
when recurring guidance changes rather than expanding this entrypoint into a
second checklist. Keep invocation policy in [openai.yaml](agents/openai.yaml).

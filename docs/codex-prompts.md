# Codex Prompts

## Rule

Do not ask Codex to build the entire product at once.

Use small, specific prompts.

---

## Prompt 1: Docs pass

```text
Read README.md, AGENTS.md, and every file in /docs.

Do not write application code yet.

Improve the implementation docs:
- product-brief.md
- architecture.md
- roadmap.md
- local-development-plan.md
- scoring-framework.md
- database-schema.md
- data-sources.md

Keep the MVP local, Docker-based, and beginner-friendly.
```

---

## Prompt 2: Backend skeleton

```text
Create a minimal FastAPI backend.

Use PostgreSQL through the DATABASE_URL in .env.

Implement these models:
- Company
- Source
- RawDocument
- Event
- Alert
- ThesisNote

Use SQLAlchemy or SQLModel.
Add Alembic migrations.
Add pytest tests.
Do not implement external API ingestion yet.
```

---

## Prompt 3: Docker check

```text
Review docker-compose.yml and .env.example.

Make sure the backend can connect to the local PostgreSQL database running in Docker.

Do not change passwords unless necessary.
Explain any required terminal commands in plain English.
```

---

## Prompt 4: Manual CRUD

```text
Add API endpoints for:
- create company
- list companies
- get company
- create thesis note
- list thesis notes
- create raw document
- list raw documents
- create event
- list events
- create alert
- list alerts

Add tests for each endpoint.
```

---

## Prompt 5: Daily brief

```text
Implement a daily brief generator.

Inputs:
- Events
- Alerts
- RawDocuments
- ThesisNotes

Output:
- title
- summary
- top events
- why each matters
- source evidence
- credibility score
- novelty score
- impact score
- follow-up questions

Do not use LLMs yet.
Use rule-based logic.
```

---

## Prompt 6: Frontend

```text
Create a simple Next.js frontend.

Pages:
- Home
- Companies
- Company detail
- Raw documents
- Thesis notes
- Alerts
- Daily brief

Keep styling simple.
Connect to the FastAPI backend.
Do not add authentication.
```

---

## Prompt 7: SEC ingestion

```text
Implement SEC EDGAR filing metadata ingestion.

Requirements:
- support company CIK
- fetch recent filings
- store form type
- accession number
- filing date
- filing URL
- raw response payload

Add mocked tests.
Do not call the live API in tests.
```

---

## Prompt 8: Error explanation

```text
Explain this error in plain English.

Then suggest the smallest fix.

Do not rewrite unrelated files.

Error:
[paste error here]
```

---

## Prompt 9: Code review

```text
Review the current repo for:
- overengineering
- missing tests
- broken assumptions
- unclear docs
- beginner-hostile complexity

Do not add new features.
Return a prioritized fix list.
```

---

## Prompt 10: Safe refactor

```text
Refactor only the files needed for [specific issue].

Do not change public behavior.
Do not introduce new dependencies unless necessary.
Update tests if needed.
Explain what changed.
```

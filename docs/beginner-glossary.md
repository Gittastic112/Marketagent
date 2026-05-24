# Beginner Glossary

## Repo

A project folder that contains code, docs, settings, and version history.

---

## Git

A tool that tracks changes in your project.

It lets you save checkpoints and undo mistakes.

---

## GitHub

A website that stores your repo online.

Git is the tool.  
GitHub is the cloud service.

---

## VS Code

The code editor where you open and manage the project.

---

## Terminal

The place where you type commands.

Examples:

```bash
node -v
python3 --version
docker ps
```

---

## Bash / zsh

Command-line languages that the Terminal understands.

You do not need to deeply learn them at first.

---

## Node.js

A tool that runs JavaScript outside the browser.

Needed for frontend apps like Next.js.

---

## npm

Comes with Node.

Downloads and runs frontend packages.

Examples:

```bash
npm install
npm run dev
```

---

## Python

A programming language used for the backend, data pipelines, AI calls, and scripts.

---

## Backend

The server-side logic of the app.

For this project, the backend handles:

- companies
- documents
- events
- alerts
- scoring
- brief generation

---

## Frontend

The dashboard you see in the browser.

---

## API

A way for one program to talk to another.

Example:

- frontend talks to backend API
- backend talks to SEC API
- backend talks to OpenAI API

---

## API key

A secret password that lets your app use an external service.

Never hardcode it in code.

---

## Environment variable

A secret or setting stored outside code.

Usually stored in `.env`.

---

## Docker

A tool that runs software in isolated containers.

For this project, Docker runs PostgreSQL locally.

---

## PostgreSQL

A serious database.

Stores companies, documents, events, alerts, and thesis notes.

---

## pgAdmin

A browser interface for looking inside PostgreSQL.

---

## localhost

Your own computer acting like a website/server.

Examples:

```text
http://localhost:3000
http://localhost:8000
```

---

## Migration

A database change file.

It updates the database structure over time.

---

## Test

A check that confirms code works.

---

## CRUD

Create, Read, Update, Delete.

Basic app operations.

Example:

- create company
- view company
- edit company
- delete company

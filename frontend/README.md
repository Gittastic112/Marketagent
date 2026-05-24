# Frontend

This is a minimal Next.js dashboard for the local Market Intelligence Engine.

It reads from the FastAPI backend through:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Current scope

Built:

- overview metrics
- companies page
- raw documents page
- events page
- alerts page
- thesis notes page
- daily brief page

Not built yet:

- create/edit forms
- delete controls
- client-side filtering
- charts
- authentication
- external ingestion UI

## Local run

After a JavaScript package manager is available:

```bash
npm install
npm run dev
```

The backend should be running on `127.0.0.1:8000`.

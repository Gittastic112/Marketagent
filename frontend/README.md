# Frontend

This is a minimal Next.js dashboard for the local Market Intelligence Engine.

It reads from the FastAPI backend through:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Debug logs are enabled unless this is set:

```text
NEXT_PUBLIC_DEBUG_LOGS=false
```

## Current scope

Built:

- overview metrics
- companies page
- sources page
- raw documents page
- events page
- alerts page
- thesis notes page
- daily brief page
- saved daily brief history
- pasted RSS XML import
- pasted SEC filing metadata import
- rule-based event extraction from raw documents
- create forms for companies, sources, raw documents, events, alerts, and thesis notes
- edit controls for companies, sources, raw documents, events, alerts, and thesis notes
- delete controls for companies, sources, raw documents, events, alerts, and thesis notes
- debug console logs for browser mount, frontend API calls, create actions, and delete actions

Not built yet:

- client-side filtering
- charts
- authentication
- live external feed fetching
- live SEC EDGAR fetching

## Local run with Docker

From the project root:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:3000
```

This is the preferred local path because it does not require `npm` to be installed on the host machine.

## Local run without Docker

After a JavaScript package manager is available:

```bash
npm install
npm run dev
```

The backend should be running on `127.0.0.1:8000`.

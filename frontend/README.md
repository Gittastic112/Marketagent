# Frontend

This is a minimal Next.js dashboard for the local Market Intelligence Engine.

It reads from the FastAPI backend through:

```text
API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_BROWSER_API_BASE_URL=/api/backend
```

`API_BASE_URL` is used by server-side frontend code. Browser-side requests use
the same-origin `/api/backend` proxy so the browser does not need to resolve
Docker-only hostnames such as `backend`.

Debug logs are off by default. Enable them with:

```text
NEXT_PUBLIC_DEBUG_LOGS=true
```

## Current scope

Built:

- overview metrics
- companies page
- company detail page
- add-company ticker lookup for SEC title and CIK
- sources page
- raw documents page
- events page
- alerts page
- thesis notes page
- daily brief page
- saved daily brief history
- pasted RSS XML import
- RSS feed URL import
- RSS source active/inactive controls
- run-one and run-all-active RSS feed controls
- company aliases for source matching
- pasted SEC filing metadata import
- recent SEC filing metadata fetch for companies with CIKs
- company detail SEC picker for form type, filing year, exact filing, and
  optional text download
- rule-based event extraction from raw documents
- rule-based alert generation from high-priority events
- score explanations on events and alerts
- create forms for companies, sources, raw documents, events, alerts, and thesis notes
- edit controls for companies, sources, raw documents, events, alerts, and thesis notes
- delete controls for companies, sources, raw documents, events, alerts, and thesis notes
- inline delete errors when linked records prevent deletion
- SEC filing text download checkbox on SEC ingestion forms
- first-pass SEC filing text change events shown through the existing Events page
- optional frontend API/action debug logs when `NEXT_PUBLIC_DEBUG_LOGS=true`

Not built yet:

- client-side filtering
- charts
- authentication

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

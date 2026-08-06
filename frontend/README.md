# CodeScope React frontend

Vite + React + TypeScript UI for uploading projects and exploring architecture graphs.

## Stack

- React 18
- Vite
- TypeScript
- Tailwind CSS
- React Flow (`@xyflow/react`)
- Framer Motion
- React Router

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

Optional env:

```bash
# frontend/.env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Pages

- `/` — Landing
- `/projects` — Project list
- `/projects/new` — ZIP or GitHub ingest
- `/projects/:id` — Dashboard, languages, folder tree
- `/projects/:id/graph/:type` — Interactive graph + inspector

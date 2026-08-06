# CodeScope

Interactive codebase visualization — upload a ZIP or GitHub repo and explore architecture graphs.

## Two separate apps

```
codescope/
├── backend/     # Django + Django REST Framework
└── frontend/    # React (Vite + TypeScript)
```

| App | Path | Stack |
|---|---|---|
| Backend API | [`backend/`](backend/) | Django 5, DRF, Celery, Redis, PostgreSQL/SQLite, Neo4j, language parsers |
| Frontend UI | [`frontend/`](frontend/) | React 18, Vite, TypeScript, Tailwind, React Flow |

## Run locally

### 1. Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

Swagger: http://127.0.0.1:8000/api/docs/

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

### Docker (optional)

```bash
docker compose up --build
```

## What works now

- Create projects via API/UI
- ZIP upload or GitHub clone
- Background analysis pipeline (eager locally without Redis)
- File inventory + language detection
- Parsers for Python, JS, TS, Java, Go, C#, C++, PHP
- Folder tree + React Flow graphs
- Neo4j persistence when available (Postgres fallback for folder graphs)

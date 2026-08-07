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

## Deploy (Vercel + Render)

### Backend on Render

1. Push this repo to GitHub.
2. In [Render](https://render.com) → **New → Blueprint** → connect the repo.
3. Render reads [`render.yaml`](render.yaml) and creates:
   - **codescope-api** (Django web service)
   - **codescope-worker** (Celery worker for ZIP/GitHub analysis)
   - **codescope-db** (PostgreSQL)
   - **codescope-redis** (Redis for Celery)
4. After deploy, copy the API URL (e.g. `https://codescope-api.onrender.com`).
5. In the **codescope-api** service → **Environment**, set:
   - `CORS_ALLOWED_ORIGINS` = your Vercel frontend URL (e.g. `https://codescope.vercel.app`)
   - `CSRF_TRUSTED_ORIGINS` = same URL
   - Optional for Vercel preview URLs: `CORS_ALLOWED_ORIGIN_REGEXES` = `^https://.*\.vercel\.app$`

Health check: `GET /api/v1/health/` · API docs: `/api/docs/`

> **Note:** Render free-tier web services spin down after inactivity (cold starts ~30s). Uploaded project files live on ephemeral disk and are lost on redeploy.

### Frontend on Vercel

1. In [Vercel](https://vercel.com) → **Add New Project** → import the repo.
2. Set **Root Directory** to `frontend`.
3. Framework preset: **Vite** (auto-detected).
4. Add environment variable:
   - `VITE_API_BASE_URL` = `https://<your-render-api>.onrender.com/api/v1`
5. Deploy.

[`frontend/vercel.json`](frontend/vercel.json) handles SPA routing (React Router).

### Manual Render setup (without Blueprint)

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Build command | `./build.sh` |
| Start command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| Python version | 3.12 |

Add a separate **Background Worker** with start command: `celery -A config worker -l INFO`.

## What works now

- Create projects via API/UI
- ZIP upload or GitHub clone
- Background analysis pipeline (eager locally without Redis)
- File inventory + language detection
- Parsers for Python, JS, TS, Java, Go, C#, C++, PHP
- Folder tree + React Flow graphs
- Neo4j persistence when available (Postgres fallback for folder graphs)

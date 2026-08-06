# CodeScope Django + DRF backend

REST API for project ingest, analysis jobs, parsers, and graph queries.

## Stack

- Django 5
- Django REST Framework
- Celery + Redis (optional in local eager mode)
- PostgreSQL or SQLite
- Neo4j (optional; folder graphs fall back to Postgres)
- Tree-sitter / LibCST / language plugins under `apps/parsers`

## Setup

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
copy .env.example .env            # or cp .env.example .env
python manage.py migrate
python manage.py runserver 8000
```

API docs: http://127.0.0.1:8000/api/docs/

## Celery worker (production / Redis)

```bash
celery -A config worker -l INFO
```

When `DEBUG=True`, Celery runs tasks eagerly in-process so Redis is not required for local demos.

## Main endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health/` | Liveness |
| GET/POST | `/api/v1/projects/` | List / create |
| POST | `/api/v1/projects/{id}/ingest/zip/` | Upload ZIP |
| POST | `/api/v1/projects/{id}/ingest/github/` | Clone GitHub |
| GET | `/api/v1/projects/{id}/jobs/{job_id}/` | Job status |
| GET | `/api/v1/projects/{id}/files/tree/` | Folder tree |
| GET | `/api/v1/projects/{id}/graphs/{type}/` | Graph slice |
| GET | `/api/v1/plugins/` | Parser plugins |

## Layout

```
backend/
├── config/           # Django settings, URLs, Celery
├── apps/
│   ├── core/         # Health, languages, exceptions
│   ├── projects/     # Projects, files, ingest
│   ├── analysis/     # Jobs + pipeline
│   ├── graphs/       # Neo4j + graph API
│   └── parsers/      # Language plugins (Python, JS, TS, …)
├── manage.py
└── requirements.txt
```

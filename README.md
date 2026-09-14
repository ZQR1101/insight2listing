# Insight2Listing

Evidence-grounded market insight, product opportunity validation, and intelligent Listing workflows for Amazon US.

> Status: **in progress**. The first milestone implements the backend API and the data-import pipeline. The web UI, chat, insight generation, and Amazon integration are later phases.

## Current scope

- Amazon US first
- Workflow-first UI with chat as an assistant
- CSV, JSON, and XLSX import architecture
- Self-hosted first, hosted-ready
- BYOK model usage: users provide their own model API key
- GPT Image 2 planned for product image generation and editing
- MIT licensed source code

The initial test products are compression packing cubes, glass oil sprayers, and car trash cans. Amazon seller authorization and production SP-API integration are deferred to a later beta phase.

## Repository layout

- `apps/api` — FastAPI backend, data import pipeline, PostgreSQL models and migrations (initial milestone)
- `apps/web` — Next.js frontend (not yet implemented)
- `apps/worker` — background task worker (not yet implemented)
- `packages/*` — shared schemas, i18n, providers, rules, evals (not yet implemented)
- `outputs/` — product and technical baseline documents

## Documentation

- [中文详细产品与技术方案](outputs/Insight2Listing详细产品与技术方案.md)
- [English project guide](README.en.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Data and asset licensing](DATA_LICENSE.md)

## Local setup

### Prerequirements

- [uv](https://docs.astral.sh/uv/) for Python tooling
- Docker (for the local database)

### 1. Start the infrastructure

```powershell
Copy-Item .env.example .env
docker compose up -d postgres minio redis
```

The Postgres host port is `5050` by default so it does not collide with an
unrelated local Postgres. `DATABASE_URL` in `.env.example` points there.

### 2. Run the API

```bash
cd apps/api
uv sync
uv run alembic upgrade head     # apply migrations
uv run python run.py            # http://localhost:8000  (docs at /docs)
```

`run.py` (rather than `uvicorn app.main:app`) is used so the server runs on a
SelectorEventLoop on Windows, which the psycopg async driver requires.

### 3. Run tests, lint and typecheck

```bash
cd apps/api
uv run pytest                   # requires the Postgres container running
uv run ruff check src tests
uv run mypy src
```

Optional: run the whole stack (API + dependencies) in containers:

```bash
docker compose up --build api
```

The test suite provisions a dedicated `insight2listing_test` database from
`DATABASE_URL` and truncates tables between tests, so dev data is never touched.

### Security notes

Do not commit `.env` or any API key. Keys must stay on the backend and never
appear in browser code or logs (see `SECURITY.md`). Uploaded cells beginning
with spreadsheet-formula prefixes are escaped to prevent formula injection.

## License

Source code is released under the MIT License. Third-party datasets, images, trademarks, and user-uploaded content are not automatically covered by this license.
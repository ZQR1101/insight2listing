<p align="center">
  <strong>Insight2Listing</strong>
</p>

<p align="center">
  Evidence-grounded market insight, product opportunity validation, and intelligent Listing workflows for Amazon US
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License: MIT"/></a>
  <a href="https://github.com/ZQR1101/insight2listing/stargazers"><img src="https://img.shields.io/github/stars/ZQR1101/insight2listing?style=flat-square" alt="Stars"/></a>
  <br/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.14-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy"/>
  <img src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="CI"/>
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh-CN.md">简体中文</a>
  <br/>
  <a href="#-overview">Overview</a> · <a href="#-quick-start">Quick Start</a> · <a href="#-features">Features</a> · <a href="#-project-structure">Structure</a> · <a href="#-roadmap">Roadmap</a> · <a href="#-license">License</a>
</p>

---

## 📋 What is Insight2Listing?

Insight2Listing turns scattered reviews, competitor data, and verified product facts into a structured, auditable Listing pipeline for **Amazon US**. It is a **workflow-first** system — chat assists, it never replaces the structured data — designed around one core promise:

> **Every insight and every claim in your Listing is traceable to a source.** The system never invents facts.

A candidate product and some market data flow through an evidence-grounded pipeline:

```text
Products & market data
      ↓
Validation & source tracking
      ↓
Comment insights & competitor gaps
      ↓
Product opportunity card
      ↓
Human-confirmed product facts
      ↓
Listing & visual asset generation
      ↓
Fact, image & platform-rule checks
      ↓
Human review & export
```

**Current milestone:** the backend and the data-import pipeline are implemented and tested. Comment insight, Listing generation, visual assets, and the web UI are the next milestones (see [Roadmap](#-roadmap)).

### Highlights

- **Evidence over prose** — every pain point, keyword and selling point carries a source reference
- **Fact isolation** — the system distinguishes *Fact / Inference / Suggestion* and never writes an unconfirmed capability into a Listing
- **Three-format import** — CSV, JSON and XLSX through a common adapter + canonical schema
- **Idempotent & safe** — deterministic deduplication and spreadsheet formula-injection protection
- **Self-hosted first, hosted-ready** — Docker Compose, BYOK models, workspace isolation baked in
- **Model-agnostic** — text, embedding, and image providers behind swappable interfaces

---

> [!TIP]
> ### 🔑 Bring Your Own Key
>
> Insight2Listing is BYOK. You provide your own model API keys — there is **no cloud gating, no hosted runtime** in this milestone, and your data stays in your environment. API keys live on the backend only and are never sent to the browser or written to logs.
>
> The system is also **honest about its boundaries**: it does **not** scrape Amazon, does **not** promise to pick a best-seller, and does **not** auto-publish any product. Listing main images must be based on real product photos.

---

## 🚀 Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python tooling
- Docker — local databases

### 1. Start the infrastructure

```powershell
Copy-Item .env.example .env
docker compose up -d postgres minio redis
```

The Postgres host port is `5050` by default so it does not collide with an unrelated local Postgres. `DATABASE_URL` in `.env.example` points there — change it if you prefer another port.

### 2. Run the API

```bash
cd apps/api
uv sync
uv run alembic upgrade head     # apply migrations
uv run python run.py            # http://localhost:8000  (OpenAPI docs at /docs)
```

> 🪟 **Windows note:** `run.py` drives uvicorn on a SelectorEventLoop because the psycopg async driver cannot run on Windows' default ProactorEventLoop. Prefer it over `uvicorn app.main:app` on Windows.

### 3. Run tests, lint and typecheck

```bash
cd apps/api
uv run pytest                   # requires the Postgres container running
uv run ruff check src tests
uv run mypy src
```

The test suite provisions a dedicated `insight2listing_test` database from `DATABASE_URL` and truncates tables between tests, so dev/application data is never touched.

### 4. Run the whole stack in containers

```bash
docker compose up --build api
```

The `api` service runs Alembic migrations on startup and then serves the app.

---

## ✨ Features

### Implemented · Backend & Data Import

| Area | Capabilities |
| --- | --- |
| **Projects** | Workspaces, projects, and the workflow state machine (`DRAFT → DATA_IMPORTED → … → EXPORTED`) |
| **Data import** | CSV / JSON / XLSX adapters, auto field mapping (with synonym + currency-suffix fallback), preview, import reports |
| **Validation** | Field coercion, required-field checks, row-level error location, deduplication by external id / title / content hash |
| **Security** | Spreadsheet formula-injection escaping; API keys backend-only; audit logging of create/status/import events |
| **Traceability** | `SourceRecord` with license, usage scope, observed time and payload hash; per-field freshness metadata |
| **Model providers** | Swappable `TextInsight / Embedding / Image / Moderation` interfaces with mock implementations (offline-ready) |
| **Quality gates** | CI runs lint (ruff), typecheck (mypy), tests (Postgres service), and a migration-vs-model check |

### Planned · Next Milestones

| Area | Direction |
| --- | --- |
| **Comment insight** | Cleaning → topic & sentiment → semantic clustering → cross-competitor merging → evidence binding |
| **Opportunity card** | Weighted scores, confidence, missing dimensions, per-version scoring |
| **Listing workbench** | Title / bullets / description / search terms generation, versioning, fact & rule checks |
| **Visual creatives** | Real-product image edits + GPT Image 2, deterministic text overlay, consistency checks |
| **Web UI** | Workflow-first Next.js interface with chat as an assistant surfaces |
| **Amazon SP-API** | Official connectors + seller OAuth in a later beta phase |

---

## 💡 Use Cases

> *"Why do buyers keep complaining about the zipper on packing cubes?"*

> *"Which reviews support this selling point before I put it on the Listing?"*

> *"Turn these confirmed product facts into an Amazon title, five bullets, and search terms — without fabricating features."*

The initial test products — compression packing cubes, glass oil sprayers, and car trash cans — validate cross-category behaviour and evaluation quality. They are not investment advice.

---

## 🔧 Project Structure

```
insight2listing/
├── apps/
│   ├── api/                     # FastAPI backend  (repository in active development)
│   │   ├── src/app/
│   │   │   ├── api/             #   REST endpoints (health, projects, imports, products, reviews)
│   │   │   ├── core/            #   Settings, DB engine, enums, security guards
│   │   │   ├── models/          #   SQLAlchemy models (project, catalog, reviews, sources, audit)
│   │   │   ├── schemas/         #   Pydantic API schemas
│   │   │   ├── ingestion/       #   CSV/JSON/XLSX adapters → mapping → canonical → dedup → importer
│   │   │   ├── providers/       #   Swappable model-provider interfaces + mocks
│   │   │   └── audit/           #   Audit event logging
│   │   ├── alembic/             #   Database migrations
│   │   ├── tests/               #   pytest suite
│   │   └── run.py               #   Windows-friendly dev server launcher
│   ├── web/                     # Next.js frontend (not yet implemented)
│   └── worker/                  # Background task worker (not yet implemented)
├── packages/
│   ├── schemas/ ui/ i18n/ rules/ prompts/ evals/   # shared packages (planned)
├── examples/synthetic-data/     # synthetic, clearly-labelled data only
├── docs/                        # architecture, API, data-source and eval documents
├── .github/workflows/           # CI: lint, typecheck, test, migrate
├── outputs/                     # product & technical baseline documents
├── docker-compose.yml
└── LICENSE
```

### Key Architecture

- **Module-first FastAPI** (`apps/api`) — a modular monolith; import, projects, catalog, reviews, sources, providers and audit are distinct modules behind a versioned `/api/v1` surface
- **Canonical import schema** — adapters only parse formats; business logic reads a single canonical schema with freshness + license metadata
- **Audit trail** — generate / edit / confirm / export actions are recorded so downstream claims stay attributable
- **Provider seam** — text, embedding, image and moderation models are swappable so no business logic is bound to a vendor

### Data & evidence principles

- **Fact / Inference / Suggestion** are kept separate; an unverified property is never written as an existing capability (§11)
- **Formula injection** is neutralised at import time — `=`/`+`/`-`/`@`/tab-led cells are escaped before storage (§18.4)
- **License discipline** — the repo ships synthetic data only; no scraped reviews, no unlicensed product images (§8.7)

---

## 🗺️ Roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| **A/B** | Engineering foundation + data import pipeline | ✅ Done (this milestone) |
| **C** | Comment insight & opportunity card | ⏳ Next |
| **D** | Listing workbench | Planned |
| **E** | Visual creatives (GPT Image 2) | Planned |
| **F** | Evaluations & open-source release | Planned |
| **G** | Live data & seller beta (SP-API) | Later |

Full detail in [`outputs/Insight2Listing详细产品与技术方案.md`](outputs/Insight2Listing详细产品与技术方案.md).

---

## 🤝 Contributing

Contributions are welcome — bug reports, feature ideas, and pull requests all help.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch and open a Pull Request

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the contribution guide and [`SECURITY.md`](SECURITY.md) for security policy.

---

## 📄 License

Source code is released under the [MIT License](LICENSE). Third-party datasets, product images, trademarks, fonts, and user-uploaded content are **not** automatically covered by this license; the repository ships synthetic data only. See [`DATA_LICENSE.md`](DATA_LICENSE.md) and [`DISCLAIMER.md`](DISCLAIMER.md) for details.

---

## ⭐ Support

If Insight2Listing is useful to you, consider giving it a ⭐ — it helps the project grow.
# Architecture

## Overview

Resona AI is a monolithic-by-design college MVP: one FastAPI backend, one
Next.js frontend, one SQLite database, and a standalone `ml/` pipeline that
writes artifacts consumed by the backend. No microservices, message queues,
or distributed infrastructure — deliberately, to keep the system
understandable and reproducible within a college project scope.

```
┌─────────────┐      HTTP/JSON      ┌──────────────┐
│  apps/web    │ ─────────────────▶ │  apps/api     │
│  Next.js     │ ◀───────────────── │  FastAPI      │
└─────────────┘                     └──────┬───────┘
                                            │ SQLAlchemy
                                            ▼
                                     ┌──────────────┐
                                     │  SQLite DB    │
                                     └──────┬───────┘
                                            ▲
                                            │ writes predictions/
                                            │ personas/recommendations
                                     ┌──────┴───────┐
                                     │  ml/ pipeline │
                                     │  (offline)    │
                                     └──────────────┘
```

## Backend (`apps/api`)

- **FastAPI** application, versioned API under `/api/v1`.
- **SQLAlchemy 2.0** declarative models, **SQLite** for storage (file-based,
  zero-config — appropriate for MVP scale).
- **Pydantic Settings** for environment configuration (`app/core/config.py`).
- Layout:
  - `app/models/` — SQLAlchemy ORM models (one file per entity)
  - `app/schemas/` — Pydantic request/response schemas (added as endpoints
    are built in later phases)
  - `app/api/v1/` — versioned route modules
  - `app/db/` — engine/session/base setup

### Data model (Phase 1)

| Model | Purpose |
|---|---|
| `User` | listener account |
| `Track` | song with audio features |
| `ListeningEvent` | a single play event linking a user to a track |
| `PersonalityPrediction` | model-estimated Big Five trait associations for a user |
| `Persona` | discovered listener cluster/persona assignment |
| `Recommendation` | a scored, explainable track recommendation |
| `Feedback` | user feedback (like/dislike) on a recommendation |

## Frontend (`apps/web`)

- **Next.js (App Router)** + **TypeScript** + **Tailwind CSS**.
- Minimal design system in `src/components/ui/` (Card, Badge — expanded as
  pages are built).
- `src/components/` holds shell-level components (NavBar, Footer,
  HealthStatus).
- **Recharts** for data visualization, **lucide-react** for icons (added in
  the dashboard/recommendation phases).

## ML pipeline (`ml/`)

Offline, script-driven pipeline — not a live service:

- `ml/data/` — dataset loading and cleaning
- `ml/features/` — audio + behavioral feature engineering
- `ml/personality/` — Big Five trait estimation models (classical ML first;
  a neural model is added only if it earns its complexity)
- `ml/personas/` — clustering for listener persona discovery
- `ml/recommendation/` — recommendation scoring + explanation generation
- `ml/evaluation/` — offline metrics, reported in `EVALUATION.md`

Trained artifacts are written to `models/` and loaded by the backend at
inference time. No online/streaming training in this MVP.

## Why this design

- **SQLite over Postgres**: zero infrastructure, fully reproducible with a
  single file, sufficient for MVP data volumes.
- **Monolith over microservices**: one deploy target, one codebase to
  reason about — matches the scope of a college submission.
- **Offline ML pipeline over live training service**: training is
  reproducible via scripts (`scripts/`), results are versioned as files in
  `models/`, and the API only performs inference.

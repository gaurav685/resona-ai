# Architecture

## Overview

Resona AI is a monolithic-by-design college MVP: one FastAPI backend, one
Streamlit frontend, one SQLite database, and a standalone `ml/` pipeline
that writes artifacts consumed by the backend at inference time. No
microservices, message queues, or distributed infrastructure — deliberately,
to keep the system understandable and reproducible within a college
project scope. See README.md § 16 for what a production version would add.

```
┌──────────────┐   Python calls      ┌───────────────┐
│ streamlit_app │ ─────────────────▶ │  apps/api      │
│  Streamlit    │ ◀───────────────── │  FastAPI       │
│  (9 pages)    │   (server-side)     └──────┬────────┘
└──────────────┘                            │
                                              │ reads at inference time
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                     ┌────────────┐  ┌───────────────┐  ┌───────────────┐
                     │  models/    │  │ data/processed │  │  SQLite DB    │
                     │ (trained    │  │ (real events,  │  │ (evidence +   │
                     │  artifacts) │  │  from ml/)      │  │  feedback)    │
                     └──────┬─────┘  └───────┬────────┘  └───────────────┘
                            ▲                ▲
                            │  writes         │  writes
                     ┌──────┴────────────────┴───────┐
                     │            ml/ pipeline         │
                     │  (offline — scripts, not a       │
                     │   live service)                  │
                     └──────────────────────────────────┘
```

## Backend (`apps/api`)

- **FastAPI**, versioned API under `/api/v1`.
- **SQLAlchemy 2.0** + **SQLite**, **Pydantic Settings** for config
  (`app/core/config.py`).
- `app/ml/runtime.py` — the one place that loads `ml/` artifacts and
  `models/` files for the API (lazy, `lru_cache`d); every route handler
  calls into it rather than touching files directly.
- Layout: `app/models/` (SQLAlchemy ORM), `app/schemas/` (Pydantic I/O),
  `app/api/v1/` (route modules), `app/db/` (engine/session).

### Data model

Two generations of models coexist, deliberately:

| Model | Purpose | Status |
|---|---|---|
| `User`, `Track`, `ListeningEvent`, `PersonalityPrediction`, `Persona`, `Recommendation`, `Feedback` | Phase 1 scaffolding for a future app-native signup flow | Declared, never populated — the real pipeline runs on file-based research data, not these tables |
| `RecommendationLog`, `RecommendationFeedback` | Phase 5 — persisted evidence + feedback for real recommendations, keyed by Last.fm string ids (no FK to the unpopulated `User`/`Track` tables) | Actively used by every recommendation request |

### API surface

| Route | Purpose |
|---|---|
| `GET /health`, `/api/v1/health` | liveness |
| `GET /api/v1/users` | real Last.fm 1K user list (demo-listener picker) |
| `GET /api/v1/users/{id}/listening-dna` | behavioral features + top artists |
| `GET /api/v1/users/{id}/persona` | KMeans cluster assignment + z-scores |
| `GET /api/v1/users/{id}/current-context` | session-vs-baseline shift classification |
| `GET /api/v1/users/{id}/taste-evolution` | real monthly-binned trends |
| `GET /api/v1/personality/sample-participants` | real beyond_big_five participants + features |
| `POST /api/v1/personality/predict` | Big Five inference |
| `GET /api/v1/tracks/{id}/similar` | real audio-feature cosine similarity |
| `GET /api/v1/recommendations` | hybrid recommender, persists evidence |
| `GET /api/v1/recommendations/{id}/explanation` | regenerated from stored evidence |
| `POST /api/v1/recommendations/{id}/feedback` | like/dislike/skip/save/replay/hide |
| `POST /api/v1/uploads/analyze` | parses a real Spotify/YouTube Music/Apple Music export, runs the same DNA/context/recommendation pipeline on it, in memory, nothing written to disk |

## Frontend (`streamlit_app`)

Streamlit (native multipage app, `pages/` directory) + Plotly for charts.
9 pages (Home, Dashboard, Listening DNA, Personality, Persona, Current
State, Recommendations, Taste Evolution, About). `lib/state.py`'s
`render_user_picker()` holds the selected demo listener in
`st.session_state` (no auth in this MVP — see README § 15); `lib/api.py`
is the single client surface, one function per backend endpoint. Because
Streamlit executes each page's Python server-side, API calls happen from
the Streamlit process itself (`RESONA_API_URL`, defaults to
`http://localhost:8000`, or `http://api:8000` under Docker Compose) rather
than from the browser — no CORS exposure of the API to the client.

Originally built as a Next.js + TypeScript + Tailwind + Recharts app
(Phase 6); replaced with this Streamlit version by explicit request. The
backend and its contract were untouched by the swap.

## ML pipeline (`ml/`)

Offline, script-driven — never imported as a live service by the API
beyond its pure functions (`ml/features/*`, `ml/recommendation/evidence.py`,
`ml/recommendation/feedback.py` are imported directly by `app/ml/runtime.py`
for shared logic; training/clustering/evaluation scripts are run manually,
not at request time):

- `ml/features/` — `listening_dna.py`, `context.py`, `taste_evolution.py`
- `ml/personality/` — `dataset.py`, `train_classical.py`, `train_nn.py`
  (GPU-aware), `compare_and_select.py`
- `ml/personas/` — `cluster.py` (KMeans + DBSCAN comparison + PCA)
- `ml/recommendation/` — `catalog.py`, `item_similarity.py`,
  `content_similarity.py`, `hybrid.py`, `evidence.py`, `feedback.py`,
  `evaluate.py`

Trained artifacts are written to `models/` (binaries gitignored, metrics
JSON/CSV kept) and loaded by the backend at inference time.

## Why this design

- **SQLite over Postgres**: zero infrastructure, fully reproducible with a
  single file, sufficient for MVP data volumes.
- **Monolith over microservices**: one deploy target, one codebase — matches
  the scope of a college submission.
- **Offline ML pipeline over live training service**: training is
  reproducible via scripts, results are versioned as files in `models/`,
  and the API only performs inference.
- **Two model generations, not a migration**: retrofitting the Phase 1
  `User`/`Track` FK schema onto Last.fm's string ids would mean fabricating
  thousands of placeholder rows just to satisfy a constraint; the Phase 5
  tables were sized for what's actually needed instead.

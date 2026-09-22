# Resona AI

**Understand people through music.**

Resona AI is a college research MVP: an AI-powered music intelligence system
that analyzes listening behavior to estimate personality-related trait
associations, discover listener personas, detect listening context/mood, and
generate explainable, personalized music recommendations.

> Personality outputs are **model-estimated associations**, not psychological
> diagnoses. See [MODEL_CARD.md](./MODEL_CARD.md).

## Status

**Phase 1 — Foundation.** Project scaffold, database schema, API health
endpoints, and application shell are in place. ML pipeline, dashboard, and
recommendation UI are built in later phases.

## Project layout

```
resona-ai/
├── apps/
│   ├── web/            Next.js + TypeScript + Tailwind frontend
│   └── api/             FastAPI + SQLAlchemy + SQLite backend
├── ml/
│   ├── data/            dataset loading utilities
│   ├── features/        audio/behavioral feature engineering
│   ├── personality/      Big Five trait estimation models
│   ├── personas/         listener clustering / persona discovery
│   ├── recommendation/   recommendation engine
│   └── evaluation/       offline evaluation & metrics
├── data/
│   ├── raw/              downloaded/original datasets (gitignored)
│   ├── processed/        cleaned/feature-engineered data (gitignored)
│   └── samples/          small committed samples for reproducibility
├── models/                trained model artifacts (gitignored)
├── scripts/                setup/data/training utility scripts
├── tests/                  backend + ML tests
└── docs/                   supplementary documentation
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) CUDA-capable GPU for neural-network training phases

## Backend setup

```bash
cd apps/api
python -m venv ../../.venv   # or use repo-root .venv
pip install -r requirements.txt
cp ../../.env.example ../../.env
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Health checks:

- `GET /health`
- `GET /api/v1/health`

## Frontend setup

```bash
cd apps/web
npm install
npm run dev
```

App available at `http://localhost:3000`.

## Running tests

```bash
# from repo root, with venv active
pytest

# frontend
cd apps/web
npm run lint
npx tsc --noEmit
```

## Docker (optional)

```bash
docker compose up --build
```

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design
- [DATASETS.md](./DATASETS.md) — dataset registry and provenance
- [MODEL_CARD.md](./MODEL_CARD.md) — model behavior, limitations, safety
- [EVALUATION.md](./EVALUATION.md) — evaluation methodology and results
- [KILO_RULES.md](./KILO_RULES.md) — project ground rules for contributors/agents

## License

College coursework project. Not licensed for production/commercial use.

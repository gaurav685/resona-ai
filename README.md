# Resona AI

**Understand people through music.**

## 1. Project

Resona AI is a college research MVP: an AI-powered music intelligence system
that analyzes real listening behavior to estimate personality-related trait
associations, discover listener personas, detect current listening context,
and generate explainable, personalized, feedback-adaptive music
recommendations.

> Personality outputs are **model-estimated associations**, not psychological
> diagnoses. See [MODEL_CARD.md](./MODEL_CARD.md).

## 2. Problem

Typical music recommenders optimize a single signal — plays — and stop
there: they lean on whatever is already popular, offer no visibility into
*why* a track was suggested, and ignore listening context, personality
signal, or discovery intent entirely.

## 3. Motivation

Music preference is a rich behavioral signal. A system that actually reads
it — behaviorally, contextually, and (where real data supports it)
psychologically — can recommend more usefully and explain itself honestly,
instead of hiding behind a black-box "you might also like."

## 4. Solution

Resona builds four real, verifiable layers on top of raw listening data —
**Listening DNA**, a **personality model**, **persona discovery**, and
**context intelligence** — and feeds them into a transparent **hybrid
recommendation engine** whose every output carries stored evidence, a
generated (never-LLM) explanation, and a live feedback loop.

## 5. Architecture

```
User → Listening Data → Preprocessing → Listening DNA → Personality Model
  → Persona → Current Context → Recommendation Engine → Explanation
  → User Feedback → Updated Recommendations
```

- **Frontend**: Next.js 16 + TypeScript + Tailwind + Recharts + Lucide (9 pages)
- **Backend**: FastAPI + Pydantic + SQLAlchemy + SQLite
- **ML**: pandas/NumPy/scikit-learn/XGBoost + PyTorch (GPU-aware) + SHAP

Full system design: [ARCHITECTURE.md](./ARCHITECTURE.md).

```
resona-ai/
├── apps/
│   ├── web/            Next.js + TypeScript + Tailwind frontend (9 pages)
│   └── api/             FastAPI + SQLAlchemy + SQLite backend
├── ml/
│   ├── features/         Listening DNA, current-context, taste-evolution
│   ├── personality/       Big Five trait models (classical + PyTorch)
│   ├── personas/          listener clustering / persona discovery
│   └── recommendation/    catalog, similarity, hybrid engine, evidence, feedback, evaluation
├── data/
│   ├── registry.yaml      machine-readable dataset provenance
│   ├── raw/                downloaded/original datasets (gitignored)
│   ├── processed/          cleaned/feature-engineered data (gitignored)
│   └── samples/            small committed samples for reproducibility
├── models/                 trained model artifacts (binaries gitignored; metrics JSON/CSV kept)
├── scripts/                 dataset download/validate/process scripts
├── tests/                   backend + ML tests (98 total)
└── docker-compose.yml
```

## 6. Features

| Layer | What it does | Endpoint |
|---|---|---|
| Listening DNA | 10 real behavioral features (frequency, session stats, diversity, discovery, replay, temporal) from actual Last.fm events | `GET /api/v1/users/{id}/listening-dna` |
| Personality | Big Five model-estimated associations from a real research dataset | `GET /api/v1/personality/sample-participants`, `POST /api/v1/personality/predict` |
| Persona | KMeans-discovered listener clusters, names auto-derived from real cluster statistics | `GET /api/v1/users/{id}/persona` |
| Current Context | Rule-based session-vs-baseline behavioral shift classification | `GET /api/v1/users/{id}/current-context` |
| Taste Evolution | Real monthly-binned preference trends | `GET /api/v1/users/{id}/taste-evolution` |
| Content Similarity | Real audio-feature cosine similarity (beyond_big_five catalog) | `GET /api/v1/tracks/{id}/similar` |
| Recommendations | Hybrid scoring + MMR diversity rerank, novelty/context tunable | `GET /api/v1/recommendations` |
| Explanation | Deterministic, evidence-grounded (never an LLM) | `GET /api/v1/recommendations/{id}/explanation` |
| Feedback | like/dislike/skip/save/replay/hide, affects future scoring | `POST /api/v1/recommendations/{id}/feedback` |

## 7. Dataset sources

| Dataset | Real size | Local folder | License |
|---|---|---|---|
| Last.fm 1K | 672,741,554 bytes raw; 288,965 processed events, 992 users | `data/raw/lastfm_1k/`, `data/processed/lastfm_1k/` | Non-commercial, permission of Last.fm |
| Beyond the Big Five (Kleć et al., 2023) | 4.6 MB, 279 participants | `data/raw/beyond_big_five/` | CC BY 4.0 |
| Million Song Dataset (metadata subset) | 84 MB + 1.1 MB | `data/raw/million_song_dataset/` | MSD research terms |
| DEAM | 4.7 MB + 0.34 MB | `data/raw/deam/` | Research use |

All four downloaded automatically, no authentication required. Full
provenance, checksums, and license detail: [DATASETS.md](./DATASETS.md) and
`data/registry.yaml`. Pipeline detail: [DATA_PIPELINE.md](./DATA_PIPELINE.md).

## 8. ML methodology

Big Five regression (32 real features: 29 audio/emotion + 3 attitude
ratings → 5 traits), evaluated with an identical train/test split across
four candidates:

| Model | Test avg MAE | Selected |
|---|---|---|
| **Random Forest** | **0.6149** | ✅ |
| Linear Regression | 0.6174 | |
| XGBoost | 0.6361 | |
| PyTorch NN (GPU-trained) | 0.6434 | |

Random Forest won on the actual metric — the GPU-trained neural network did
not, and that's reported as-is. Persona discovery: KMeans, k=3 selected by
silhouette score (0.2393). Full methodology, negative-R² honesty, and SHAP
explainability detail: [MODEL_CARD.md](./MODEL_CARD.md).

## 9. Recommendation methodology

Candidate generation (top-1,500 Last.fm items by unique listeners) →
filtering (already-played + feedback-excluded) → weighted scoring
(co-listening similarity, artist preference, context alignment, novelty —
all normalized, weights configurable) → MMR diversity rerank (max 2
tracks/artist). Evaluated against a most-popular baseline with a real
leave-last-N-out split — see § 11.

## 10. Explainability

Every recommendation persists structured evidence (SQLite) at generation
time. `GET /api/v1/recommendations/{id}/explanation` **regenerates** its
text from that stored evidence at read time — deterministic templates, no
LLM. Reason codes (`similar_to_recent_listening`, `matches_current_context`,
`introduces_new_artist`, `exploration_candidate`, `behavioral_signal`) only
fire when their real evidence crosses a stated threshold.

## 11. Actual evaluation results

**Personality** (beyond_big_five, 279 participants, 80/20 split, seed=42):
Random Forest MAE 0.615, R² -0.048 — R² negative for nearly every
trait/model on this small dataset; reported honestly, not hidden.

**Recommendations** (985 users, leave-last-5-out, no leakage — real numbers
from `models/recommendation/evaluation_results.json`):

| Metric (K=10) | Resona | Most-popular baseline |
|---|---|---|
| Precision | 0.0016 | 0.0007 |
| Recall | 0.0032 | 0.0016 |
| NDCG | 0.0034 | 0.0010 |
| Hit Rate | 0.0132 | 0.0071 |
| Coverage | 0.956 | 0.011 |
| Diversity | 0.964 | 0.893 |
| Novelty | 0.766 | 0.247 |

Resona beats the baseline on every metric — but absolute precision/recall
are genuinely low (sparse implicit feedback + a capped candidate pool);
that's stated, not smoothed over. Full detail: [EVALUATION.md](./EVALUATION.md).

## 12. Screenshots

_Not included in this submission — capture via `npm run dev` (frontend) +
`uvicorn` (backend) running together locally, then screenshot the 9 pages
listed in § 6/Architecture. (The sandboxed environment this MVP was built
in had no connected browser to capture screenshots automatically.)_

## 13. Installation

**Prerequisites**: Python 3.11+, Node.js 20+, (optional) CUDA-capable GPU.

```bash
git clone <this-repo>
cd resona-ai
python -m venv .venv
source .venv/Scripts/activate   # or .venv\Scripts\activate on Windows PowerShell
pip install -r apps/api/requirements.txt -r ml/requirements.txt
# GPU PyTorch (optional — CPU wheel installs automatically as a dependency
# otherwise): pip install torch --index-url https://download.pytorch.org/whl/cu126
cd apps/web && npm install && cd ../..
cp .env.example .env
```

Download and process the real datasets, then train/cluster (reproduces
every artifact this README cites):

```bash
python scripts/download_datasets.py
python scripts/validate_datasets.py
python scripts/process_datasets.py
python ml/personality/train_classical.py
python ml/personality/train_nn.py
python ml/personality/compare_and_select.py
python ml/personas/cluster.py
python ml/recommendation/item_similarity.py
python ml/recommendation/content_similarity.py
python ml/recommendation/evaluate.py
```

## 14. Running locally

```bash
# Backend
cd apps/api && uvicorn app.main:app --reload   # http://localhost:8000

# Frontend (separate terminal)
cd apps/web && npm run dev                      # http://localhost:3000

# Or both via Docker (after the pipeline above has produced models/ and data/processed/)
docker compose up --build
```

Tests:

```bash
pytest                              # backend + ML, 98 tests
cd apps/web && npm run lint && npx tsc --noEmit && npm run build
```

## 15. Limitations

- 279 personality participants is small for 5-target regression on 32
  features — R² is negative for nearly every trait/model.
- Last.fm behavioral data and the personality/audio-feature datasets have
  disjoint identity spaces — no listener has both real behavioral and real
  personality data; the app never pretends otherwise (see the Personality
  page's demo-participant flow).
- Recommendation candidate pool capped at the 1,500 most-listened-to items
  for tractability — absolute precision/recall are low as a genuine
  consequence.
- night/weekend listening ratios use UTC timestamps, not the listener's
  true local time zone (not present in source data).
- No auth/user accounts — a real demo-listener picker stands in.

## 16. Future work

### Current college MVP
SQLite · local hybrid recommender · basic co-listening + audio-feature
similarity · classical + one small PyTorch model · local Docker Compose ·
simple bounded feedback reweighting.

### Future production expansion
- SQLite → **PostgreSQL**
- Local recommendation engine → **scalable recommendation service**
- Basic similarity → **vector embeddings / vector database**
- Simple personality models → **advanced multimodal intelligence**
- Batch processing → **streaming/event-driven architecture** (e.g. Kafka)
- Local Docker → **cloud deployment**
- Ad hoc experiment tracking → **MLflow / model registry**
- Simple feedback weighting → **advanced ranking / online learning**
- Spotify OAuth for real listener accounts
- **Redis** for caching hot recommendation queries

None of the above is implemented now — this MVP is intentionally sized to
finish, demonstrate, and be graded, not to simulate production
infrastructure.

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design
- [DATASETS.md](./DATASETS.md) — dataset registry and provenance
- [DATA_PIPELINE.md](./DATA_PIPELINE.md) — preprocessing detail
- [MODEL_CARD.md](./MODEL_CARD.md) — model behavior, limitations, safety
- [EVALUATION.md](./EVALUATION.md) — evaluation methodology and results
- [KILO_RULES.md](./KILO_RULES.md) — project ground rules for contributors/agents

## License

College coursework project. Not licensed for production/commercial use.

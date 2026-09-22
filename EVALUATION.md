# Evaluation

Every number below came from an actual run of the referenced script
against actual project data. No metric is estimated, assumed, or
fabricated — where something could not be measured, that is stated
explicitly instead.

## Principles

- Every reported metric cites the script/command that produced it.
- Train/test splits and random seeds are recorded for reproducibility.
- A method is never declared "better" unless the actual numbers say so.

---

## Personality estimation (Phase 3)

Run: `python ml/personality/train_classical.py && python ml/personality/train_nn.py && python ml/personality/compare_and_select.py`

Dataset: `beyond_big_five`, 279 participants, single 80/20 train/test split
(seed=42), 5-fold CV on train reported alongside for a small-sample sanity
check. Full detail in [MODEL_CARD.md](./MODEL_CARD.md).

| Model | Test avg MAE | Test avg RMSE | Test avg R² |
|---|---|---|---|
| **Random Forest (selected)** | **0.615** | 0.757 | -0.048 |
| Linear Regression | 0.617 | 0.756 | -0.046 |
| XGBoost | 0.636 | 0.791 | -0.147 |
| PyTorch NN (GPU-trained) | 0.643 | 0.806 | -0.220 |

Random Forest won on the actual metric (lowest MAE) — the neural network
was not assumed to win, and did not. R² is negative for nearly every
model/trait: on this 279-row dataset, none of these models currently
explain more test-set variance than predicting the training mean. Reported
as-is, not hidden.

## Persona discovery (Phase 3)

Run: `python ml/personas/cluster.py`

983 Last.fm 1K users (≥20 events each), KMeans with k selected by
silhouette score (scanned k=2–8):

| k | Silhouette | Davies-Bouldin |
|---|---|---|
| 2 | 0.2268 | 1.5585 |
| **3 (selected)** | **0.2393** | **1.2067** |
| 4 | 0.2233 | 1.2947 |

DBSCAN comparison (eps=1.5, min_samples=5) found only 1 real cluster (106
noise points) — no useful structure, so KMeans was kept. A silhouette of
0.24 is real but moderate, not strong — reported honestly.

## Context/mood detection (Phase 4, Part A)

No formal metric is reported here: there is no ground-truth "correct
context label" dataset to score classification accuracy against — the
four labels (Exploratory, Focused, Reflective, Routine) come from a
transparent, deterministic rule over actual behavioral shift signals (see
`ml/features/context.py`), not a trained classifier. What can be verified
is that the rule actually fires on real data and produces a real,
non-degenerate distribution across all 992 users:

```
Exploratory: 524   Routine: 276   Focused: 153   Reflective: 39
```

(Run: the loop in `tests/ml/test_context.py` and ad-hoc verification —
see DATA_PIPELINE.md-style reproduction in `ml/features/context.py`.)

---

## Recommendation engine (Phase 4, Parts B–D)

### Methodology

Run: `python ml/recommendation/evaluate.py`

- Per-user leave-last-N-out split: each user with ≥10 events has their
  last `min(5, 20%)` events (by timestamp) held out as ground truth; the
  rest is "train". **No leakage**: the item catalog, item-item
  co-occurrence similarity matrix, and every preference signal used for
  scoring are rebuilt from the train split only.
- Evaluated on **985 users** (of 992 total — 7 had fewer than 10 events).
- Candidate/catalog pool: top 1,500 items by unique listeners (see
  `ml/recommendation/catalog.py` — a documented MVP tradeoff, not a
  full-catalog computation).
- Baseline: global most-popular train items (same list for every user,
  non-personalized).
- Resona: hybrid recommender (content/co-listening similarity + artist
  preference + context alignment + novelty, MMR diversity rerank with a
  max-2-per-artist cap).

### Results — actual, both K=5 and K=10

| Metric | Resona (K=5) | Baseline (K=5) | Resona (K=10) | Baseline (K=10) |
|---|---|---|---|---|
| Precision | 0.0026 | 0.0006 | 0.0016 | 0.0007 |
| Recall | 0.0026 | 0.0007 | 0.0032 | 0.0016 |
| NDCG | 0.0031 | 0.0006 | 0.0034 | 0.0010 |
| Hit Rate | 0.0112 | 0.0030 | 0.0132 | 0.0071 |
| Coverage | 0.8673 | 0.0067 | 0.9560 | 0.0107 |
| Diversity | 0.9569 | 0.8693 | 0.9635 | 0.8933 |
| Novelty | 0.7629 | 0.1829 | 0.7658 | 0.2468 |

Raw output: `models/recommendation/evaluation_results.json`.

### Honest interpretation

**Absolute precision/recall/NDCG/hit-rate are low for both methods** —
around 0.1–1.3%. This is a real, expected consequence of a hard implicit-
feedback setup: a 1,500-item candidate pool drawn mostly from *other*
users' plays, evaluated against a specific user's actual next 1–5 tracks
(often a long-tail item outside that pool entirely, or a repeat of
something already in their train history and therefore filtered out as a
candidate). This is not a broken pipeline — it's what these numbers
genuinely look like on a small, sparse, capped Last.fm sample; a
production system with the full catalog and richer signals would be
expected to do better, and that is a stated limitation, not a claim.

**Resona beats the most-popular baseline on every single metric**,
typically by 2–4x on ranking quality (precision/recall/NDCG/hit-rate), and
dramatically on coverage (87–96% of the catalog gets recommended to
*someone*, vs. ~1% for the baseline, which by construction only ever
recommends the same fixed top-K list) and novelty (0.76 vs. 0.18–0.25 —
Resona surfaces less-generic items). This is a genuine, measured win for
personalization over a naive non-personalized baseline — not a claim that
Resona is "good" in absolute terms, which the low precision/recall numbers
above explicitly do not support.

### What was NOT measured

- No personality-informed ranking signal was evaluated — `personality_signal`
  is not used by the recommender (no personality labels exist for Last.fm
  users; see MODEL_CARD.md).
- Content-based (audio-feature) similarity was not evaluated in this
  pipeline — it operates on a disjoint 745-track catalog
  (`beyond_big_five`) with no overlap with Last.fm track identities, so it
  is demonstrated separately via `GET /api/v1/tracks/{id}/similar` rather
  than scored against Last.fm ground truth.

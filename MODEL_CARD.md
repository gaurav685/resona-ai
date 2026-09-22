# Model Card — Resona AI

Every number in this document was produced by an actual run of the
scripts under `ml/` against the actual datasets in `data/` — nothing here
is estimated or invented. Re-run instructions are given per section.

## Intended use

Resona AI estimates associations between listening behavior and Big Five
personality traits, discovers listener personas via clustering, and (in a
later phase) generates explainable music recommendations.

**Personality outputs are model-estimated associations only.** They are
statistical associations learned from a small research dataset, not a
validated psychological instrument. They must never be presented, used, or
interpreted as psychological diagnoses, clinical assessments, or
definitive statements about a person's character. Every `/api/v1/personality/predict`
response carries this disclaimer.

---

## 1. Big Five personality model

### Dataset

- **Source:** `beyond_big_five` — Kleć et al. (2023), "Beyond the Big Five
  Personality Traits for Music Recommendation Systems" (see
  [DATASETS.md](./DATASETS.md)).
- **279 participants**, each rating a set of songs; personality (BFI-2 Big
  Five + 15 lower-order facets) measured once per participant.
- **NOT** derived from Last.fm — no personality labels exist for Last.fm
  users in this project, and none were fabricated.

### Feature set (32 inputs)

Per-participant mean, across all songs the participant rated, of:

- **29 low-level audio / emotion features** extracted from the rated songs:
  `rms, lowenergy, eventdensity, pulseclarity, attacktime_{mean,std,slope,periodentropy},
  attackslope_{mean,std,slope,periodentropy}, zerocross, brightness, centroid,
  spread, skewness, kurtosis, flatness, mirentropy, inharmonicity, activity,
  valence, tension, happy, sad, tender, anger, fear`
- **3 music-attitude Likert ratings** (`Q1` cognitive, `Q2` motivational,
  `Q3` social), also averaged per participant.

This mirrors the feature set the source paper uses to relate music
preference to personality (see `ml/personality/dataset.py`).

### Targets

Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
(BFI-2 scale, continuous, 1–5).

### Train/test methodology

- Single held-out split: 223 train / 56 test (`test_size=0.2, random_seed=42`).
- 5-fold cross-validation on the training split reported alongside, to
  sanity-check the single split isn't a fluke (dataset is small — 279
  rows — so this is a real limitation, stated here rather than hidden).
- No data leakage: aggregation (mean per participant) happens before the
  split is drawn; the same split is reused identically across all four
  candidate models for a fair comparison.

### Classical baselines — actual results

Run: `python ml/personality/train_classical.py`

| Model | Test avg MAE | Test avg RMSE | Test avg R² | 5-fold CV MAE (train) |
|---|---|---|---|---|
| Linear Regression | 0.617 | 0.756 | -0.046 | 0.570 ± 0.039 |
| **Random Forest** | **0.615** | 0.757 | -0.048 | 0.570 ± 0.031 |
| XGBoost | 0.636 | 0.791 | -0.147 | 0.613 ± 0.027 |

Per-trait detail (Random Forest, test set): Openness MAE 0.494, R² -0.045;
Conscientiousness MAE 0.795, R² -0.077; Extraversion MAE 0.608, R² -0.084;
Agreeableness MAE 0.452, R² 0.051; Neuroticism MAE 0.726, R² -0.084.

**R² is negative for nearly every trait/model.** This is a real,
unfavorable result, reported as-is: on this 279-row dataset, none of the
classical baselines explain test-set variance better than predicting the
training mean. This is consistent with personality-from-music-preference
being a genuinely hard, weak-signal research problem — not a bug in the
pipeline.

### PyTorch neural network — actual results

Run: `python ml/personality/train_nn.py --epochs 100 --patience 10`

**Architecture:** `Linear(32→64) → ReLU → Dropout(0.3) → Linear(64→32) →
ReLU → Dropout(0.3) → Linear(32→5)`. Loss: MSE. Optimizer: Adam.

**Device (actual, printed at training time):**
```
PyTorch version: 2.14.0+cu126
CUDA available: True
Device: CUDA
GPU: NVIDIA GeForce RTX 3050 Ti Laptop GPU
CUDA version: 12.6
```

**Training configuration:** epochs requested 100, batch size 16, learning
rate 0.001, patience 10, seed 42. Split: 189 train / 34 val / 56 test
(same test set as the classical models).

**Early stopping:** triggered — `Early stopping at epoch 88/100`,
`Best epoch: 78` (best validation loss 0.5653). Training duration: 3.9s
(this GPU, this dataset size — genuinely fast given only 279 rows).

**Test-set result (best checkpoint):** avg MAE 0.643, avg RMSE 0.806, avg
R² -0.220 — **worse than the classical baselines**, including plain Linear
Regression. This is reported honestly: the neural network was not assumed
to win, and here it didn't. Global feature importance (permutation, top
3): `brightness`, `Q2`, `flatness`.

### Model comparison and selection

Run: `python ml/personality/compare_and_select.py`

| Model | Test avg MAE | Selected |
|---|---|---|
| **Random Forest** | **0.6149** | ✅ |
| Linear Regression | 0.6174 | |
| XGBoost | 0.6361 | |
| PyTorch NN | 0.6434 | |

**Selected model: Random Forest** (lowest average test MAE). The
GPU-trained neural network is kept as an experimental artifact
(`models/personality/pytorch_nn.pt` + `nn_results.json`) even though it
did not become the production model — per project rules, this is an
acceptable and expected outcome, not a failure to fix.

### Explainability

Global feature importance for the selected Random Forest model was
computed with **SHAP TreeExplainer** (mean |SHAP value| across the 5
per-trait sub-estimators, on a 100-row background sample). Top 5 features:
`Q3, Q2, sad, Q1, kurtosis` — the three self-reported music-attitude
ratings dominate over the low-level audio descriptors, which is a
substantively interpretable result. Per-request confidence is estimated
as the standard deviation of predictions across the Random Forest's
individual trees (only supported for this model type; other model types
report `confidence: null` with an explicit reason rather than a fake
number).

### Artifacts

`models/personality/{linear_regression,random_forest,xgboost}.joblib`,
`pytorch_nn.pt`, `classical_results.json`, `nn_results.json`,
`selected_model.json` (points the API at the winning model).

---

## 2. Persona discovery (clustering)

### Data

Listening DNA features (`ml/features/listening_dna.py`) computed from
`data/processed/lastfm_1k/listening_events.csv` (288,965 events, 992
users). Users with fewer than 20 events are excluded for stable session
statistics (983 of 992 retained).

### Method

`StandardScaler` → `KMeans`, k scanned over 2–8, selected by silhouette
score. `DBSCAN` run for comparison (not selected). `PCA(2)` computed for
visualization coordinates.

Run: `python ml/personas/cluster.py`

**k selection (actual scores):**

| k | Silhouette | Davies-Bouldin |
|---|---|---|
| 2 | 0.2268 | 1.5585 |
| **3** | **0.2393** | **1.2067** |
| 4 | 0.2233 | 1.2947 |
| 5 | 0.1953 | 1.4141 |
| 6 | 0.1953 | 1.3158 |
| 7 | 0.1991 | 1.3301 |
| 8 | 0.1859 | 1.3643 |

**Selected k=3.** Final: silhouette 0.2393, Davies-Bouldin 1.2067 — a
real, moderate (not strong) cluster structure; reported as-is.

**DBSCAN comparison** (eps=1.5, min_samples=5): found only 1 cluster (106
noise points) — did not find useful structure on this feature space, so
KMeans was kept. This negative result is reported rather than hidden.

**PCA(2) explained variance ratio:** [0.366, 0.256] (62.1% of variance in
2 components).

### Cluster profiles (derived from actual centroids, not hard-coded)

| Cluster | Name (auto-derived) | Users | Notable |
|---|---|---|---|
| 0 | High Replay Rate / Low Artist Diversity | 444 | replay_rate z=+0.80, artist_diversity z=-0.76 |
| 1 | Low Replay Rate / Low Repeat Rate | 527 | replay_rate z=-0.65, artist_diversity z=+0.60 |
| 2 | High Avg Session Duration / High Tracks/Session | 12 | listening_frequency z=+5.59 (heavy/power users, hit the 300-event sampling cap) |

Names are generated by `ml/personas/cluster.py::name_cluster()` from each
cluster's top-2 |z-score| features vs. the global mean — never a hard-coded
lookup table.

### Artifacts

`models/personas/{kmeans,scaler,pca}.joblib`, `user_cluster_assignments.csv`,
`persona_metadata.json`.

---

## 3. Listening DNA (feature engineering)

See `ml/features/listening_dna.py`. Computes, from actual event data:
`listening_frequency, average_session_duration_min, tracks_per_session,
replay_rate, repeat_rate, artist_diversity, artist_concentration,
discovery_rate, night_listening_ratio_utc, weekend_listening_ratio_utc`.

**Explicitly unavailable** (returned as `null` with a stated reason, never
fabricated): `completion_rate, skip_rate, genre_diversity,
genre_concentration, energy, valence, danceability, tempo, acousticness,
instrumentalness, speechiness` — no track-duration/skip field, no genre
labels, and no audio-feature dataset are joined to Last.fm track
identifiers in this MVP (see [DATASETS.md](./DATASETS.md)).

`night_listening_ratio_utc` / `weekend_listening_ratio_utc` are computed
from event UTC timestamps, not the listener's local time (Last.fm 1K
gives country, not a UTC offset) — labeled accordingly, not corrected.

---

## GPU / device policy

Every training script in this project (`ml/personality/train_nn.py`)
detects CUDA at runtime via `torch.cuda.is_available()`, prints the actual
device/GPU/CUDA/PyTorch versions before training, and only claims "CUDA"
when the model and batches are actually moved to that device. On this
development machine: NVIDIA GeForce RTX 3050 Ti Laptop GPU, driver
supporting CUDA 13.0, PyTorch built against CUDA 12.6 — training above was
verified running on this GPU. If CUDA is unavailable on another machine,
the script falls back to CPU and prints the actual reason instead of
silently continuing.

## Limitations

- **279 participants** is a small dataset for 5-target regression with 32
  features; single-split test metrics carry real variance (hence the
  5-fold CV numbers alongside).
- Negative R² across nearly all trait/model combinations means these
  models currently explain less test-set variance than the training mean
  — they should be treated as a research baseline, not a working
  predictor, in this MVP.
- Persona clusters are behavioral (Last.fm 1K), not linked to the
  personality dataset — no personality-informed persona claims are made.
- MSD and DEAM audio features are not joined to Last.fm tracks (see
  DATASETS.md), so Listening DNA has no audio-content dimensions yet.

## Ethical considerations

- Personality-related inferences are sensitive. Every prediction response
  includes the model-estimated-association disclaimer, never a diagnosis.
- No demographic or protected-attribute inference is performed.
- Given the negative R² results above, this MVP does not claim the model
  is currently reliable enough for consequential decisions about a person
  — it is presented as a research/explainability demonstration.

# Evaluation

Status: **no models trained, no evaluation performed yet.** This file
documents the evaluation methodology to be used in later phases. No
metrics, numbers, or results below are fabricated — this is a plan, not a
report.

## Principles

- Every reported metric must come from an actual run against actual data,
  with the script and command used to produce it noted alongside the
  number.
- If a metric cannot be measured (e.g. no ground truth available for a
  task), this file will say so explicitly rather than omit or estimate it.
- Train/validation/test splits and random seeds will be recorded for
  reproducibility.

## Planned evaluation per component

### Personality estimation
- Metric candidates: MAE / RMSE per trait (if regression), against
  whatever validation labels the selected dataset provides.
- Baseline: predict the training-set mean per trait.

### Persona discovery
- Metric candidates: silhouette score, inertia/elbow analysis, qualitative
  cluster profile inspection.
- No ground-truth labels expected — evaluation will be largely
  unsupervised/qualitative.

### Context/mood detection
- Metric candidates: accuracy / F1 against session-derived labels, if a
  labeling strategy is defined.

### Recommendation quality
- Metric candidates: precision@k / recall@k on held-out listening events,
  offline; explanation quality assessed qualitatively.

## Results

_None yet. Populated once models exist._

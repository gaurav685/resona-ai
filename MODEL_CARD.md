# Model Card — Resona AI

Status: **no models trained yet.** This file is a placeholder structure to
be filled in with real information as each model is built in later phases.
No metrics, datasets, or behavior claims below are fabricated in advance.

## Intended use

Resona AI estimates associations between listening behavior and Big Five
personality traits, discovers listener personas via clustering, detects
listening context, and generates explainable music recommendations.

**Personality outputs are model-estimated associations only.** They are
derived from statistical patterns in listening behavior, not validated
psychological instruments. They must not be presented, used, or interpreted
as psychological diagnoses, clinical assessments, or definitive statements
about a person's character.

## Models (to be documented as built)

| Model | Task | Algorithm | Training data | Status |
|---|---|---|---|---|
| Personality estimator | Big Five trait regression | TBD | TBD | not built |
| Persona clustering | listener segmentation | TBD | TBD | not built |
| Context/mood detector | session context classification | TBD | TBD | not built |
| Recommendation model | ranking/scoring | TBD | TBD | not built |

## Evaluation

See [EVALUATION.md](./EVALUATION.md). No results yet — none will be
reported until models are actually trained and measured.

## Limitations (known, to be expanded)

- Trained on whatever dataset(s) are documented in `DATASETS.md`; does not
  generalize beyond the population and platform those datasets represent.
- Personality estimation from behavioral data is inherently noisy;
  predictions carry meaningful uncertainty.
- Cold-start users (little/no listening history) will have low-confidence
  or unavailable predictions.

## Ethical considerations

- Personality-related inferences are sensitive. Outputs are always labeled
  as model-estimated associations, never as fact.
- No demographic or protected-attribute inference is performed.
- Users' listening data stays local to this project's database; no
  third-party sharing is implemented.

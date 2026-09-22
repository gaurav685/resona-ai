# Project Ground Rules

Binding rules for anyone (human or AI agent) working on this repository.

## 1. Local files are the source of truth

Every piece of code, config, data registry, model, test, or doc must exist
as an actual file in this repository. Do not describe changes without
making them. When implementing something: create/update the file, verify
it exists, run relevant checks, fix errors before calling it done.

## 2. Never push to GitHub automatically

No `git push` or equivalent without explicit, per-instance authorization
from the project owner. A local commit is not permission to push.
Completing a phase is not permission to push. Workflow:

```
implement → test → fix → inspect diff → local commit → STOP → wait for explicit push command
```

## 3. Do not overengineer

This is a compressed college MVP. No microservices, Kubernetes, Kafka,
event buses, enterprise IAM, or complex MLOps. Impress through the idea,
the ML pipeline, explainability, and UI — not infrastructure complexity.

## 4. Never fabricate results

No invented datasets, users, labels, metrics, accuracy, recommendations,
evaluation results, latency, or scalability claims. If something can't be
measured, say so explicitly.

## 5. Personality safety

All personality outputs must be labeled **"model-estimated associations,"**
never presented as psychological diagnoses or deterministic claims about a
person.

## 6. Automatic dataset download

Publicly downloadable datasets requiring no unavoidable human action are
downloaded automatically into `data/raw/<dataset_name>/`. If a dataset
needs authentication, license acceptance, CAPTCHA, or manual approval:
stop and report the exact blocker. Never fabricate or silently substitute
data. Don't blindly download large datasets — determine what's actually
needed for the MVP first.

## 7. GPU / ML training rule

Before training any neural network: detect CUDA availability and GPU name,
prefer GPU when available, fall back to CPU otherwise, and print actual
device info at the start of training. Never claim GPU training falsely.
Show live per-epoch progress (loss, validation metric, time) for neural
network training only — classical models (linear regression, random
forest, etc.) do not get fake epochs. Record device/GPU info in model
metadata.

# Dataset Registry

Status: **no datasets downloaded yet.** Phase 1 establishes project
structure only. This file will be updated with actual dataset names,
sources, licenses, sizes, and download dates when a later phase acquires
data — nothing below is fabricated or assumed in advance.

## Directory convention

```
data/
├── raw/         original, unmodified downloads — one subdirectory per dataset
├── processed/   cleaned / feature-engineered outputs of ml/data and ml/features
└── samples/     small, committed samples for reproducibility and quick tests
```

`data/raw/` and `data/processed/` are gitignored (datasets are not vendored
into version control). `data/samples/` is small enough to commit.

## Candidate datasets (planning only — not yet acquired)

These are candidates under consideration for the personality/persona/
recommendation pipeline. None have been downloaded. Each will be evaluated
for license terms and whether download requires authentication before any
automated download is attempted, per project rules.

| Candidate | Purpose | Access | Status |
|---|---|---|---|
| TBD | listening history / behavioral data | TBD | not selected |
| TBD | audio features | TBD | not selected |
| TBD | personality-labeled data (for validation) | TBD | not selected |

This table will be replaced with real entries — including exact source URL,
license, row counts, and retrieval date — once a dataset is actually
downloaded in a later phase.

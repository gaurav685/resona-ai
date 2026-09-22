# Dataset Registry

Status: **4 datasets downloaded and processed.** Everything below reflects
what was actually downloaded, validated, and processed — see
`data/registry.yaml` for the machine-readable source of truth (verified
2026-09-23) and [DATA_PIPELINE.md](./DATA_PIPELINE.md) for exact
preprocessing steps and real row counts.

## Directory convention

```
data/
├── registry.yaml   machine-readable dataset provenance (source, license, size, checksum)
├── raw/            original, unmodified downloads (gitignored — not vendored)
├── processed/      canonical CSVs produced by scripts/process_datasets.py (gitignored)
└── samples/        small committed samples for reproducibility (not yet populated)
```

## Datasets

### 1. Beyond the Big Five Personality Traits for Music Recommendation Systems

- **Purpose:** Big Five / BFI-2 personality trait modeling.
- **Source:** [Figshare](https://figshare.com/articles/dataset/Beyond_the_Big_Five_Personality_Traits_for_Music_Recommendation_Systems_-_dataset/19678962), DOI `10.6084/m9.figshare.19678962.v1`.
- **License:** CC BY 4.0.
- **Size:** 4.6 MB, single Excel file (`PER_dataset.xls`), 5,278 rows / 279 participants.
- **Download:** direct HTTP, no authentication, md5-checksum-verified.
- **Subset used:** full file. De-duplicated to one row per participant for
  the `PersonalityRecord` output (Big Five values are constant per
  participant — verified, not assumed).
- **Processed output:** `data/processed/beyond_big_five/personality_records.csv` (279 rows).

### 2. Last.fm Dataset — 1K users

- **Purpose:** listening behavior, temporal patterns, behavioral clustering for persona discovery.
- **Source:** [ocelma.net](http://ocelma.net/MusicRecommendationDataset/lastfm-1K.html) (official MTG/UPF mirror).
- **License:** distributed with permission of Last.fm, **non-commercial use only**.
- **Size:** 672,741,554 bytes (~642 MiB) compressed `.tar.gz`.
- **Download:** direct HTTP, no authentication.
- **Subset used:** full user-profile file (992 users); listening-events
  file streamed directly from the compressed archive (never fully
  extracted — it's several GB uncompressed), capped at 300 events per user
  so every user contributes data for persona clustering.
- **Processed output:** `data/processed/lastfm_1k/users.csv` (992 rows),
  `data/processed/lastfm_1k/listening_events.csv` (288,965 rows across all
  992 users, sessionized).

### 3. Million Song Dataset — metadata subset

- **Purpose:** track/artist metadata.
- **Source:** [millionsongdataset.com](http://millionsongdataset.com/pages/getting-dataset/).
- **License:** research use per MSD terms (Echo Nest / LabROSA).
- **Size:** `unique_tracks.txt` ~84 MB (1,000,000 rows), `artist_location.txt` ~1.1 MB (13,850 rows).
- **Download:** direct HTTP, no authentication.
- **Subset used:** text metadata files only — the 1.8 GB audio-feature
  subset and 746 MB full metadata SQLite DB were deliberately skipped as
  unnecessary for this MVP. **Consequence: no tempo/energy/valence audio
  features are available from MSD** — `Track` audio-feature fields stay
  null for MSD-sourced tracks rather than being fabricated. Tracks
  reservoir-sampled (seed=42) to 20,000 of the full 1,000,000.
- **Processed output:** `data/processed/million_song_dataset/artists.csv`
  (13,850 rows), `data/processed/million_song_dataset/tracks.csv` (20,000 rows).

### 4. DEAM — MediaEval Database for Emotional Analysis in Music

- **Purpose:** valence/arousal emotion annotations for listening context/mood detection.
- **Source:** [cvml.unige.ch/databases/DEAM](https://cvml.unige.ch/databases/DEAM/).
- **License:** research use per DEAM manual; annotations only (no audio downloaded).
- **Size:** annotations 4.7 MB, metadata 0.34 MB.
- **Download:** direct HTTP, no authentication.
- **Subset used:** annotations + metadata only. `DEAM_audio.zip` (1.3 GB)
  and `features.zip` (601 MB, openSMILE descriptors) were not downloaded —
  not needed since this MVP only uses the valence/arousal labels.
- **Processed output:** `data/processed/deam/emotion_annotations.csv`
  (1,802 rows), `data/processed/deam/track_metadata.csv` (1,132 rows;
  2015-release metadata had 29 malformed CSV rows in the source, skipped
  and counted, not silently dropped).

## What was NOT forced

Per project rules, no dataset was forced into a component it doesn't
genuinely support. In particular: `beyond_big_five`'s per-song
audio/emotion columns (`valence`, `activity`, `tension`, ...) were **not**
mapped to the `EmotionAnnotation` schema — `activity` is not the same
construct as DEAM's `arousal`, and conflating them would be a fabricated
equivalence. See [DATA_DICTIONARY.md](./DATA_DICTIONARY.md) for the exact
schema coverage matrix.

## Reproducing the download

```bash
pip install -r ml/requirements.txt
python scripts/download_datasets.py
python scripts/validate_datasets.py
python scripts/process_datasets.py
```

No dataset in this registry required authentication, license
click-through, or CAPTCHA — all four were downloaded automatically.

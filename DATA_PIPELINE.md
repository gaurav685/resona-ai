# Data Pipeline

How raw datasets become the processed CSVs consumed by `ml/` and (later)
the backend. Every number in this file comes from an actual run of the
scripts below against the actual downloaded files — nothing is estimated.

## Stages

```
data/registry.yaml
        │
        ▼
scripts/download_datasets.py   → data/raw/<dataset>/       (original files)
        │
        ▼
scripts/validate_datasets.py   → integrity / schema checks (stdout report)
        │
        ▼
scripts/process_datasets.py    → data/processed/<dataset>/ (canonical CSVs)
```

Canonical target schemas: `ml/data/schemas.py` (see
[DATA_DICTIONARY.md](./DATA_DICTIONARY.md)).

## Per-dataset processing notes

### beyond_big_five

- Source: `PER_dataset.xls`, 5,278 rows (279 participants × up to 19 songs
  rated each).
- Big Five trait values are constant per participant across their rows
  (verified: 0 of 279 participants have more than one distinct value for
  any trait) — so the dataset is de-duplicated to one row per `userId`
  before being mapped to `PersonalityRecord`.
- 15 lower-order BFI-2 facet scores are preserved in `raw_facets` (JSON).
- Output: `data/processed/beyond_big_five/personality_records.csv` (279 rows).

### lastfm_1k

- Source: `lastfm-dataset-1K.tar.gz` (~642 MiB), official MTG/UPF mirror.
- The small `userid-profile.tsv` member is extracted and parsed fully →
  `User` records.
- The large listening-events member
  (`userid-timestamp-artid-artname-traid-traname.tsv`) is **never fully
  extracted to disk**. It's read as a stream directly from the open tar
  member (`tarfile.extractfile`), line by line, and capped at 300 events
  per user — a deliberate manageable subset for the college-MVP scope that
  still covers all 992 users (a first-200,000-rows cap was tried first but
  only covered 8 users, since the source file is sorted by user; see
  `data/registry.yaml` for the full rationale).
- Timestamps are parsed and validated per `ml/data/schemas.py`; rows with
  unparseable timestamps or the wrong tab-separated field count are
  dropped and counted (reported by the script, not silently discarded).
- Sessionization: events are grouped per user into sessions using a
  30-minute inactivity-gap rule (a listening event starts a new session if
  more than 30 minutes have passed since the user's previous event).
- Output: `data/processed/lastfm_1k/users.csv` (992 rows),
  `data/processed/lastfm_1k/listening_events.csv` (288,965 rows, all 992
  users represented).

### million_song_dataset

- Source: `unique_tracks.txt` (1,000,000 rows, track_id/song_id/artist/title)
  and `artist_location.txt` (13,850 rows, real Echo Nest artist IDs + geo).
- The 1.8 GB audio-feature subset and 746 MB full metadata SQLite DB were
  **not downloaded** — not needed for the MVP scope (see registry).
  Consequence: MSD contributes **track/artist identity metadata only**; no
  tempo/energy/valence audio features come from this source.
- `unique_tracks.txt` has no artist_id column, only artist name text.
  There is no reliable official join to `artist_location.txt`'s artist IDs
  in the files distributed by the source, so `Track.artist_id` is left
  null for MSD tracks rather than fabricating a match.
- Tracks are reservoir-sampled (seed=42) down to 20,000 of the 1,000,000
  rows for the processed output — streamed line-by-line, never loaded
  fully into memory.
- Output: `data/processed/million_song_dataset/artists.csv` (13,850 rows),
  `data/processed/million_song_dataset/tracks.csv` (20,000 rows).

### deam

- Source: `DEAM_Annotations.zip` (song-level averaged valence/arousal,
  1,802 rows after de-duplicating the two overlapping annotation files)
  and `metadata.zip` (three inconsistent per-year schemas: 2013, 2014,
  2015).
- `metadata_2015.csv` contains 29 rows with unescaped commas in free-text
  fields (malformed CSV in the source); these are skipped and the count is
  reported by the script rather than silently dropped.
- Output: `data/processed/deam/emotion_annotations.csv` (1,802 rows),
  `data/processed/deam/track_metadata.csv` (1,132 rows, union of the three
  metadata releases, de-duplicated by song_id).
- `DEAM_audio.zip` (1.3 GB) and `features.zip` (601 MB, openSMILE
  low-level descriptors) were **not downloaded** — this MVP only needs the
  valence/arousal labels.

## Reproducing this pipeline

```bash
python -m venv .venv && source .venv/Scripts/activate   # or .venv\Scripts\activate on native Windows shells
pip install -r ml/requirements.txt

python scripts/download_datasets.py
python scripts/validate_datasets.py
python scripts/process_datasets.py
```

All four datasets download over plain HTTP from their official sources,
with no authentication required, so this is fully automatable and was run
end-to-end while building this phase.

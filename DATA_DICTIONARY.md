# Data Dictionary

Canonical schemas used across the Resona AI data pipeline. Defined in
`ml/data/schemas.py` as pydantic models; every raw dataset is mapped into
these before being written to `data/processed/`. Fields not populated by a
given source are left null — never fabricated.

## User

| Field | Type | Notes |
|---|---|---|
| `user_id` | str | normalized (stripped), source-specific |
| `gender` | str? | as reported by source |
| `age` | int? | as reported by source |
| `country` | str? | as reported by source |
| `registered_at` | datetime? | parsed from source timestamp |
| `source_dataset` | str | provenance |

## Artist

| Field | Type | Notes |
|---|---|---|
| `artist_id` | str | source-specific ID (e.g. Echo Nest artist ID for MSD) |
| `name` | str | |
| `mbid` | str? | MusicBrainz ID, when available |
| `source_dataset` | str | |

## Album

| Field | Type | Notes |
|---|---|---|
| `album_id` | str | |
| `title` | str | |
| `artist_id` | str? | |
| `source_dataset` | str | |

## Genre

| Field | Type | Notes |
|---|---|---|
| `genre_id` | str | |
| `name` | str | |
| `source_dataset` | str | |

## Track

| Field | Type | Notes |
|---|---|---|
| `track_id` | str | |
| `title` | str | |
| `artist_id` | str? | null when no reliable join exists in the source |
| `artist_name` | str? | |
| `album_id` | str? | |
| `duration_sec` | float? | |
| `source_dataset` | str | |

## ListeningEvent

| Field | Type | Notes |
|---|---|---|
| `event_id` | str | md5 of (user_id, timestamp, track_title) |
| `user_id` | str | |
| `track_id` | str? | |
| `artist_name` | str? | |
| `track_title` | str? | |
| `played_at` | datetime | required, parsed and validated |
| `session_id` | str? | assigned by sessionization (30-minute inactivity gap) |
| `source_dataset` | str | |

## PersonalityRecord

Model-estimated / self-reported Big Five associations — **never** treated
as a clinical assessment. See [MODEL_CARD.md](./MODEL_CARD.md).

| Field | Type | Notes |
|---|---|---|
| `participant_id` | str | |
| `openness` | float? | Big Five trait (BFI-2, 1–5 scale) |
| `conscientiousness` | float? | |
| `extraversion` | float? | |
| `agreeableness` | float? | |
| `neuroticism` | float? | |
| `raw_facets` | dict? | 15 lower-order BFI-2 facet scores |
| `source_dataset` | str | |

## EmotionAnnotation

| Field | Type | Notes |
|---|---|---|
| `track_id` | str | |
| `valence_mean` | float | DEAM 1–9 scale |
| `arousal_mean` | float | DEAM 1–9 scale |
| `valence_std` | float? | inter-rater std. dev. |
| `arousal_std` | float? | inter-rater std. dev. |
| `source_dataset` | str | |

## Source → schema coverage

| Dataset | User | Artist | Track | ListeningEvent | PersonalityRecord | EmotionAnnotation |
|---|---|---|---|---|---|---|
| beyond_big_five | — | — | — | — | ✅ | — |
| lastfm_1k | ✅ | — | — | ✅ | — | — |
| million_song_dataset | — | ✅ | ✅ (no audio features) | — | — | — |
| deam | — | — | ✅ (metadata only) | — | — | ✅ |

No dataset is forced into a schema it doesn't genuinely support (rule:
"don't force every dataset into every component").

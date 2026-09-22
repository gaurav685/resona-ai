"""Preprocess raw datasets into canonical CSVs under data/processed/<name>/.

Implements: schema validation (via ml/data/schemas.py pydantic models),
missing-value handling, duplicate handling, ID normalization, timestamp
parsing, and basic sessionization for listening events. Large raw files are
streamed/chunked rather than loaded fully into memory where practical.

Usage:
    python scripts/process_datasets.py                    # all datasets
    python scripts/process_datasets.py --dataset deam
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ml"))
from data.schemas import (  # noqa: E402
    PersonalityRecord,
    Track,
    Artist,
    EmotionAnnotation,
    User,
    ListeningEvent,
    parse_timestamp,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

LASTFM_EVENTS_PER_USER = 300
MSD_TRACK_SAMPLE_ROWS = 20_000
SESSION_GAP_MINUTES = 30

BIG5_FACET_COLUMNS = [
    "sociability", "assertiveness", "energy_level",
    "compassion", "respectfulness", "trust",
    "organization", "productiveness", "responsibility",
    "anxiety", "depression", "emotional_volatility",
    "intellectual_curiosity", "aesthetic_sensitivity", "creative_imagination",
]


def _write_csv(df: pd.DataFrame, out_dir: Path, filename: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    df.to_csv(path, index=False)
    print(f"  wrote {path.relative_to(REPO_ROOT)} ({len(df):,} rows, {len(df.columns)} cols)")


# ---------------------------------------------------------------------------
# beyond_big_five
# ---------------------------------------------------------------------------

def process_beyond_big_five() -> None:
    print("[beyond_big_five]")
    src = RAW_DIR / "beyond_big_five" / "PER_dataset.xls"
    df = pd.read_excel(src)

    before = len(df)
    df = df.drop_duplicates(subset=["userId"])
    print(f"  {before} rows -> {len(df)} unique participants (dropped {before - len(df)} duplicate-user rows)")

    records = []
    errors = 0
    for _, row in df.iterrows():
        facets = {c: float(row[c]) for c in BIG5_FACET_COLUMNS if c in row and pd.notna(row[c])}
        try:
            rec = PersonalityRecord(
                participant_id=str(int(row["userId"])),
                openness=float(row["Openness"]),
                conscientiousness=float(row["Conscientiousness"]),
                extraversion=float(row["Extraversion"]),
                agreeableness=float(row["Agreeableness"]),
                neuroticism=float(row["Neuroticism"]),
                raw_facets=facets,
                source_dataset="beyond_big_five",
            )
        except Exception:
            errors += 1
            continue
        records.append(rec.model_dump())

    if errors:
        print(f"  schema validation rejected {errors} rows")

    out = pd.DataFrame(records)
    out["raw_facets"] = out["raw_facets"].apply(json.dumps)
    _write_csv(out, PROCESSED_DIR / "beyond_big_five", "personality_records.csv")


# ---------------------------------------------------------------------------
# million_song_dataset
# ---------------------------------------------------------------------------

def process_msd() -> None:
    print("[million_song_dataset]")
    tracks_path = RAW_DIR / "million_song_dataset" / "unique_tracks.txt"
    loc_path = RAW_DIR / "million_song_dataset" / "artist_location.txt"

    # Artists: from artist_location.txt (real Echo Nest artist IDs).
    artists = []
    with open(loc_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("<SEP>")
            if len(parts) != 5:
                continue
            artist_id, lat, lon, name, location = parts
            try:
                artists.append(Artist(artist_id=artist_id, name=name, source_dataset="million_song_dataset").model_dump())
            except Exception:
                continue
    artists_df = pd.DataFrame(artists).drop_duplicates(subset=["artist_id"])
    _write_csv(artists_df, PROCESSED_DIR / "million_song_dataset", "artists.csv")

    # Tracks: deterministic reservoir sample of MSD_TRACK_SAMPLE_ROWS from the
    # full 1,000,000-line file, streamed line-by-line (never fully loaded).
    import random

    rng = random.Random(42)
    sample: list[str] = []
    total_lines = 0
    with open(tracks_path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            total_lines += 1
            if len(sample) < MSD_TRACK_SAMPLE_ROWS:
                sample.append(line)
            else:
                j = rng.randint(0, i)
                if j < MSD_TRACK_SAMPLE_ROWS:
                    sample[j] = line

    track_records = []
    malformed = 0
    for line in sample:
        parts = line.rstrip("\n").split("<SEP>")
        if len(parts) != 4:
            malformed += 1
            continue
        track_id, song_id, artist_name, title = parts
        try:
            rec = Track(
                track_id=track_id,
                title=title,
                artist_name=artist_name,
                source_dataset="million_song_dataset",
            )
        except Exception:
            malformed += 1
            continue
        track_records.append(rec.model_dump())

    print(f"  sampled {len(track_records)} of {total_lines:,} total tracks (seed=42), {malformed} malformed skipped")
    print("  NOTE: artist_id left null on Track rows — no reliable official join between "
          "unique_tracks.txt artist names and artist_location.txt artist IDs is provided "
          "by the source; not fabricated here.")
    tracks_df = pd.DataFrame(track_records)
    _write_csv(tracks_df, PROCESSED_DIR / "million_song_dataset", "tracks.csv")


# ---------------------------------------------------------------------------
# deam
# ---------------------------------------------------------------------------

def process_deam() -> None:
    print("[deam]")
    ann_zip = RAW_DIR / "deam" / "DEAM_Annotations.zip"
    meta_zip = RAW_DIR / "deam" / "metadata.zip"

    with zipfile.ZipFile(ann_zip) as z:
        frames = []
        for name in [
            "annotations/annotations averaged per song/song_level/static_annotations_averaged_songs_1_2000.csv",
            "annotations/annotations averaged per song/song_level/static_annotations_averaged_songs_2000_2058.csv",
        ]:
            with z.open(name) as f:
                df = pd.read_csv(f)
                df.columns = [c.strip() for c in df.columns]
                frames.append(df)
        ann_df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["song_id"])

    records = []
    errors = 0
    for _, row in ann_df.iterrows():
        try:
            rec = EmotionAnnotation(
                track_id=str(int(row["song_id"])),
                valence_mean=float(row["valence_mean"]),
                arousal_mean=float(row["arousal_mean"]),
                valence_std=float(row["valence_std"]) if pd.notna(row["valence_std"]) else None,
                arousal_std=float(row["arousal_std"]) if pd.notna(row["arousal_std"]) else None,
                source_dataset="deam",
            )
        except Exception:
            errors += 1
            continue
        records.append(rec.model_dump())
    if errors:
        print(f"  schema validation rejected {errors} annotation rows")
    emo_df = pd.DataFrame(records)
    _write_csv(emo_df, PROCESSED_DIR / "deam", "emotion_annotations.csv")

    # Track/genre metadata: best-effort union across the three source files,
    # which have inconsistent schemas across DEAM's 2013/2014/2015 releases.
    meta_frames = []
    with zipfile.ZipFile(meta_zip) as z:
        specs = {
            "metadata/metadata_2013.csv": {"song_id": "song_id", "artist": "Artist", "title": "Song title", "genre": "Genre"},
            "metadata/metadata_2014.csv": {"song_id": "Id", "artist": "Artist", "title": "Track", "genre": "Genre"},
            "metadata/metadata_2015.csv": {"song_id": "id", "artist": "artist", "title": "title", "genre": "genre"},
        }
        skipped_2015 = 0
        for member, cols in specs.items():
            with z.open(member) as f:
                if member.endswith("2015.csv"):
                    before_rows = sum(1 for _ in zipfile.ZipFile(meta_zip).open(member)) - 1
                    df = pd.read_csv(f, on_bad_lines="skip", engine="python")
                    skipped_2015 = before_rows - len(df)
                else:
                    df = pd.read_csv(f)
            df = df.rename(columns={v: k for k, v in cols.items()})
            df = df[["song_id", "artist", "title", "genre"]].copy()
            for c in ("artist", "title", "genre"):
                df[c] = df[c].astype(str).str.strip()
            meta_frames.append(df)
        if skipped_2015:
            print(f"  metadata_2015.csv: skipped {skipped_2015} malformed rows (unescaped commas in source)")

    meta_df = pd.concat(meta_frames, ignore_index=True).drop_duplicates(subset=["song_id"])
    meta_df["track_id"] = meta_df["song_id"].astype(str)
    meta_df = meta_df[["track_id", "artist", "title", "genre"]]
    _write_csv(meta_df, PROCESSED_DIR / "deam", "track_metadata.csv")


# ---------------------------------------------------------------------------
# lastfm_1k
# ---------------------------------------------------------------------------

def _sessionize(events: pd.DataFrame) -> pd.DataFrame:
    events = events.sort_values(["user_id", "played_at"]).reset_index(drop=True)
    gap = pd.Timedelta(minutes=SESSION_GAP_MINUTES)
    session_ids = []
    counters: dict[str, int] = {}
    last_ts: dict[str, pd.Timestamp] = {}
    for user_id, ts in zip(events["user_id"], events["played_at"]):
        if user_id not in counters or ts - last_ts[user_id] > gap:
            counters[user_id] = counters.get(user_id, 0) + 1
        last_ts[user_id] = ts
        session_ids.append(f"{user_id}-s{counters[user_id]}")
    events["session_id"] = session_ids
    return events


def process_lastfm() -> None:
    print("[lastfm_1k]")
    archive = RAW_DIR / "lastfm_1k" / "lastfm-dataset-1K.tar.gz"
    if not archive.exists():
        print("  SKIPPED: archive not present")
        return

    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
        profile_name = next(n for n in names if n.endswith("userid-profile.tsv"))
        events_name = next(n for n in names if n.endswith("userid-timestamp-artid-artname-traid-traname.tsv"))

        # --- users (small file, extracted fully) ---
        with tar.extractfile(profile_name) as f:
            profile_df = pd.read_csv(f, sep="\t")
        profile_df.columns = [c.strip("#").strip().lower() for c in profile_df.columns]

        user_records = []
        errors = 0
        for _, row in profile_df.iterrows():
            try:
                rec = User(
                    user_id=row["id"],
                    gender=str(row.get("gender")) if pd.notna(row.get("gender")) else None,
                    age=int(row["age"]) if pd.notna(row.get("age")) else None,
                    country=str(row.get("country")) if pd.notna(row.get("country")) else None,
                    registered_at=row.get("registered") if pd.notna(row.get("registered")) else None,
                    source_dataset="lastfm_1k",
                )
            except Exception:
                errors += 1
                continue
            user_records.append(rec.model_dump())
        if errors:
            print(f"  schema validation rejected {errors} user rows")
        users_df = pd.DataFrame(user_records)
        _write_csv(users_df, PROCESSED_DIR / "lastfm_1k", "users.csv")

        # --- listening events: streamed from the tar member, never fully
        # extracted to disk. Column layout per source docs:
        # userid, timestamp, artist-mbid, artist-name, track-mbid, track-name
        #
        # The source file is sorted by user, so a naive "first N rows" cap
        # (used in an earlier version of this script) only ever captured a
        # handful of the heaviest-listening users. To get behavioral
        # diversity across the user base (needed for persona clustering in
        # Phase 3), we instead cap each user at LASTFM_EVENTS_PER_USER
        # events, scanning the full stream once so every user gets a
        # chance to contribute rows.
        with tar.extractfile(events_name) as f:
            rows = []
            malformed = 0
            bad_ts = 0
            user_counts: dict[str, int] = {}
            for raw_line in f:
                try:
                    line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
                except Exception:
                    malformed += 1
                    continue
                parts = line.split("\t")
                if len(parts) != 6:
                    malformed += 1
                    continue
                user_id, ts, _artist_mbid, artist_name, _track_mbid, track_name = parts
                if user_counts.get(user_id, 0) >= LASTFM_EVENTS_PER_USER:
                    continue
                played_at = parse_timestamp(ts)
                if played_at is None:
                    bad_ts += 1
                    continue
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
                rows.append(
                    {
                        "event_id": hashlib.md5(f"{user_id}|{ts}|{track_name}".encode()).hexdigest(),
                        "user_id": user_id,
                        "artist_name": artist_name,
                        "track_title": track_name,
                        "played_at": played_at,
                        "source_dataset": "lastfm_1k",
                    }
                )

    print(f"  streamed {len(rows):,} rows from source (cap {LASTFM_EVENTS_PER_USER}/user), "
          f"covering {len(user_counts):,} distinct users, "
          f"{malformed} malformed, {bad_ts} unparseable timestamps")

    events_df = pd.DataFrame(rows)
    before = len(events_df)
    events_df = events_df.drop_duplicates(subset=["user_id", "played_at", "track_title"])
    print(f"  dropped {before - len(events_df)} duplicate events")

    events_df["played_at"] = pd.to_datetime(events_df["played_at"], utc=True)
    events_df = _sessionize(events_df)
    n_sessions = events_df["session_id"].nunique()
    print(f"  sessionized into {n_sessions:,} sessions (gap threshold = {SESSION_GAP_MINUTES} min)")

    _write_csv(events_df, PROCESSED_DIR / "lastfm_1k", "listening_events.csv")


PROCESSORS = {
    "beyond_big_five": process_beyond_big_five,
    "million_song_dataset": process_msd,
    "deam": process_deam,
    "lastfm_1k": process_lastfm,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", help="process only this dataset name")
    args = parser.parse_args()

    names = [args.dataset] if args.dataset else list(PROCESSORS.keys())
    for name in names:
        PROCESSORS[name]()
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Part of the "bring your own history" feature: parses a listener's own
export from Spotify, YouTube Music, or Apple Music into the project's
canonical event shape (user_id, artist_name, track_title, played_at,
ms_played, skipped, source_dataset), so it can be run through the same
real ml/features/* functions used for the Last.fm 1K demo listeners.

Every field name below was verified against real, documented export
formats before writing this parser — never guessed:
  - Spotify: two real export variants exist.
      "basic" (older "Account data" request): endTime, artistName,
      trackName, msPlayed.
      "extended" (Extended Streaming History request): ts, ms_played,
      master_metadata_track_name, master_metadata_album_artist_name,
      reason_start, reason_end, skipped.
  - YouTube Music: Google Takeout's watch-history.json. Each YouTube Music
    entry has header == "YouTube Music", title (often "Watched <track>"),
    subtitles[0].name (the channel, usually "<Artist> - Topic" for
    auto-generated music channels), time (ISO 8601).
  - Apple Music: "Play History Daily Tracks.csv" /
    "Recently Played Tracks.csv" from Apple's "Get a copy of your data".
    Track Description is "<Artist> - <Track>"; Daily Tracks has
    Date Played + Play Duration Milliseconds, Recently Played has
    Last Event End Timestamp + Media duration in millis.

No live OAuth / API integration here — those require each listener's own
registered developer app (Spotify/Google), which this project can't
create on anyone's behalf. This is deliberately the "upload the export
you already have" path instead.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

import pandas as pd

CANONICAL_COLUMNS = ["user_id", "artist_name", "track_title", "played_at", "ms_played", "skipped", "source_dataset"]


class UnrecognizedUploadFormat(Exception):
    pass


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=CANONICAL_COLUMNS)


def parse_spotify_json(raw: bytes, user_id: str) -> pd.DataFrame:
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise UnrecognizedUploadFormat(f"not valid JSON: {e}") from e
    if not isinstance(data, list) or not data:
        return _empty_df()

    sample = data[0]
    rows = []
    if "master_metadata_track_name" in sample or "ts" in sample:
        # Extended Streaming History
        for row in data:
            track = row.get("master_metadata_track_name")
            artist = row.get("master_metadata_album_artist_name")
            if not track or not artist:
                continue  # podcast/video episodes etc. have no track/artist
            ts = row.get("ts")
            played_at = _parse_iso(ts)
            if played_at is None:
                continue
            rows.append(
                {
                    "user_id": user_id,
                    "artist_name": artist,
                    "track_title": track,
                    "played_at": played_at,
                    "ms_played": row.get("ms_played"),
                    "skipped": row.get("skipped"),
                    "source_dataset": "spotify_upload",
                }
            )
    elif "artistName" in sample or "endTime" in sample:
        # Basic "Account data" export
        for row in data:
            artist = row.get("artistName")
            track = row.get("trackName")
            if not track or not artist:
                continue
            played_at = _parse_iso(row.get("endTime"), fmt="%Y-%m-%d %H:%M")
            if played_at is None:
                continue
            rows.append(
                {
                    "user_id": user_id,
                    "artist_name": artist,
                    "track_title": track,
                    "played_at": played_at,
                    "ms_played": row.get("msPlayed"),
                    "skipped": None,
                    "source_dataset": "spotify_upload",
                }
            )
    else:
        raise UnrecognizedUploadFormat(
            "JSON doesn't match a known Spotify export (expected either "
            "master_metadata_track_name/ts, or artistName/endTime fields)"
        )
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def parse_youtube_music_json(raw: bytes, user_id: str) -> pd.DataFrame:
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise UnrecognizedUploadFormat(f"not valid JSON: {e}") from e
    if not isinstance(data, list):
        raise UnrecognizedUploadFormat("expected a JSON array (Google Takeout watch-history.json)")

    rows = []
    for row in data:
        if row.get("header") != "YouTube Music":
            continue  # this Takeout file also contains regular YouTube views
        title = row.get("title", "")
        track = title[len("Watched ") :] if title.startswith("Watched ") else title
        subtitles = row.get("subtitles") or []
        artist = subtitles[0]["name"] if subtitles and "name" in subtitles[0] else None
        if artist and artist.endswith(" - Topic"):
            artist = artist[: -len(" - Topic")]
        played_at = _parse_iso(row.get("time"))
        if not track or not artist or played_at is None:
            continue
        rows.append(
            {
                "user_id": user_id,
                "artist_name": artist,
                "track_title": track,
                "played_at": played_at,
                "ms_played": None,  # not present in Takeout watch history
                "skipped": None,
                "source_dataset": "youtube_music_upload",
            }
        )
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def parse_apple_music_csv(raw: bytes, user_id: str) -> pd.DataFrame:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise UnrecognizedUploadFormat(f"not valid UTF-8 CSV: {e}") from e

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = set(reader.fieldnames or [])
    if "Track Description" not in fieldnames:
        raise UnrecognizedUploadFormat(
            "CSV doesn't match a known Apple Music export (expected a 'Track Description' column — "
            "'Play History Daily Tracks.csv' or 'Recently Played Tracks.csv')"
        )
    is_daily = "Date Played" in fieldnames and "Play Duration Milliseconds" in fieldnames
    is_recent = "Last Event End Timestamp" in fieldnames and "Media duration in millis" in fieldnames
    if not (is_daily or is_recent):
        raise UnrecognizedUploadFormat(
            "recognized 'Track Description' but not the expected timestamp/duration columns for "
            "either Apple Music export variant"
        )

    rows = []
    for row in reader:
        desc = (row.get("Track Description") or "").strip()
        if " - " not in desc:
            continue  # can't split artist/track reliably
        artist, track = desc.split(" - ", 1)
        if is_daily:
            played_at = _parse_iso(row.get("Date Played"), fmt="%Y%m%d")
            ms_played = row.get("Play Duration Milliseconds")
        else:
            played_at = _parse_iso(row.get("Last Event End Timestamp"))
            ms_played = row.get("Media duration in millis")
        if played_at is None or not artist or not track:
            continue
        rows.append(
            {
                "user_id": user_id,
                "artist_name": artist.strip(),
                "track_title": track.strip(),
                "played_at": played_at,
                "ms_played": float(ms_played) if ms_played else None,
                "skipped": None,
                "source_dataset": "apple_music_upload",
            }
        )
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def _parse_iso(value, fmt: str | None = None) -> datetime | None:
    if not value:
        return None
    try:
        if fmt:
            dt = datetime.strptime(str(value), fmt)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def parse_uploaded_file(filename: str, raw: bytes, service: str, user_id: str) -> pd.DataFrame:
    """service: one of 'spotify', 'youtube_music', 'apple_music' — chosen
    explicitly by the uploader rather than sniffed, since file extensions
    alone don't distinguish these formats reliably."""
    if service == "spotify":
        return parse_spotify_json(raw, user_id)
    if service == "youtube_music":
        return parse_youtube_music_json(raw, user_id)
    if service == "apple_music":
        return parse_apple_music_csv(raw, user_id)
    raise UnrecognizedUploadFormat(f"unknown service: {service}")

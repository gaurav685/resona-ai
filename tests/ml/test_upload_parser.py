import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml"))

from features.upload_parser import (  # noqa: E402
    UnrecognizedUploadFormat,
    parse_apple_music_csv,
    parse_spotify_json,
    parse_uploaded_file,
    parse_youtube_music_json,
)

USER_ID = "uploaded_test_user"


def test_spotify_extended_format():
    data = [
        {
            "ts": "2024-03-01T10:00:00Z",
            "ms_played": 180000,
            "master_metadata_track_name": "Song A",
            "master_metadata_album_artist_name": "Artist A",
            "skipped": False,
        },
        {
            "ts": "2024-03-01T10:05:00Z",
            "ms_played": 5000,
            "master_metadata_track_name": "Song B",
            "master_metadata_album_artist_name": "Artist B",
            "skipped": True,
        },
        # podcast episode row (no track/artist) must be dropped, not crash
        {"ts": "2024-03-01T10:10:00Z", "ms_played": 100, "episode_name": "Ep 1"},
    ]
    df = parse_spotify_json(json.dumps(data).encode(), USER_ID)
    assert len(df) == 2
    assert df.iloc[0]["artist_name"] == "Artist A"
    assert df.iloc[0]["ms_played"] == 180000
    assert df.iloc[1]["skipped"] == True  # noqa: E712


def test_spotify_basic_format():
    data = [
        {"endTime": "2024-03-01 10:00", "artistName": "Artist A", "trackName": "Song A", "msPlayed": 180000},
    ]
    df = parse_spotify_json(json.dumps(data).encode(), USER_ID)
    assert len(df) == 1
    assert df.iloc[0]["artist_name"] == "Artist A"
    assert df.iloc[0]["source_dataset"] == "spotify_upload"


def test_spotify_unrecognized_format_raises():
    data = [{"some_other_field": 1}]
    with pytest.raises(UnrecognizedUploadFormat):
        parse_spotify_json(json.dumps(data).encode(), USER_ID)


def test_spotify_invalid_json_raises():
    with pytest.raises(UnrecognizedUploadFormat):
        parse_spotify_json(b"not json {{{", USER_ID)


def test_youtube_music_format():
    data = [
        {
            "header": "YouTube Music",
            "title": "Watched Song A",
            "titleUrl": "https://music.youtube.com/watch?v=x",
            "subtitles": [{"name": "Artist A - Topic", "url": "https://..."}],
            "time": "2024-03-01T10:00:00.000Z",
        },
        {
            "header": "YouTube",  # not music, must be filtered out
            "title": "Watched Some Video",
            "time": "2024-03-01T10:05:00.000Z",
        },
    ]
    df = parse_youtube_music_json(json.dumps(data).encode(), USER_ID)
    assert len(df) == 1
    assert df.iloc[0]["artist_name"] == "Artist A"  # "- Topic" suffix stripped
    assert df.iloc[0]["track_title"] == "Song A"  # "Watched " prefix stripped
    assert df.iloc[0]["source_dataset"] == "youtube_music_upload"


def test_apple_music_daily_tracks_csv():
    csv_text = (
        "Track Description,Container Description,Date Played,Play Duration Milliseconds\n"
        "Artist A - Song A,My Library,20240301,180000\n"
    )
    df = parse_apple_music_csv(csv_text.encode(), USER_ID)
    assert len(df) == 1
    assert df.iloc[0]["artist_name"] == "Artist A"
    assert df.iloc[0]["track_title"] == "Song A"
    assert df.iloc[0]["ms_played"] == 180000.0


def test_apple_music_recently_played_csv():
    csv_text = (
        "Track Description,Container Description,Last Event End Timestamp,Media duration in millis\n"
        "Artist A - Song A,My Library,2024-03-01T10:00:00Z,180000\n"
    )
    df = parse_apple_music_csv(csv_text.encode(), USER_ID)
    assert len(df) == 1
    assert df.iloc[0]["artist_name"] == "Artist A"


def test_apple_music_unrecognized_csv_raises():
    csv_text = "Not,A,Real,Export\n1,2,3,4\n"
    with pytest.raises(UnrecognizedUploadFormat):
        parse_apple_music_csv(csv_text.encode(), USER_ID)


def test_parse_uploaded_file_dispatch():
    data = [{"endTime": "2024-03-01 10:00", "artistName": "A", "trackName": "T", "msPlayed": 1000}]
    df = parse_uploaded_file("StreamingHistory0.json", json.dumps(data).encode(), "spotify", USER_ID)
    assert len(df) == 1

    with pytest.raises(UnrecognizedUploadFormat):
        parse_uploaded_file("x", b"", "unknown_service", USER_ID)

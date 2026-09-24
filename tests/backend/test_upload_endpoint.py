import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _spotify_payload():
    data = [
        {"endTime": "2024-03-01 10:00", "artistName": "Mgmt", "trackName": "Kids", "msPlayed": 180000},
        {"endTime": "2024-03-01 10:05", "artistName": "Mgmt", "trackName": "Time To Pretend", "msPlayed": 200000},
        {"endTime": "2024-03-01 11:00", "artistName": "Some Unknown Band", "trackName": "Random Track", "msPlayed": 150000},
    ]
    return json.dumps(data).encode()


def test_analyze_spotify_upload_returns_real_pipeline_output():
    files = {"files": ("StreamingHistory0.json", _spotify_payload(), "application/json")}
    resp = client.post("/api/v1/uploads/analyze", data={"service": "spotify"}, files=files)
    assert resp.status_code == 200
    body = resp.json()

    assert body["session_user_id"].startswith("uploaded_")
    assert body["n_events_parsed"] == 3
    assert body["n_distinct_tracks"] == 3
    assert 0 <= body["n_tracks_matched_catalog"] <= 3
    assert body["listening_dna"]["n_events"] == 3
    assert body["current_context"]["context_label"] in ("Exploratory", "Focused", "Reflective", "Routine", "Unknown")


def test_analyze_upload_recommendations_have_real_ids_and_explain():
    files = {"files": ("StreamingHistory0.json", _spotify_payload(), "application/json")}
    resp = client.post("/api/v1/uploads/analyze", data={"service": "spotify"}, files=files)
    body = resp.json()
    recs = body["recommendations"]
    if recs and recs["recommendations"]:
        rec_id = recs["recommendations"][0]["recommendation_id"]
        assert rec_id
        explain_resp = client.get(f"/api/v1/recommendations/{rec_id}/explanation")
        assert explain_resp.status_code == 200


def test_analyze_upload_feedback_works_like_any_other_recommendation():
    files = {"files": ("StreamingHistory0.json", _spotify_payload(), "application/json")}
    resp = client.post("/api/v1/uploads/analyze", data={"service": "spotify"}, files=files)
    recs = resp.json()["recommendations"]
    if recs and recs["recommendations"]:
        rec_id = recs["recommendations"][0]["recommendation_id"]
        fb_resp = client.post(f"/api/v1/recommendations/{rec_id}/feedback", json={"feedback_type": "like"})
        assert fb_resp.status_code == 200


def test_analyze_unrecognized_format_422():
    files = {"files": ("bad.json", b"not json at all", "application/json")}
    resp = client.post("/api/v1/uploads/analyze", data={"service": "spotify"}, files=files)
    assert resp.status_code == 422


def test_analyze_no_files_422():
    resp = client.post("/api/v1/uploads/analyze", data={"service": "spotify"}, files={})
    assert resp.status_code == 422


def test_analyze_youtube_music_upload():
    data = [
        {
            "header": "YouTube Music",
            "title": "Watched Kids",
            "subtitles": [{"name": "Mgmt - Topic"}],
            "time": "2024-03-01T10:00:00.000Z",
        }
    ]
    files = {"files": ("watch-history.json", json.dumps(data).encode(), "application/json")}
    resp = client.post("/api/v1/uploads/analyze", data={"service": "youtube_music"}, files=files)
    assert resp.status_code == 200
    assert resp.json()["n_events_parsed"] == 1


def test_analyze_apple_music_upload():
    csv_text = (
        "Track Description,Container Description,Date Played,Play Duration Milliseconds\n"
        "Mgmt - Kids,My Library,20240301,180000\n"
    )
    files = {"files": ("Apple Music - Play History Daily Tracks.csv", csv_text.encode(), "text/csv")}
    resp = client.post("/api/v1/uploads/analyze", data={"service": "apple_music"}, files=files)
    assert resp.status_code == 200
    assert resp.json()["n_events_parsed"] == 1


def test_analyze_multiple_files_concatenated():
    file1 = json.dumps([{"endTime": "2024-03-01 10:00", "artistName": "A", "trackName": "T1", "msPlayed": 1000}]).encode()
    file2 = json.dumps([{"endTime": "2024-03-01 10:05", "artistName": "B", "trackName": "T2", "msPlayed": 1000}]).encode()
    files = [
        ("files", ("StreamingHistory0.json", file1, "application/json")),
        ("files", ("StreamingHistory1.json", file2, "application/json")),
    ]
    resp = client.post("/api/v1/uploads/analyze", data={"service": "spotify"}, files=files)
    assert resp.status_code == 200
    assert resp.json()["n_events_parsed"] == 2
    assert resp.json()["n_files"] == 2

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from app.main import app
from app.ml.runtime import known_user_ids

client = TestClient(app)


def _sample_user_id() -> str:
    return sorted(known_user_ids())[0]


def test_current_context_known_user():
    user_id = _sample_user_id()
    resp = client.get(f"/api/v1/users/{user_id}/current-context")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == user_id
    assert body["context_label"] in ("Exploratory", "Focused", "Reflective", "Routine", "Unknown")
    # audio/genre shifts must be explicitly unavailable, never fabricated
    assert body["shifts"]["energy_shift"] is None
    assert body["shifts"]["energy_shift_unavailable_reason"]
    assert "psychological" in body["disclaimer"] or "medical" in body["disclaimer"]


def test_current_context_unknown_user_404():
    resp = client.get("/api/v1/users/does-not-exist/current-context")
    assert resp.status_code == 404


def test_similar_tracks_known_track():
    # a real songId from the beyond_big_five content-similarity catalog
    resp = client.get("/api/v1/tracks/16057/similar", params={"limit": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert body["track_id"] == "16057"
    assert len(body["similar_tracks"]) <= 3
    for t in body["similar_tracks"]:
        assert 0.0 <= t["similarity"] <= 1.0


def test_similar_tracks_unknown_track_404():
    resp = client.get("/api/v1/tracks/does-not-exist/similar")
    assert resp.status_code == 404


def test_recommendations_known_user():
    user_id = _sample_user_id()
    resp = client.get("/api/v1/recommendations", params={"user_id": user_id, "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == user_id
    assert len(body["recommendations"]) <= 10
    item_ids = [r["item_id"] for r in body["recommendations"]]
    assert len(item_ids) == len(set(item_ids))  # no duplicate items
    for r in body["recommendations"]:
        assert 0.0 <= r["score"]


def test_recommendations_diversity_cap_per_artist():
    user_id = _sample_user_id()
    resp = client.get("/api/v1/recommendations", params={"user_id": user_id, "limit": 10})
    body = resp.json()
    artists = [r["artist_name"] for r in body["recommendations"]]
    from collections import Counter

    counts = Counter(artists)
    assert max(counts.values()) <= 2  # diversity reranking caps at 2 per artist


def test_recommendations_unknown_user_404():
    resp = client.get("/api/v1/recommendations", params={"user_id": "does-not-exist"})
    assert resp.status_code == 404


def test_recommendations_novelty_param_changes_weights():
    user_id = _sample_user_id()
    resp = client.get("/api/v1/recommendations", params={"user_id": user_id, "limit": 5, "novelty": 0.9})
    assert resp.status_code == 200
    assert resp.json()["weights_used"]["novelty"] == 0.9


def test_recommendations_context_override():
    user_id = _sample_user_id()
    resp = client.get(
        "/api/v1/recommendations", params={"user_id": user_id, "limit": 5, "context": "Exploratory"}
    )
    assert resp.status_code == 200
    assert resp.json()["context_label"] == "Exploratory"


def test_recommendations_sparse_history_user_still_gets_results():
    # find the user with the fewest events and confirm the edge case works
    from app.ml.runtime import get_listening_events_df

    events = get_listening_events_df()
    sparse_user = events["user_id"].value_counts().idxmin()
    resp = client.get("/api/v1/recommendations", params={"user_id": sparse_user, "limit": 10})
    assert resp.status_code == 200
    assert len(resp.json()["recommendations"]) > 0

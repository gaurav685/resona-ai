import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from app.main import app
from app.ml.runtime import known_user_ids

client = TestClient(app)


def _sample_user_id() -> str:
    return sorted(known_user_ids())[0]


def _get_recommendations(user_id: str, limit: int = 10, **params):
    resp = client.get("/api/v1/recommendations", params={"user_id": user_id, "limit": limit, **params})
    assert resp.status_code == 200
    return resp.json()


# --- Part A/B: evidence + reason codes ---------------------------------

def test_recommendation_stores_evidence_and_reason_codes():
    user_id = _sample_user_id()
    body = _get_recommendations(user_id, limit=5)
    for item in body["recommendations"]:
        assert item["recommendation_id"]
        assert isinstance(item["reason_codes"], list) and len(item["reason_codes"]) > 0
        assert item["explanation"]


def test_reason_codes_only_from_real_evidence_thresholds():
    user_id = _sample_user_id()
    body = _get_recommendations(user_id, limit=10)
    for item in body["recommendations"]:
        bd = item["score_breakdown"]
        if "similar_to_recent_listening" in item["reason_codes"]:
            assert bd["co_listening_similarity"] >= 0.3
        if "exploration_candidate" in item["reason_codes"]:
            assert bd["novelty"] >= 0.6


def test_new_artist_claim_is_never_false():
    """Regression test for a real bug found during Phase 5 development:
    'introduces_new_artist' was based on top-10-familiar-artist membership,
    which mislabeled artists the user had genuinely played (just outside
    their top 10) as 'new'. Must use full play history."""
    user_id = _sample_user_id()
    body = _get_recommendations(user_id, limit=20)

    from app.ml.runtime import get_listening_events_df

    events = get_listening_events_df()
    played_artists = set(events[events["user_id"] == user_id]["artist_name"].unique())

    for item in body["recommendations"]:
        if "introduces_new_artist" in item["reason_codes"]:
            assert item["artist_name"] not in played_artists


# --- Part C: explanation API ---------------------------------------------

def test_explanation_endpoint_matches_stored_evidence():
    user_id = _sample_user_id()
    body = _get_recommendations(user_id, limit=1)
    rec_id = body["recommendations"][0]["recommendation_id"]

    resp = client.get(f"/api/v1/recommendations/{rec_id}/explanation")
    assert resp.status_code == 200
    explanation = resp.json()
    assert explanation["recommendation_id"] == rec_id
    assert explanation["explanation"]
    assert explanation["reason_codes"] == body["recommendations"][0]["reason_codes"]
    # unavailable evidence must stay explicitly unavailable, never fabricated
    assert explanation["evidence"]["genre_preference"] is None
    assert explanation["evidence"]["genre_preference_unavailable_reason"]
    assert explanation["evidence"]["energy_match"] is None
    assert explanation["evidence"]["personality_signal"] is None


def test_explanation_unknown_id_404_not_fabricated():
    resp = client.get("/api/v1/recommendations/does-not-exist/explanation")
    assert resp.status_code == 404
    assert "explanation" not in resp.json()  # no fabricated body on error


# --- Part D: feedback ------------------------------------------------------

def test_feedback_is_stored():
    user_id = _sample_user_id()
    body = _get_recommendations(user_id, limit=1)
    rec_id = body["recommendations"][0]["recommendation_id"]

    resp = client.post(f"/api/v1/recommendations/{rec_id}/feedback", json={"feedback_type": "like"})
    assert resp.status_code == 200
    fb = resp.json()
    assert fb["recommendation_id"] == rec_id
    assert fb["feedback_type"] == "like"
    assert fb["feedback_id"]


def test_feedback_invalid_type_422():
    user_id = _sample_user_id()
    body = _get_recommendations(user_id, limit=1)
    rec_id = body["recommendations"][0]["recommendation_id"]

    resp = client.post(f"/api/v1/recommendations/{rec_id}/feedback", json={"feedback_type": "love"})
    assert resp.status_code == 422


def test_feedback_unknown_recommendation_404():
    resp = client.post("/api/v1/recommendations/does-not-exist/feedback", json={"feedback_type": "like"})
    assert resp.status_code == 404


def test_hide_feedback_excludes_item_from_future_recommendations():
    user_id = _sample_user_id()
    before = _get_recommendations(user_id, limit=10)
    top_item = before["recommendations"][0]
    rec_id = top_item["recommendation_id"]

    resp = client.post(f"/api/v1/recommendations/{rec_id}/feedback", json={"feedback_type": "hide"})
    assert resp.status_code == 200

    after = _get_recommendations(user_id, limit=10)
    after_item_ids = [i["item_id"] for i in after["recommendations"]]
    assert top_item["item_id"] not in after_item_ids


def test_dislike_feedback_excludes_item_from_future_recommendations():
    user_id = _sample_user_id()
    before = _get_recommendations(user_id, limit=10)
    top_item = before["recommendations"][0]
    rec_id = top_item["recommendation_id"]

    resp = client.post(f"/api/v1/recommendations/{rec_id}/feedback", json={"feedback_type": "dislike"})
    assert resp.status_code == 200

    after = _get_recommendations(user_id, limit=10)
    after_item_ids = [i["item_id"] for i in after["recommendations"]]
    assert top_item["item_id"] not in after_item_ids


def test_like_feedback_does_not_hard_exclude():
    user_id = _sample_user_id()
    before = _get_recommendations(user_id, limit=1)
    rec_id = before["recommendations"][0]["recommendation_id"]

    resp = client.post(f"/api/v1/recommendations/{rec_id}/feedback", json={"feedback_type": "like"})
    assert resp.status_code == 200
    # liking doesn't exclude — a subsequent request should still succeed and
    # may include tracks by the same, now-boosted artist
    after = _get_recommendations(user_id, limit=10)
    assert len(after["recommendations"]) > 0

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from app.main import app
from app.ml.runtime import known_user_ids

client = TestClient(app)


def _sample_user_id() -> str:
    return sorted(known_user_ids())[0]


def test_users_list_returns_real_users():
    resp = client.get("/api/v1/users")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["users"]) == len(known_user_ids())
    ids = {u["user_id"] for u in body["users"]}
    assert _sample_user_id() in ids
    for u in body["users"]:
        assert u["n_events"] > 0


def test_listening_dna_includes_real_top_artists():
    user_id = _sample_user_id()
    resp = client.get(f"/api/v1/users/{user_id}/listening-dna")
    assert resp.status_code == 200
    top_artists = resp.json()["top_artists"]
    assert len(top_artists) > 0
    assert len(top_artists) <= 10
    counts = [a["play_count"] for a in top_artists]
    assert counts == sorted(counts, reverse=True)  # sorted descending, real counts


def test_taste_evolution_known_user():
    user_id = _sample_user_id()
    resp = client.get(f"/api/v1/users/{user_id}/taste-evolution")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == user_id
    assert len(body["periods"]) > 0
    for p in body["periods"]:
        assert p["n_events"] > 0
        assert 0.0 <= p["discovery_rate"] <= 1.0


def test_taste_evolution_unknown_user_404():
    resp = client.get("/api/v1/users/does-not-exist/taste-evolution")
    assert resp.status_code == 404


def test_personality_sample_participants_are_real():
    resp = client.get("/api/v1/personality/sample-participants")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["participants"]) > 0
    p = body["participants"][0]
    assert len(p["features"]) == 32
    assert set(p["actual_traits"].keys()) == {
        "Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism",
    }


def test_predict_using_real_sample_participant_features():
    participants = client.get("/api/v1/personality/sample-participants").json()["participants"]
    p = participants[0]
    resp = client.post("/api/v1/personality/predict", json={"features": p["features"]})
    assert resp.status_code == 200
    predictions = resp.json()["predictions"]
    assert len(predictions) == 5

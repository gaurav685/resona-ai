import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from app.main import app
from app.ml.runtime import known_user_ids

client = TestClient(app)


def _sample_user_id() -> str:
    return sorted(known_user_ids())[0]


def test_listening_dna_known_user():
    user_id = _sample_user_id()
    resp = client.get(f"/api/v1/users/{user_id}/listening-dna")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == user_id
    assert body["n_events"] > 0
    # unavailable audio features must be explicitly null with a reason, never fabricated
    assert body["energy"] is None
    assert body["energy_unavailable_reason"]


def test_listening_dna_unknown_user_404():
    resp = client.get("/api/v1/users/does-not-exist/listening-dna")
    assert resp.status_code == 404


def test_persona_known_user():
    user_id = _sample_user_id()
    resp = client.get(f"/api/v1/users/{user_id}/persona")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == user_id
    assert body["cluster_id"] >= 0
    assert body["persona_name"]
    assert body["algorithm"] == "KMeans"


def test_persona_unknown_user_404():
    resp = client.get("/api/v1/users/does-not-exist/persona")
    assert resp.status_code == 404


def test_personality_model_info():
    resp = client.get("/api/v1/personality/model-info")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["feature_columns"]) == 32
    assert body["trait_columns"] == [
        "Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism",
    ]


def test_personality_predict_missing_features_422():
    resp = client.post("/api/v1/personality/predict", json={"features": {"Q1": 3.0}})
    assert resp.status_code == 422


def test_personality_predict_valid():
    info = client.get("/api/v1/personality/model-info").json()
    features = {c: 3.0 for c in info["feature_columns"]}
    resp = client.post("/api/v1/personality/predict", json={"features": features})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["predictions"]) == 5
    assert "Model-estimated associations" in body["disclaimer"]
    for pred in body["predictions"]:
        assert isinstance(pred["score"], float)

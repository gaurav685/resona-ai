"""Phase 7 — full integration flow, chained against real local data and
real trained models, end to end:

User -> Listening Data -> Preprocessing -> Listening DNA -> Personality
Model -> Persona -> Current Context -> Recommendation Engine ->
Explanation -> User Feedback -> Updated Recommendations

Every step below calls a real endpoint backed by real artifacts on disk —
nothing here is mocked or fabricated. This is the single test that proves
the whole pipeline actually integrates, not just each piece in isolation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from fastapi.testclient import TestClient

from app.main import app
from app.ml.runtime import known_user_ids

client = TestClient(app)


def test_full_integration_flow_user_to_updated_recommendations():
    # 1. User + real listening data (preprocessing already ran in Phase 2;
    #    this confirms the processed data is actually reachable).
    user_id = sorted(known_user_ids())[0]
    users_resp = client.get("/api/v1/users")
    assert users_resp.status_code == 200
    assert any(u["user_id"] == user_id for u in users_resp.json()["users"])

    # 2. Listening DNA — real behavioral features from real events.
    dna_resp = client.get(f"/api/v1/users/{user_id}/listening-dna")
    assert dna_resp.status_code == 200
    dna = dna_resp.json()
    assert dna["n_events"] > 0
    assert len(dna["top_artists"]) > 0

    # 3. Personality model — no personality ground truth exists for Last.fm
    #    users, so this step is verified on a real research participant
    #    instead (the honest path established in Phase 6), proving the
    #    trained model actually loads and predicts.
    participants = client.get("/api/v1/personality/sample-participants").json()["participants"]
    assert len(participants) > 0
    predict_resp = client.post(
        "/api/v1/personality/predict", json={"features": participants[0]["features"]}
    )
    assert predict_resp.status_code == 200
    predictions = predict_resp.json()["predictions"]
    assert len(predictions) == 5
    assert all(isinstance(p["score"], float) for p in predictions)

    # 4. Persona — real KMeans cluster assignment (may be unavailable for
    #    a user below the minimum event threshold; both outcomes are real).
    persona_resp = client.get(f"/api/v1/users/{user_id}/persona")
    assert persona_resp.status_code in (200, 404)
    if persona_resp.status_code == 200:
        assert persona_resp.json()["persona_name"]

    # 5. Current context — real behavioral-shift classification.
    context_resp = client.get(f"/api/v1/users/{user_id}/current-context")
    assert context_resp.status_code == 200
    context = context_resp.json()
    assert context["context_label"] in ("Exploratory", "Focused", "Reflective", "Routine", "Unknown")

    # 6. Recommendation engine — real hybrid scoring using the above context.
    recs_resp = client.get("/api/v1/recommendations", params={"user_id": user_id, "limit": 10})
    assert recs_resp.status_code == 200
    recs = recs_resp.json()
    assert recs["context_label"] == context["context_label"]
    assert len(recs["recommendations"]) > 0
    top_item = recs["recommendations"][0]
    recommendation_id = top_item["recommendation_id"]

    # 7. Explanation — regenerated from the evidence persisted in step 6.
    explanation_resp = client.get(f"/api/v1/recommendations/{recommendation_id}/explanation")
    assert explanation_resp.status_code == 200
    explanation = explanation_resp.json()
    assert explanation["explanation"]
    assert explanation["reason_codes"] == top_item["reason_codes"]

    # 8. User feedback — hide this specific recommendation.
    feedback_resp = client.post(
        f"/api/v1/recommendations/{recommendation_id}/feedback", json={"feedback_type": "hide"}
    )
    assert feedback_resp.status_code == 200

    # 9. Updated recommendations — the hidden item must actually be gone.
    recs_after_resp = client.get("/api/v1/recommendations", params={"user_id": user_id, "limit": 10})
    assert recs_after_resp.status_code == 200
    after_item_ids = [r["item_id"] for r in recs_after_resp.json()["recommendations"]]
    assert top_item["item_id"] not in after_item_ids

"""Typed-ish HTTP client for the Resona AI FastAPI backend.

Mirrors apps/web/src/lib/api.ts endpoint-for-endpoint — same backend, same
contract, different frontend. No fabricated data: every function here is a
thin wrapper over a real HTTP call.
"""

from __future__ import annotations

import os
from typing import Any

import requests

API_URL = os.environ.get("RESONA_API_URL", "http://localhost:8000")


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _request(method: str, path: str, **kwargs) -> dict[str, Any]:
    try:
        resp = requests.request(method, f"{API_URL}{path}", timeout=15, **kwargs)
    except requests.RequestException as e:
        raise ApiError(0, f"Could not reach the Resona API at {API_URL} ({e}). Is the backend running?") from e
    if not resp.ok:
        detail = resp.reason
        try:
            body = resp.json()
            detail = body.get("detail", detail)
        except ValueError:
            pass
        raise ApiError(resp.status_code, detail)
    return resp.json()


def list_users() -> dict:
    return _request("GET", "/api/v1/users")


def get_listening_dna(user_id: str) -> dict:
    return _request("GET", f"/api/v1/users/{user_id}/listening-dna")


def get_persona(user_id: str) -> dict:
    return _request("GET", f"/api/v1/users/{user_id}/persona")


def get_current_context(user_id: str) -> dict:
    return _request("GET", f"/api/v1/users/{user_id}/current-context")


def get_taste_evolution(user_id: str) -> dict:
    return _request("GET", f"/api/v1/users/{user_id}/taste-evolution")


def get_personality_model_info() -> dict:
    return _request("GET", "/api/v1/personality/model-info")


def get_sample_participants() -> dict:
    return _request("GET", "/api/v1/personality/sample-participants")


def predict_personality(features: dict[str, float]) -> dict:
    return _request("POST", "/api/v1/personality/predict", json={"features": features})


def get_recommendations(
    user_id: str, limit: int = 10, novelty: float | None = None, context: str | None = None
) -> dict:
    params: dict[str, Any] = {"user_id": user_id, "limit": limit}
    if novelty is not None:
        params["novelty"] = novelty
    if context:
        params["context"] = context
    return _request("GET", "/api/v1/recommendations", params=params)


def get_explanation(recommendation_id: str) -> dict:
    return _request("GET", f"/api/v1/recommendations/{recommendation_id}/explanation")


def submit_feedback(recommendation_id: str, feedback_type: str) -> dict:
    return _request(
        "POST", f"/api/v1/recommendations/{recommendation_id}/feedback", json={"feedback_type": feedback_type}
    )


def get_similar_tracks(track_id: str, limit: int = 10) -> dict:
    return _request("GET", f"/api/v1/tracks/{track_id}/similar", params={"limit": limit})

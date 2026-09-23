from typing import Literal

from pydantic import BaseModel, ConfigDict


class SimilarTrack(BaseModel):
    track_id: str
    similarity: float


class SimilarTracksResponse(BaseModel):
    track_id: str
    similar_tracks: list[SimilarTrack]
    method: str


class ScoreBreakdown(BaseModel):
    co_listening_similarity: float
    artist_preference: float
    context_alignment: float
    novelty: float


class Evidence(BaseModel):
    co_listening_similarity: float
    artist_preference: float
    context_alignment: float
    novelty: float
    popularity: float
    is_new_artist: bool
    genre_preference: float | None = None
    genre_preference_unavailable_reason: str | None = None
    energy_match: float | None = None
    energy_match_unavailable_reason: str | None = None
    personality_signal: float | None = None
    personality_signal_unavailable_reason: str | None = None


class RecommendedItem(BaseModel):
    recommendation_id: str
    item_id: str
    artist_name: str
    track_title: str
    score: float
    score_breakdown: ScoreBreakdown
    popularity: float
    reason_codes: list[str]
    explanation: str


class RecommendationsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    context_label: str
    weights_used: dict[str, float]
    recommendations: list[RecommendedItem]
    note: str


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    recommendation_id: str
    user_id: str
    item_id: str
    artist_name: str
    track_title: str
    context_label: str
    evidence: Evidence
    reason_codes: list[str]
    explanation: str
    model_version: str


FeedbackType = Literal["like", "dislike", "skip", "save", "replay", "hide"]


class FeedbackRequest(BaseModel):
    feedback_type: FeedbackType


class FeedbackResponse(BaseModel):
    feedback_id: str
    recommendation_id: str
    user_id: str
    feedback_type: FeedbackType
    note: str

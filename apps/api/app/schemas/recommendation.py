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


class RecommendedItem(BaseModel):
    item_id: str
    artist_name: str
    track_title: str
    score: float
    score_breakdown: ScoreBreakdown
    popularity: float


class RecommendationsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    context_label: str
    weights_used: dict[str, float]
    recommendations: list[RecommendedItem]
    note: str

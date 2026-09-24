from pydantic import BaseModel, ConfigDict

from app.schemas.context import ContextResponse
from app.schemas.listening_dna import ListeningDNAResponse
from app.schemas.recommendation import RecommendationsResponse
from app.schemas.taste_evolution import TasteEvolutionResponse


class UploadAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_user_id: str
    service: str
    n_files: int
    n_events_parsed: int
    n_tracks_matched_catalog: int
    n_distinct_tracks: int
    parse_errors: dict[str, str]
    listening_dna: ListeningDNAResponse
    current_context: ContextResponse
    taste_evolution: TasteEvolutionResponse
    recommendations: RecommendationsResponse | None
    note: str

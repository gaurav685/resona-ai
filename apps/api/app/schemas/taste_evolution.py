from pydantic import BaseModel


class TastePeriod(BaseModel):
    period: str
    n_events: int
    unique_artists: int
    artist_diversity: float | None
    discovery_rate: float | None
    listening_frequency: float


class TasteEvolutionResponse(BaseModel):
    user_id: str
    periods: list[TastePeriod]

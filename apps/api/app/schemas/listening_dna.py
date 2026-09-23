from pydantic import BaseModel


class TopArtist(BaseModel):
    artist_name: str
    play_count: int


class ListeningDNAResponse(BaseModel):
    user_id: str
    n_events: int
    n_sessions: int
    top_artists: list[TopArtist]
    listening_frequency: float | None
    average_session_duration_min: float | None
    tracks_per_session: float | None
    replay_rate: float | None
    repeat_rate: float | None
    artist_diversity: float | None
    artist_concentration: float | None
    discovery_rate: float | None
    night_listening_ratio_utc: float | None
    weekend_listening_ratio_utc: float | None
    completion_rate: float | None
    completion_rate_unavailable_reason: str | None = None
    skip_rate: float | None
    skip_rate_unavailable_reason: str | None = None
    genre_diversity: float | None
    genre_diversity_unavailable_reason: str | None = None
    genre_concentration: float | None
    genre_concentration_unavailable_reason: str | None = None
    energy: float | None
    energy_unavailable_reason: str | None = None
    valence: float | None
    valence_unavailable_reason: str | None = None
    danceability: float | None
    danceability_unavailable_reason: str | None = None
    tempo: float | None
    tempo_unavailable_reason: str | None = None
    acousticness: float | None
    acousticness_unavailable_reason: str | None = None
    instrumentalness: float | None
    instrumentalness_unavailable_reason: str | None = None
    speechiness: float | None
    speechiness_unavailable_reason: str | None = None

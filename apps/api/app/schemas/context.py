from pydantic import BaseModel


class WindowStats(BaseModel):
    n_events: int
    artist_diversity: float | None = None
    repeat_rate: float | None = None
    artist_shift: float | None = None
    avg_gap_sec: float | None = None
    night_ratio: float | None = None


class ContextResponse(BaseModel):
    user_id: str
    windows: dict[str, WindowStats]
    baseline: dict
    shifts: dict
    context_label: str
    context_explanation: str
    disclaimer: str

from pydantic import BaseModel, ConfigDict, Field


class PersonalityPredictRequest(BaseModel):
    features: dict[str, float] = Field(
        description=(
            "Named input features expected by the trained model (29 mean "
            "audio/emotion features + Q1/Q2/Q3 music-attitude ratings — see "
            "GET /api/v1/personality/model-info for the exact required set)."
        )
    )


class TraitPrediction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    trait: str
    score: float
    confidence: float | None
    confidence_note: str | None
    model_version: str
    important_features: list[dict]


class PersonalityPredictResponse(BaseModel):
    predictions: list[TraitPrediction]
    disclaimer: str


class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_type: str
    model_version: str
    feature_columns: list[str]
    trait_columns: list[str]


class SampleParticipant(BaseModel):
    participant_id: str
    features: dict[str, float]
    actual_traits: dict[str, float]


class SampleParticipantsResponse(BaseModel):
    participants: list[SampleParticipant]
    note: str

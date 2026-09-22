from fastapi import APIRouter, HTTPException

from app.ml.runtime import ArtifactUnavailable, get_personality_model_info, predict_personality
from app.schemas.personality import (
    ModelInfoResponse,
    PersonalityPredictRequest,
    PersonalityPredictResponse,
)

router = APIRouter(prefix="/personality", tags=["personality"])


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    try:
        info = get_personality_model_info()
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return ModelInfoResponse(
        model_type=info["model_type"],
        model_version=info["model_version"],
        feature_columns=info["feature_columns"],
        trait_columns=info["trait_columns"],
    )


@router.post("/predict", response_model=PersonalityPredictResponse)
def predict(request: PersonalityPredictRequest) -> PersonalityPredictResponse:
    try:
        result = predict_personality(request.features)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return PersonalityPredictResponse(**result)

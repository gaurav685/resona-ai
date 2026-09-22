from fastapi import APIRouter, HTTPException, Query

from app.ml.runtime import ArtifactUnavailable, get_recommendations
from app.schemas.recommendation import RecommendationsResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationsResponse)
def recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    novelty: float | None = Query(default=None, ge=0.0, le=1.0),
    context: str | None = Query(default=None, description="Override auto-detected context label"),
) -> RecommendationsResponse:
    try:
        result = get_recommendations(user_id, limit=limit, novelty=novelty, context=context)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RecommendationsResponse(**result)

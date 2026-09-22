from fastapi import APIRouter, HTTPException, Query

from app.ml.runtime import ArtifactUnavailable, get_similar_tracks
from app.schemas.recommendation import SimilarTracksResponse

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("/{track_id}/similar", response_model=SimilarTracksResponse)
def similar_tracks(track_id: str, limit: int = Query(default=10, ge=1, le=50)) -> SimilarTracksResponse:
    try:
        result = get_similar_tracks(track_id, limit=limit)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return SimilarTracksResponse(**result)

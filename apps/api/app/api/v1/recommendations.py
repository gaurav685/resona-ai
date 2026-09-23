import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ml.runtime import ArtifactUnavailable, get_recommendations
from app.models.recommendation_log import RecommendationFeedback, RecommendationLog
from app.schemas.recommendation import (
    ExplanationResponse,
    FeedbackRequest,
    FeedbackResponse,
    RecommendationsResponse,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "ml" / "recommendation"))
from evidence import generate_explanation  # noqa: E402

MODEL_VERSION = "hybrid-v1"

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _feedback_rows_for_user(db: Session, user_id: str) -> list[dict]:
    rows = (
        db.query(
            RecommendationFeedback.feedback_type,
            RecommendationLog.item_id,
            RecommendationLog.artist_name,
        )
        .join(RecommendationLog, RecommendationFeedback.recommendation_id == RecommendationLog.id)
        .filter(RecommendationFeedback.user_id == user_id)
        .all()
    )
    return [{"feedback_type": r.feedback_type, "item_id": r.item_id, "artist_name": r.artist_name} for r in rows]


@router.get("", response_model=RecommendationsResponse)
def recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    novelty: float | None = Query(default=None, ge=0.0, le=1.0),
    context: str | None = Query(default=None, description="Override auto-detected context label"),
    db: Session = Depends(get_db),
) -> RecommendationsResponse:
    feedback_rows = _feedback_rows_for_user(db, user_id)
    try:
        result = get_recommendations(
            user_id, limit=limit, novelty=novelty, context=context, feedback_rows=feedback_rows
        )
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    persisted = []
    for item in result["recommendations"]:
        log = RecommendationLog(
            user_id=user_id,
            item_id=item["item_id"],
            artist_name=item["artist_name"],
            track_title=item["track_title"],
            score=item["score"],
            score_breakdown=item["score_breakdown"],
            context_label=result["context_label"],
            reason_codes=item["reason_codes"],
            evidence=item["evidence"],
            model_version=MODEL_VERSION,
        )
        db.add(log)
        db.flush()  # assigns log.id without ending the transaction
        item["recommendation_id"] = log.id
        persisted.append(item)
    db.commit()

    result["recommendations"] = persisted
    return RecommendationsResponse(**result)


@router.get("/{recommendation_id}/explanation", response_model=ExplanationResponse)
def explanation(recommendation_id: str, db: Session = Depends(get_db)) -> ExplanationResponse:
    log = db.get(RecommendationLog, recommendation_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"unknown recommendation_id: {recommendation_id}")

    # Regenerated from the stored evidence at read time — proves the
    # explanation is derived from persisted evidence, not a cached string
    # that could drift from it.
    explanation_text = generate_explanation(
        log.evidence, log.reason_codes, log.context_label, log.artist_name, log.track_title
    )
    return ExplanationResponse(
        recommendation_id=log.id,
        user_id=log.user_id,
        item_id=log.item_id,
        artist_name=log.artist_name,
        track_title=log.track_title,
        context_label=log.context_label,
        evidence=log.evidence,
        reason_codes=log.reason_codes,
        explanation=explanation_text,
        model_version=log.model_version,
    )


@router.post("/{recommendation_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    recommendation_id: str, request: FeedbackRequest, db: Session = Depends(get_db)
) -> FeedbackResponse:
    log = db.get(RecommendationLog, recommendation_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"unknown recommendation_id: {recommendation_id}")

    entry = RecommendationFeedback(
        recommendation_id=recommendation_id,
        user_id=log.user_id,
        feedback_type=request.feedback_type,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return FeedbackResponse(
        feedback_id=entry.id,
        recommendation_id=recommendation_id,
        user_id=log.user_id,
        feedback_type=request.feedback_type,
        note=(
            "Recorded. Future GET /api/v1/recommendations calls for this user will apply a "
            "feedback-derived artist preference adjustment; 'dislike'/'hide' also exclude this "
            "specific item from future candidate pools."
        ),
    )

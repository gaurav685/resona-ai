"""Shared by app/api/v1/recommendations.py and app/api/v1/uploads.py: both
need to persist a hybrid.recommend() result's items as RecommendationLog
rows (assigning each a real recommendation_id) before returning them, so
GET .../explanation and POST .../feedback work for either source."""

from sqlalchemy.orm import Session

from app.models.recommendation_log import RecommendationLog

MODEL_VERSION = "hybrid-v1"


def persist_recommendations(db: Session, user_id: str, result: dict) -> dict:
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
    return result

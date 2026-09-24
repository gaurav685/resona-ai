from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ml.runtime import ArtifactUnavailable, analyze_uploaded_history
from app.schemas.upload import UploadAnalysisResponse
from app.services.recommendation_persistence import persist_recommendations

router = APIRouter(prefix="/uploads", tags=["uploads"])

Service = Literal["spotify", "youtube_music", "apple_music"]


@router.post("/analyze", response_model=UploadAnalysisResponse)
async def analyze(
    service: Service = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> UploadAnalysisResponse:
    if not files:
        raise HTTPException(status_code=422, detail="no files uploaded")

    file_bytes = [(f.filename or "upload", await f.read()) for f in files]

    try:
        result = analyze_uploaded_history(file_bytes, service)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if result["recommendations"]:
        result["recommendations"] = persist_recommendations(
            db, result["session_user_id"], result["recommendations"]
        )

    return UploadAnalysisResponse(**result)

from fastapi import APIRouter, HTTPException

from app.ml.runtime import ArtifactUnavailable, get_listening_dna, get_persona
from app.schemas.listening_dna import ListeningDNAResponse
from app.schemas.persona import PersonaResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/listening-dna", response_model=ListeningDNAResponse)
def listening_dna(user_id: str) -> ListeningDNAResponse:
    try:
        dna = get_listening_dna(user_id)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ListeningDNAResponse(**dna)


@router.get("/{user_id}/persona", response_model=PersonaResponse)
def persona(user_id: str) -> PersonaResponse:
    try:
        result = get_persona(user_id)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return PersonaResponse(**result)

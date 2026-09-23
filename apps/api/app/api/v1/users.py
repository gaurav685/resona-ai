from fastapi import APIRouter, HTTPException

from app.ml.runtime import (
    ArtifactUnavailable,
    get_current_context,
    get_listening_dna,
    get_persona,
    get_taste_evolution,
    list_users,
)
from app.schemas.context import ContextResponse
from app.schemas.listening_dna import ListeningDNAResponse
from app.schemas.persona import PersonaResponse
from app.schemas.taste_evolution import TasteEvolutionResponse
from app.schemas.user_list import UserListResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def users() -> UserListResponse:
    return UserListResponse(users=list_users())


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


@router.get("/{user_id}/current-context", response_model=ContextResponse)
def current_context(user_id: str) -> ContextResponse:
    try:
        result = get_current_context(user_id)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ContextResponse(**result)


@router.get("/{user_id}/taste-evolution", response_model=TasteEvolutionResponse)
def taste_evolution(user_id: str) -> TasteEvolutionResponse:
    try:
        result = get_taste_evolution(user_id)
    except ArtifactUnavailable as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return TasteEvolutionResponse(**result)

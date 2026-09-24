from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.personality import router as personality_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.tracks import router as tracks_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(users_router)
api_router.include_router(personality_router)
api_router.include_router(tracks_router)
api_router.include_router(recommendations_router)
api_router.include_router(uploads_router)

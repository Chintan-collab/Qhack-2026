from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.agents import router as agents_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.projects import router as projects_router

router = APIRouter()
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(agents_router, prefix="/agents", tags=["agents"])
router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])

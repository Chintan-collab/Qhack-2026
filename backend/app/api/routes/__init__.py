from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.agents import router as agents_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.deliverables import router as deliverables_router
from app.api.routes.projects import router as projects_router
from app.api.routes.voice import router as voice_router

router = APIRouter()
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(agents_router, prefix="/agents", tags=["agents"])
router.include_router(
    conversations_router,
    prefix="/conversations",
    tags=["conversations"],
)
router.include_router(
    deliverables_router,
    prefix="/deliverables",
    tags=["deliverables"],
)
router.include_router(
    projects_router, prefix="/projects", tags=["projects"]
)
router.include_router(
    voice_router, prefix="/voice", tags=["voice"]
)

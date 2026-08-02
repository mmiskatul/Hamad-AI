from fastapi import APIRouter

from app.api.v1.endpoints import agents, chat, files, health, models, rag, voice

router = APIRouter()
router.include_router(health.router)
router.include_router(chat.router)
router.include_router(models.router)
router.include_router(voice.router)
router.include_router(rag.router)
router.include_router(agents.router)
router.include_router(files.router)

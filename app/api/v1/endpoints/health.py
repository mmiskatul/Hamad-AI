from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_model_router
from app.services.model_router import ConfiguredModelRouter

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/health/live")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "oneai-hub-fastapi"}


@router.get("/health/ready")
async def readiness(
    model_router: Annotated[ConfiguredModelRouter, Depends(get_model_router)],
) -> dict[str, str | int]:
    models = await model_router.list_models()
    available = sum(1 for model in models if model.available)
    if available == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "NO_AI_PROVIDER",
                "message": "No AI provider API key is configured.",
            },
        )
    return {"status": "ready", "service": "oneai-hub-fastapi", "models": available}

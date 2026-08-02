from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_model_router
from app.schemas.ai import ModelListResponse
from app.services.model_router import ConfiguredModelRouter

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ModelListResponse)
async def models(
    model_router: Annotated[ConfiguredModelRouter, Depends(get_model_router)],
) -> ModelListResponse:
    return ModelListResponse(models=await model_router.list_models())

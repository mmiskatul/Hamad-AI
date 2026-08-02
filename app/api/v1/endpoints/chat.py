from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_model_router
from app.schemas.ai import ModelListResponse
from app.schemas.chat import (
    ChatCompletionResponse,
    ChatRequest,
    ConversationCreate,
    ConversationMessage,
)
from app.services.conversation_service import ConversationService
from app.services.model_router import (
    ConfiguredModelRouter,
    ModelUnavailableError,
    ProviderRequestError,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    model_router: Annotated[ConfiguredModelRouter, Depends(get_model_router)],
) -> ModelListResponse:
    return ModelListResponse(models=await model_router.list_models())


@router.post("/responses", response_model=ChatCompletionResponse)
async def create_response(
    request: ChatRequest,
    model_router: Annotated[ConfiguredModelRouter, Depends(get_model_router)],
) -> ChatCompletionResponse:
    try:
        return await ConversationService(model_router).generate_response(request)
    except ModelUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "MODEL_UNAVAILABLE", "message": str(error)},
        ) from error
    except ProviderRequestError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "PROVIDER_REQUEST_FAILED", "message": str(error)},
        ) from error


@router.post("/conversations", response_model=dict)
async def create_conversation(_: ConversationCreate) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Conversation persistence is owned by the Fastify backend.",
    )


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationMessage)
async def append_message(conversation_id: str, _: ConversationMessage) -> ConversationMessage:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Conversation {conversation_id} is owned by the Fastify backend.",
    )

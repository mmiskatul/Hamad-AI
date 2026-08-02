from time import time

from app.schemas.ai import GenerateRequest, GenerateResponse
from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionResponse,
    ChatRequest,
    ConversationMessage,
)
from app.services.model_router import ModelRouter


class ConversationService:
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router

    async def generate_response(self, request: ChatRequest) -> ChatCompletionResponse:
        generated = await self.model_router.generate(
            GenerateRequest(
                model_id=request.model_id,
                messages=request.messages,
                response_language=request.response_language,
                memory=request.memory,
            )
        )
        return ChatCompletionResponse(
            id=generated.id.replace("resp_", "chatcmpl_", 1),
            created=int(time()),
            model=generated.configured_model,
            model_id=generated.model_id,
            provider=generated.provider,
            configured_model=generated.configured_model,
            choices=[
                ChatCompletionChoice(
                    message=ConversationMessage(role="assistant", content=generated.content)
                )
            ],
            usage=generated.usage,
        )

    async def generate_stateless(self, request: GenerateRequest) -> GenerateResponse:
        return await self.model_router.generate(request)

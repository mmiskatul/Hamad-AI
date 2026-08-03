from typing import Literal

from pydantic import Field

from app.schemas.chat import ChatMessage, ResponseLanguage
from app.schemas.common import ApiModel, GeneratedImage, TokenUsage, UserMemory


class ModelInfo(ApiModel):
    id: str
    name: str
    vendor: str
    min_plan: Literal["free", "pro", "business"]
    available: bool
    configured_model: str


class ModelListResponse(ApiModel):
    models: list[ModelInfo] = Field(default_factory=list)


class GenerateRequest(ApiModel):
    model_id: str
    messages: list[ChatMessage] = Field(min_length=1)
    response_language: ResponseLanguage = "auto"
    memory: UserMemory | None = None


class GenerateResponse(ApiModel):
    id: str
    object: Literal["response"] = "response"
    created_at: str
    model_id: str
    provider: str
    configured_model: str
    content: str
    generated_images: list[GeneratedImage] = Field(default_factory=list)
    usage: TokenUsage | None = None

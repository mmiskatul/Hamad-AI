from typing import Literal

from pydantic import Field

from app.schemas.common import ApiModel, TokenUsage, UserMemory

ChatRole = Literal["system", "user", "assistant"]
ResponseLanguage = Literal["auto", "en", "ar", "both"]


class ChatMessage(ApiModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=50_000)


class ChatRequest(ApiModel):
    model_id: str
    messages: list[ChatMessage] = Field(min_length=1)
    response_language: ResponseLanguage = "auto"
    memory: UserMemory | None = None


class ConversationCreate(ApiModel):
    title: str | None = None
    model_id: str
    response_language: ResponseLanguage = "auto"


class ConversationMessage(ApiModel):
    id: str | None = None
    role: ChatRole
    content: str


class ChatCompletionChoice(ApiModel):
    index: int = 0
    message: ConversationMessage
    finish_reason: Literal["stop"] = "stop"


class ChatCompletionResponse(ApiModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    model_id: str
    provider: str
    configured_model: str
    choices: list[ChatCompletionChoice]
    usage: TokenUsage | None = None

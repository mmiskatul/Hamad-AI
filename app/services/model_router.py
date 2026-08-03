import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import uuid4

import httpx

from app.core.config import Settings, settings
from app.schemas.ai import GenerateRequest, GenerateResponse, ModelInfo
from app.schemas.common import GeneratedImage, TokenUsage

ProviderId = Literal["gpt", "deepseek", "gemini", "perplexity", "claude", "grok"]
ProviderKind = Literal["openai", "openai-compatible", "anthropic", "gemini", "perplexity"]
PlanId = Literal["free", "pro", "business"]


@dataclass(slots=True)
class ProviderConfig:
    id: ProviderId
    name: str
    vendor: str
    kind: ProviderKind
    base_url: str
    api_key: str
    model: str
    min_plan: PlanId
    enabled: bool
    image_model: str = "gpt-image-2"


class ModelUnavailableError(Exception):
    def __init__(self, model_id: str):
        self.model_id = model_id
        super().__init__(f"{model_id} is not configured in the AI service.")


class ProviderRequestError(Exception):
    def __init__(
        self, provider: str, message: str = "The AI provider could not complete the request."
    ):
        self.provider = provider
        super().__init__(message)


class ModelRouter(Protocol):
    async def list_models(self) -> list[ModelInfo]: ...

    async def generate(self, request: GenerateRequest) -> GenerateResponse: ...


class ConfiguredModelRouter:
    def __init__(self, providers: list[ProviderConfig], client: httpx.AsyncClient | None = None):
        self.providers = providers
        self.client = client

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id=provider.id,
                name=provider.name,
                vendor=provider.vendor,
                min_plan=provider.min_plan,
                available=provider.enabled and bool(provider.api_key.strip()),
                configured_model=provider.model,
            )
            for provider in self.providers
        ]

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        provider = next((item for item in self.providers if item.id == request.model_id), None)
        if provider is None or not provider.enabled or not provider.api_key.strip():
            raise ModelUnavailableError(request.model_id)

        response_provider = provider
        configured_model = provider.model
        image_request = _is_image_generation_request(request)
        try:
            if image_request:
                image_provider = next(
                    (
                        item
                        for item in self.providers
                        if item.kind == "openai" and item.enabled and item.api_key.strip()
                    ),
                    None,
                )
                if image_provider is None:
                    raise ProviderRequestError(
                        "OpenAI", "Image generation is unavailable because OPENAI_API_KEY is not configured."
                    )
                response_provider = image_provider
                configured_model = image_provider.image_model
                if self.client is not None:
                    result = await _request_openai_image(self.client, image_provider, request)
                else:
                    timeout = httpx.Timeout(settings.model_router_timeout_seconds)
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        result = await _request_openai_image(client, image_provider, request)
            if self.client is not None:
                if not image_request:
                    result = await self._generate_with_client(self.client, provider, request)
            elif not image_request:
                timeout = httpx.Timeout(settings.model_router_timeout_seconds)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    result = await self._generate_with_client(client, provider, request)
        except (ModelUnavailableError, ProviderRequestError):
            raise
        except (httpx.HTTPError, ValueError) as error:
            raise ProviderRequestError(provider.vendor) from error

        content, usage, generated_images = result
        if not content.strip() and not generated_images:
            raise ProviderRequestError(
                provider.vendor, "The AI provider returned an empty response."
            )
        return GenerateResponse(
            id=f"resp_{uuid4()}",
            created_at=datetime.now(UTC).isoformat(),
            model_id=provider.id,
            provider=response_provider.vendor,
            configured_model=configured_model,
            content=content.strip() or "Here is your generated image.",
            generated_images=generated_images,
            usage=usage,
        )

    async def _generate_with_client(
        self,
        client: httpx.AsyncClient,
        provider: ProviderConfig,
        request: GenerateRequest,
    ) -> tuple[str, TokenUsage | None, list[GeneratedImage]]:
        if provider.kind == "openai":
            return await _request_openai(client, provider, request)
        if provider.kind == "anthropic":
            return await _request_anthropic(client, provider, request)
        if provider.kind == "gemini":
            return await _request_gemini(client, provider, request)
        if provider.kind == "perplexity":
            return await _request_perplexity(client, provider, request)
        return await _request_openai_compatible(client, provider, request)


def _language_instruction(language: str) -> str:
    instructions = {
        "auto": "Reply in the language of the user's latest message.",
        "en": "Reply in English.",
        "ar": "Reply in Arabic.",
        "both": "Reply in English first, then repeat the answer in Arabic under an Arabic heading.",
    }
    return f"{instructions[language]} Preserve code, commands, URLs, API names, and identifiers exactly."


def _system_instruction(request: GenerateRequest) -> str:
    base = f"You are OneAI Hub, a helpful assistant. {_language_instruction(request.response_language)}"
    if request.memory is None:
        return base
    details = [
        f"Preferred name: {request.memory.nickname}" if request.memory.nickname else "",
        f"Occupation: {request.memory.occupation}" if request.memory.occupation else "",
        f"About the user: {request.memory.about}" if request.memory.about else "",
        f"Saved memory: {request.memory.summary}" if request.memory.summary else "",
    ]
    memory = "\n".join(item for item in details if item)
    return (
        f"{base}\nUse the following user memory only when relevant:\n{memory}" if memory else base
    )


def _auth_headers(provider: ProviderConfig) -> dict[str, str]:
    return {"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"}


def _is_image_generation_request(request: GenerateRequest) -> bool:
    latest = next(
        (message.content.lower() for message in reversed(request.messages) if message.role == "user"),
        "",
    )
    action = re.search(r"\b(generate|create|make|draw|paint|render|design|produce)\b", latest)
    subject = re.search(r"\b(image|images|picture|pictures|photo|photos|illustration|artwork)\b", latest)
    arabic = re.search(r"(ارسم|أنشئ|انشئ|ولّد|ولد|توليد).{0,30}(صورة|صور|رسمة)", latest)
    return bool((action and subject) or arabic)


async def _request_openai_image(
    client: httpx.AsyncClient,
    provider: ProviderConfig,
    request: GenerateRequest,
) -> tuple[str, TokenUsage | None, list[GeneratedImage]]:
    prompt = next(
        (message.content for message in reversed(request.messages) if message.role == "user"),
        "",
    )
    response = await client.post(
        f"{provider.base_url.rstrip('/')}/images/generations",
        headers=_auth_headers(provider),
        json={
            "model": provider.image_model,
            "prompt": prompt,
            "quality": "low",
            "size": "1024x1024",
            "output_format": "png",
        },
    )
    body = _response_json(response, provider.vendor)
    images = [
        GeneratedImage(mime_type="image/png", data_base64=item["b64_json"])
        for item in body.get("data", [])
        if item.get("b64_json")
    ]
    return "Here is your generated image.", _token_usage(body.get("usage")), images


async def _request_openai(
    client: httpx.AsyncClient,
    provider: ProviderConfig,
    request: GenerateRequest,
) -> tuple[str, TokenUsage | None, list[GeneratedImage]]:
    response = await client.post(
        f"{provider.base_url.rstrip('/')}/responses",
        headers=_auth_headers(provider),
        json={
            "model": provider.model,
            "instructions": (
                f"{_system_instruction(request)}\n"
                "When the user asks to create, generate, or edit an image, use the "
                "image_generation tool and return the generated image instead of only "
                "describing a prompt for another tool."
            ),
            "input": [
                message.model_dump() for message in request.messages if message.role != "system"
            ],
            "text": {"verbosity": "medium"},
            "tools": [{"type": "image_generation"}],
        },
    )
    body = _response_json(response, provider.vendor)
    content = body.get("output_text") or "".join(
        part.get("text", "")
        for item in body.get("output", [])
        if item.get("type") == "message"
        for part in item.get("content", [])
        if part.get("type") == "output_text"
    )
    images = [
        GeneratedImage(mime_type="image/png", data_base64=item["result"])
        for item in body.get("output", [])
        if item.get("type") == "image_generation_call" and item.get("result")
    ]
    return content, _token_usage(body.get("usage")), images


async def _request_openai_compatible(
    client: httpx.AsyncClient,
    provider: ProviderConfig,
    request: GenerateRequest,
) -> tuple[str, TokenUsage | None, list[GeneratedImage]]:
    messages = [{"role": "system", "content": _system_instruction(request)}]
    messages.extend(message.model_dump() for message in request.messages)
    response = await client.post(
        f"{provider.base_url.rstrip('/')}/chat/completions",
        headers=_auth_headers(provider),
        json={"model": provider.model, "messages": messages},
    )
    body = _response_json(response, provider.vendor)
    choices = body.get("choices", [])
    content = choices[0].get("message", {}).get("content", "") if choices else ""
    return content, _token_usage(body.get("usage"), chat_completions=True), []


async def _request_perplexity(
    client: httpx.AsyncClient,
    provider: ProviderConfig,
    request: GenerateRequest,
) -> tuple[str, TokenUsage | None, list[GeneratedImage]]:
    messages = [{"role": "system", "content": _system_instruction(request)}]
    messages.extend(message.model_dump() for message in request.messages)
    response = await client.post(
        f"{provider.base_url.rstrip('/')}/chat/completions",
        headers=_auth_headers(provider),
        json={"model": provider.model, "messages": messages},
    )
    body = _response_json(response, provider.vendor)
    choices = body.get("choices", [])
    content = choices[0].get("message", {}).get("content", "") if choices else ""
    return content, _token_usage(body.get("usage"), chat_completions=True), []


async def _request_anthropic(
    client: httpx.AsyncClient,
    provider: ProviderConfig,
    request: GenerateRequest,
) -> tuple[str, TokenUsage | None, list[GeneratedImage]]:
    response = await client.post(
        f"{provider.base_url.rstrip('/')}/messages",
        headers={
            "x-api-key": provider.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": provider.model,
            "max_tokens": 4096,
            "system": _system_instruction(request),
            "messages": [
                message.model_dump() for message in request.messages if message.role != "system"
            ],
        },
    )
    body = _response_json(response, provider.vendor)
    content = "".join(
        part.get("text", "") for part in body.get("content", []) if part.get("type") == "text"
    )
    usage = body.get("usage")
    if usage:
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        return content, TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        ), []
    return content, None, []


async def _request_gemini(
    client: httpx.AsyncClient,
    provider: ProviderConfig,
    request: GenerateRequest,
) -> tuple[str, TokenUsage | None, list[GeneratedImage]]:
    response = await client.post(
        f"{provider.base_url.rstrip('/')}/models/{provider.model}:generateContent",
        params={"key": provider.api_key},
        json={
            "systemInstruction": {"parts": [{"text": _system_instruction(request)}]},
            "contents": [
                {
                    "role": "model" if message.role == "assistant" else "user",
                    "parts": [{"text": message.content}],
                }
                for message in request.messages
                if message.role != "system"
            ],
        },
    )
    body = _response_json(response, provider.vendor)
    candidates = body.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    content = "".join(part.get("text", "") for part in parts)
    metadata = body.get("usageMetadata")
    if metadata:
        return content, TokenUsage(
            input_tokens=int(metadata.get("promptTokenCount", 0)),
            output_tokens=int(metadata.get("candidatesTokenCount", 0)),
            total_tokens=int(metadata.get("totalTokenCount", 0)),
        ), []
    return content, None, []


def _response_json(response: httpx.Response, provider: str) -> dict:
    try:
        body = response.json()
    except ValueError as decode_error:
        raise ProviderRequestError(
            provider, "The AI provider returned an invalid response."
        ) from decode_error
    if response.is_error:
        error_detail = body.get("error") or body.get("detail") or {}
        message = (
            error_detail.get("message") if isinstance(error_detail, dict) else str(error_detail)
        )
        raise ProviderRequestError(provider, message or "The AI provider rejected the request.")
    return body


def _token_usage(usage: dict | None, *, chat_completions: bool = False) -> TokenUsage | None:
    if not usage:
        return None
    input_key = "prompt_tokens" if chat_completions else "input_tokens"
    output_key = "completion_tokens" if chat_completions else "output_tokens"
    input_tokens = int(usage.get(input_key, 0))
    output_tokens = int(usage.get(output_key, 0))
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=int(usage.get("total_tokens", input_tokens + output_tokens)),
    )


def create_model_router(config: Settings | None = None) -> ConfiguredModelRouter:
    configured = config or settings
    return ConfiguredModelRouter(
        providers=[
            ProviderConfig(
                "gpt",
                "ChatGPT",
                "OpenAI",
                "openai",
                configured.openai_base_url,
                configured.openai_api_key,
                configured.openai_model,
                "free",
                bool(configured.openai_api_key.strip()),
                configured.openai_image_model,
            ),
            ProviderConfig(
                "deepseek",
                "DeepSeek",
                "DeepSeek",
                "openai-compatible",
                configured.deepseek_base_url,
                configured.deepseek_api_key,
                configured.deepseek_model,
                "free",
                bool(configured.deepseek_api_key.strip()),
            ),
            ProviderConfig(
                "gemini",
                "Gemini",
                "Google",
                "gemini",
                configured.gemini_base_url,
                configured.gemini_api_key,
                configured.gemini_model,
                "pro",
                bool(configured.gemini_api_key.strip()),
            ),
            ProviderConfig(
                "perplexity",
                "Perplexity",
                "Perplexity",
                "perplexity",
                configured.perplexity_base_url,
                configured.perplexity_api_key,
                configured.perplexity_model,
                "pro",
                bool(configured.perplexity_api_key.strip()),
            ),
            ProviderConfig(
                "claude",
                "Claude",
                "Anthropic",
                "anthropic",
                configured.anthropic_base_url,
                configured.anthropic_api_key,
                configured.anthropic_model,
                "business",
                bool(configured.anthropic_api_key.strip()),
            ),
            ProviderConfig(
                "grok",
                "Grok",
                "xAI",
                "openai-compatible",
                configured.xai_base_url,
                configured.xai_api_key,
                configured.xai_model,
                "business",
                bool(configured.xai_api_key.strip()),
            ),
        ]
    )

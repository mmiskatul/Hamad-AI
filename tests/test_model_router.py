import json

import httpx
import pytest

from app.core.config import Settings
from app.schemas.ai import GenerateRequest
from app.schemas.chat import ChatMessage
from app.services.model_router import (
    ConfiguredModelRouter,
    ModelUnavailableError,
    ProviderConfig,
    create_model_router,
)


@pytest.mark.asyncio
async def test_openai_responses_generation_and_usage() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.test/v1/responses"
        assert request.headers["authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "gpt-test"
        assert payload["input"] == [{"role": "user", "content": "Hello"}]
        assert "Reply in English" in payload["instructions"]
        return httpx.Response(
            200,
            json={
                "output_text": "Hello from OpenAI",
                "usage": {"input_tokens": 4, "output_tokens": 5, "total_tokens": 9},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    router = ConfiguredModelRouter(
        [
            ProviderConfig(
                "gpt",
                "ChatGPT",
                "OpenAI",
                "openai",
                "https://api.openai.test/v1",
                "test-key",
                "gpt-test",
                "free",
                True,
            )
        ],
        client,
    )

    result = await router.generate(
        GenerateRequest(
            model_id="gpt",
            messages=[ChatMessage(role="user", content="Hello")],
            response_language="en",
        )
    )

    assert result.content == "Hello from OpenAI"
    assert result.provider == "OpenAI"
    assert result.usage is not None
    assert result.usage.total_tokens == 9
    await client.aclose()


@pytest.mark.asyncio
async def test_unconfigured_model_is_rejected_before_network_call() -> None:
    router = ConfiguredModelRouter([])
    with pytest.raises(ModelUnavailableError):
        await router.generate(
            GenerateRequest(
                model_id="gpt",
                messages=[ChatMessage(role="user", content="Hello")],
            )
        )


@pytest.mark.asyncio
async def test_all_configured_provider_keys_make_all_models_available() -> None:
    config = Settings(
        _env_file=None,
        openai_api_key="openai-test-key",
        deepseek_api_key="deepseek-test-key",
        gemini_api_key="gemini-test-key",
        perplexity_api_key="perplexity-test-key",
        anthropic_api_key="anthropic-test-key",
        xai_api_key="xai-test-key",
    )

    models = await create_model_router(config).list_models()

    assert [model.id for model in models] == [
        "gpt",
        "deepseek",
        "gemini",
        "perplexity",
        "claude",
        "grok",
    ]
    assert all(model.available for model in models)
    assert {model.id: model.configured_model for model in models} == {
        "gpt": "gpt-5.6-sol",
        "deepseek": "deepseek-v4-flash",
        "gemini": "gemini-3.6-flash",
        "perplexity": "sonar",
        "claude": "claude-sonnet-5",
        "grok": "grok-4.5",
    }

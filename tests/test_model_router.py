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
        assert payload["tools"] == [{"type": "image_generation"}]
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
async def test_openai_image_generation_output_is_returned() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.test/v1/images/generations"
        payload = json.loads(request.content)
        assert payload == {
            "model": "gpt-image-2",
            "prompt": "Generate a lighthouse image",
            "quality": "low",
            "size": "1024x1024",
            "output_format": "png",
        }
        return httpx.Response(200, json={
            "data": [{"b64_json": "aW1hZ2U="}],
            "usage": {"input_tokens": 3, "output_tokens": 7, "total_tokens": 10},
        })

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    router = ConfiguredModelRouter([
        ProviderConfig("gpt", "ChatGPT", "OpenAI", "openai", "https://api.openai.test/v1",
                       "test-key", "gpt-test", "free", True)
    ], client)

    result = await router.generate(GenerateRequest(
        model_id="gpt",
        messages=[ChatMessage(role="user", content="Generate a lighthouse image")],
    ))

    assert result.content == "Here is your generated image."
    assert result.generated_images[0].data_base64 == "aW1hZ2U="
    await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_id", "name", "vendor", "kind"),
    [
        ("deepseek", "DeepSeek", "DeepSeek", "openai-compatible"),
        ("gemini", "Gemini", "Google", "gemini"),
        ("perplexity", "Perplexity", "Perplexity", "perplexity"),
        ("claude", "Claude", "Anthropic", "anthropic"),
        ("grok", "Grok", "xAI", "openai-compatible"),
    ],
)
async def test_every_non_openai_model_uses_shared_image_generator(
    model_id: str,
    name: str,
    vendor: str,
    kind: str,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.test/v1/images/generations"
        assert request.headers["authorization"] == "Bearer openai-key"
        return httpx.Response(200, json={"data": [{"b64_json": "aW1hZ2U="}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    router = ConfiguredModelRouter([
        ProviderConfig("gpt", "ChatGPT", "OpenAI", "openai", "https://api.openai.test/v1",
                       "openai-key", "gpt-test", "free", True),
        ProviderConfig(model_id, name, vendor, kind, "https://selected-provider.test",
                       "selected-key", "selected-test", "free", True),
    ], client)

    result = await router.generate(GenerateRequest(
        model_id=model_id,
        messages=[ChatMessage(role="user", content="Create an image of a moon base")],
    ))

    assert result.model_id == model_id
    assert result.provider == "OpenAI"
    assert result.configured_model == "gpt-image-2"
    assert result.generated_images[0].data_base64 == "aW1hZ2U="
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

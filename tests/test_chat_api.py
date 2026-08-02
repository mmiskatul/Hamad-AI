from typing import cast

from fastapi.testclient import TestClient

from app.dependencies import get_model_router
from app.main import app
from app.schemas.ai import GenerateRequest, GenerateResponse, ModelInfo
from app.schemas.common import TokenUsage
from app.services.model_router import ConfiguredModelRouter


class FakeModelRouter:
    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="gpt",
                name="ChatGPT",
                vendor="OpenAI",
                min_plan="free",
                available=True,
                configured_model="gpt-test",
            )
        ]

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        assert request.messages[0].content == "Hello"
        assert request.memory is not None
        assert request.memory.nickname == "Miskat"
        return GenerateResponse(
            id="resp_test",
            created_at="2026-08-02T00:00:00+00:00",
            model_id="gpt",
            provider="OpenAI",
            configured_model="gpt-test",
            content="Hello from FastAPI",
            usage=TokenUsage(input_tokens=2, output_tokens=3, total_tokens=5),
        )


def test_chat_endpoint_uses_pydantic_contract_and_injected_router() -> None:
    app.dependency_overrides[get_model_router] = lambda: cast(
        ConfiguredModelRouter, FakeModelRouter()
    )
    try:
        response = TestClient(app).post(
            "/api/v1/chat/responses",
            json={
                "modelId": "gpt",
                "messages": [{"role": "user", "content": "  Hello  "}],
                "responseLanguage": "en",
                "memory": {"nickname": "  Miskat  "},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["message"]["content"] == "Hello from FastAPI"
    assert body["usage"]["totalTokens"] == 5


def test_chat_endpoint_rejects_unknown_fields() -> None:
    response = TestClient(app).post(
        "/api/v1/chat/responses",
        json={
            "modelId": "gpt",
            "messages": [{"role": "user", "content": "Hello"}],
            "unexpected": True,
        },
    )

    assert response.status_code == 422


def test_health_endpoints_support_container_probes() -> None:
    app.dependency_overrides[get_model_router] = lambda: cast(
        ConfiguredModelRouter, FakeModelRouter()
    )
    try:
        client = TestClient(app)
        live = client.get("/api/v1/health/live")
        ready = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert live.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["models"] == 1

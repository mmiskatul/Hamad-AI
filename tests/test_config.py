import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_requires_at_least_one_provider_key() -> None:
    with pytest.raises(ValidationError, match="At least one AI provider API key"):
        Settings(
            app_env="production",
            openai_api_key="",
            deepseek_api_key="",
            gemini_api_key="",
            perplexity_api_key="",
            anthropic_api_key="",
            xai_api_key="",
        )


def test_production_accepts_a_provider_key() -> None:
    settings = Settings(
        app_env="production",
        openai_api_key="test-key",
        deepseek_api_key="",
        gemini_api_key="",
        perplexity_api_key="",
        anthropic_api_key="",
        xai_api_key="",
    )

    assert settings.openai_api_key == "test-key"

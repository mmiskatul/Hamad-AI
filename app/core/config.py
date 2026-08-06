from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "OneAI Hub FastAPI"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    app_env: str = "development"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "one_ai_hub"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    model_router_timeout_seconds: int = 180
    upload_dir: str = "storage/uploads"
    enable_workers: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.6-sol"
    openai_image_model: str = "gpt-image-2"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-3.6-flash"

    perplexity_api_key: str = ""
    perplexity_base_url: str = "https://api.perplexity.ai"
    perplexity_model: str = "sonar"

    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    anthropic_model: str = "claude-sonnet-5"

    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.5"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None:
            return ["http://localhost:3000"]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if self.app_env.lower() != "production":
            return self
        provider_keys = (
            self.openai_api_key,
            self.deepseek_api_key,
            self.gemini_api_key,
            self.perplexity_api_key,
            self.anthropic_api_key,
            self.xai_api_key,
        )
        if not any(key.strip() for key in provider_keys):
            # Allow the service to start without provider keys so the catalogue
            # endpoint can still list models (with available=False) and the
            # health check can succeed. Provider-keyed requests fail later via
            # the model router, not at import time — which is critical for
            # serverless platforms that crash every cold start on a raised
            # validator.
            import warnings

            warnings.warn(
                "No AI provider API keys are configured. Models will be listed "
                "with available=False until at least one key is set.",
                RuntimeWarning,
                stacklevel=2,
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

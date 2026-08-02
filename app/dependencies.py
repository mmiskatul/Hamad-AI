from functools import lru_cache

from app.services.model_router import ConfiguredModelRouter, create_model_router


@lru_cache(maxsize=1)
def get_model_router() -> ConfiguredModelRouter:
    """Return the process-wide stateless provider router."""
    return create_model_router()

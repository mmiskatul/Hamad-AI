from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.common import ApiModel


class TokenClaims(ApiModel):
    sub: str
    sid: str
    email: str
    name: str
    created_at: datetime


def create_access_token(*, claims: dict[str, object], minutes: int | None = None) -> str:
    payload = {
        **claims,
        "exp": datetime.now(UTC) + timedelta(minutes=minutes or settings.access_token_minutes),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenClaims:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return TokenClaims.model_validate(payload)


def jwt_error_message(error: Exception) -> str:
    if isinstance(error, JWTError):
        return "Invalid or expired token."
    return "Authentication failed."

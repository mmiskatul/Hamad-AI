from pydantic import EmailStr, Field

from app.schemas.common import ApiModel, TokenPair


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(ApiModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserPublic(ApiModel):
    id: str
    email: EmailStr
    name: str
    created_at: str


__all__ = ["LoginRequest", "RegisterRequest", "TokenPair", "UserPublic"]

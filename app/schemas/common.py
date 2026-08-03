from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    words = value.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class UserMemory(ApiModel):
    nickname: str = ""
    occupation: str = ""
    about: str = ""
    summary: str = ""


class TokenUsage(ApiModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class GeneratedImage(ApiModel):
    mime_type: str = "image/png"
    data_base64: str


class TokenPair(ApiModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: str = "15m"

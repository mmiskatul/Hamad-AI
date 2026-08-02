from pydantic import Field

from app.schemas.common import ApiModel


class VoiceSessionRequest(ApiModel):
    model_id: str
    language: str = "auto"


class VoiceSessionResponse(ApiModel):
    session_id: str
    ws_url: str
    ice_servers: list[dict[str, str]] = Field(default_factory=list)

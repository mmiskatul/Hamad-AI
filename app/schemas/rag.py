from pydantic import Field

from app.schemas.common import ApiModel


class RagIngestRequest(ApiModel):
    source_id: str
    content: str = Field(min_length=1)


class RagSearchRequest(ApiModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RagChunk(ApiModel):
    id: str
    score: float
    text: str
    source_id: str


class RagSearchResponse(ApiModel):
    chunks: list[RagChunk]

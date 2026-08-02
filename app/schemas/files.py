from app.schemas.common import ApiModel


class FileIngestResponse(ApiModel):
    file_id: str
    filename: str
    status: str


class FileChunkResponse(ApiModel):
    chunk_id: str
    file_id: str
    text: str

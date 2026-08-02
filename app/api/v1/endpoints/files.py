from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.files import FileIngestResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileIngestResponse)
async def upload_file(file: Annotated[UploadFile, File()]) -> FileIngestResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Wire file processing here.",
    )

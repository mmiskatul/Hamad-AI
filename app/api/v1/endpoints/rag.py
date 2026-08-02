from fastapi import APIRouter, HTTPException, status

from app.schemas.rag import RagIngestRequest, RagSearchRequest, RagSearchResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest")
async def ingest(_: RagIngestRequest) -> dict[str, bool]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire ingest worker here."
    )


@router.post("/search", response_model=RagSearchResponse)
async def search(_: RagSearchRequest) -> RagSearchResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire retrieval here.")

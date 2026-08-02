from fastapi import APIRouter, HTTPException, status

from app.schemas.agents import AgentRunRequest, AgentRunResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(_: AgentRunRequest) -> AgentRunResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire AI agents here.")

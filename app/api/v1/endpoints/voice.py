from fastapi import APIRouter, HTTPException, status

from app.schemas.voice import VoiceSessionRequest, VoiceSessionResponse

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/sessions", response_model=VoiceSessionResponse)
async def create_voice_session(_: VoiceSessionRequest) -> VoiceSessionResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Wire WebSocket/WebRTC signaling here.",
    )

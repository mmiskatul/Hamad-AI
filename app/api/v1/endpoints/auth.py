from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair, UserPublic

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenPair)
async def login(_: LoginRequest) -> TokenPair:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire AuthService here."
    )


@router.post("/register", response_model=TokenPair)
async def register(_: RegisterRequest) -> TokenPair:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire registration here."
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh() -> TokenPair:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire token rotation here."
    )


@router.post("/logout")
async def logout() -> dict[str, bool]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire session revocation here."
    )


@router.get("/me", response_model=UserPublic)
async def me() -> UserPublic:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Wire current-user lookup here."
    )

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    revoke_access_token,
    check_auth_rate_limit,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT.lower() == "production",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )


def _extract_request_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return request.cookies.get("access_token")


def _enforce_rate_limit(request: Request, action: str, email: str = "") -> None:
    client_host = request.client.host if request.client else "unknown"
    rate_key = f"{action}:{client_host}:{email.lower().strip()}"
    if not check_auth_rate_limit(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait a minute before trying again.",
        )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    _enforce_rate_limit(request, "register")
    user_repo = UserRepository(db)
    existing = await user_repo.get_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    hashed_pw = get_password_hash(user_in.password)
    user = await user_repo.create(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name
    )

    token = create_access_token(subject=str(user.id))
    _set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    _enforce_rate_limit(request, "login", credentials.email)
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    token = create_access_token(subject=str(user.id))
    _set_auth_cookie(response, token)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    token = _extract_request_token(request)
    revoke_access_token(token)
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Successfully logged out"}


@router.delete("/me")
async def delete_my_account(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently deletes the authenticated user's account and all associated athlete data."""
    token = _extract_request_token(request)
    revoke_access_token(token)
    user_repo = UserRepository(db)
    await user_repo.delete_user_and_data(current_user)
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Account and all associated personal fitness data permanently deleted"}

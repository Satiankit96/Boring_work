"""
Auth API Routes (v1)
====================
Role: Define REST endpoints for authentication — register, login, refresh, logout, get current user.
Routes ONLY handle HTTP concerns: request validation, calling services, returning responses.
Supports both local (bcrypt/JWT) and Keycloak authentication modes.
Business logic lives in auth_service.py — this file never touches the database directly.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
)
from app.db.base import get_db_session
from app.models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    RegisterResponse,
    LoginResponse,
    RefreshResponse,
    LogoutResponse,
    MeResponse,
    UserOut,
)
from app.middleware.auth_middleware import CurrentUser
from app.repositories.sqlite_user_repository import SqliteUserRepository
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> AuthService:
    """
    Dependency that creates AuthService with repository.
    This is the ONLY place we wire the concrete repository to the service.
    """
    repository = SqliteUserRepository(session)
    return AuthService(repository)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        409: {"description": "Email already exists"},
    }
)
async def register(
    request: UserRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> RegisterResponse:
    """
    Register a new user account.
    
    - Validates email format and password length
    - Checks for duplicate email
    - Stores password as bcrypt hash
    """
    try:
        user_id, message = await auth_service.register(
            email=request.email,
            password=request.password,
        )
        return RegisterResponse(message=message, user_id=user_id)
    
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message}
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and get access token",
    responses={
        401: {"description": "Invalid credentials"},
    }
)
async def login(
    request: UserLoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """
    Authenticate user and return JWT access token.
    
    - In Keycloak mode: delegates to Keycloak, returns access + refresh tokens
    - In local mode: validates against local DB, returns access token only
    - Generic error message to prevent email enumeration
    """
    try:
        tokens, user = await auth_service.login(
            email=request.email,
            password=request.password,
        )
        
        # Build user response for local mode
        user_out = None
        if user is not None:
            user_out = UserOut.model_validate(user)
        
        return LoginResponse(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
            refresh_token=tokens.refresh_token,
            user=user_out,
        )
    
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message}
        )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    }
)
async def refresh(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> RefreshResponse:
    """
    Refresh the access token using a refresh token.
    
    Only available in Keycloak mode. In local mode, returns 401.
    """
    if settings.auth_mode != "keycloak":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOT_SUPPORTED", "message": "Token refresh not supported in local mode"}
        )
    
    try:
        tokens = await auth_service.refresh_token(request.refresh_token)
        
        return RefreshResponse(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
            refresh_token=tokens.refresh_token,
        )
    
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "REFRESH_FAILED", "message": str(e)}
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and invalidate tokens",
)
async def logout(
    request: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LogoutResponse:
    """
    Logout the user by invalidating the refresh token.
    
    In Keycloak mode: invalidates the refresh token server-side.
    In local mode: no-op (tokens expire naturally).
    """
    await auth_service.logout(request.refresh_token)
    return LogoutResponse()


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user info",
    responses={
        401: {"description": "Not authenticated"},
    }
)
async def get_me(current_user: CurrentUser) -> MeResponse:
    """
    Get the currently authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    In Keycloak mode: returns user info from token claims.
    In local mode: returns user info from database.
    """
    # Handle both local and Keycloak modes
    created_at = None
    if current_user.local_user is not None:
        created_at = current_user.local_user.created_at
    
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        roles=current_user.roles,
        created_at=created_at,
    )

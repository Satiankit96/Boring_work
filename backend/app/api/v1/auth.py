"""
Auth API Routes (v1)
====================
Role: Define REST endpoints for authentication — register, login, get current user.
Routes ONLY handle HTTP concerns: request validation, calling services, returning responses.
Business logic lives in auth_service.py — this file never touches the database directly.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
)
from app.db.base import get_db_session
from app.models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    RegisterResponse,
    LoginResponse,
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
    
    - Validates credentials
    - Returns bearer token on success
    - Generic error message to prevent email enumeration
    """
    try:
        access_token, user = await auth_service.login(
            email=request.email,
            password=request.password,
        )
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )
    
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message}
        )


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
    """
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
    )

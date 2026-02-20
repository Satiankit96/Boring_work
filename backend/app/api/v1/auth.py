# api/v1/auth.py
# Role: Route definitions ONLY. Validates requests (via Pydantic), calls AuthService, returns responses.
# NEVER: touches DB directly, hashes passwords, writes SQL, or contains any business logic.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.repositories.sqlite_user_repository import SqliteUserRepository
from app.services.auth_service import AuthService
from app.models.schemas import RegisterRequest, LoginRequest, RegisterResponse, LoginResponse, UserOut
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.middleware.auth_middleware import get_current_user_id

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency: wires together the concrete repository and service."""
    repo = SqliteUserRepository(db)
    return AuthService(repo)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return await service.register(email=body.email, password=body.password)
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return await service.login(email=body.email, password=body.password)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/me", response_model=UserOut)
async def me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SqliteUserRepository(db)
    service = AuthService(repo)
    try:
        # Re-use get_current_user by looking up by ID from the validated token
        from app.models.schemas import UserOut
        user = await repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "USER_NOT_FOUND", "message": "User not found"})
        return UserOut.model_validate(user)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )

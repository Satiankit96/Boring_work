"""
Auth Middleware (JWT Dependency)
================================
Role: FastAPI dependency for protecting routes that require authentication.
Validates JWT token from Authorization header and returns current user.
Reused by ALL future modules that need authentication.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.exceptions import InvalidTokenError, UserNotFoundError
from app.db.base import get_db_session
from app.models.user import User
from app.repositories.sqlite_user_repository import SqliteUserRepository
from app.services.auth_service import AuthService


# Bearer token security scheme for Swagger UI
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    FastAPI dependency that extracts and validates JWT from Authorization header.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    
    Args:
        credentials: Bearer token from Authorization header
        session: Database session (injected)
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Decode and validate JWT
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token payload invalid"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    repository = SqliteUserRepository(session)
    auth_service = AuthService(repository)
    
    try:
        user = await auth_service.get_current_user(user_id)
        return user
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User no longer exists"},
            headers={"WWW-Authenticate": "Bearer"},
        )


# Type alias for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]

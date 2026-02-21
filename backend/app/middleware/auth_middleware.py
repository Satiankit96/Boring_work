"""
Auth Middleware (JWT Dependency)
================================
Role: FastAPI dependency for protecting routes that require authentication.
Validates JWT token from Authorization header and returns current user.
Supports both local (HS256) and Keycloak (RS256 via JWKS) modes.
Reused by ALL future modules that need authentication.
"""

from typing import Annotated, Optional
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.core.exceptions import InvalidTokenError, UserNotFoundError
from app.db.base import get_db_session
from app.models.user import User
from app.repositories.sqlite_user_repository import SqliteUserRepository
from app.services.auth_service import AuthService

# Import auth-client for Keycloak mode
import sys
from pathlib import Path

# Add auth-client to path if running locally
auth_client_path = Path(__file__).resolve().parent.parent.parent.parent / "auth-client" / "src"
if auth_client_path.exists() and str(auth_client_path) not in sys.path:
    sys.path.insert(0, str(auth_client_path))

from auth_client import KeycloakConfig, JWKSVerifier, AuthUser as KeycloakAuthUser
from auth_client.verifier import (
    JWKSVerificationError,
    TokenExpiredError as JWKSTokenExpiredError,
    InvalidTokenError as JWKSInvalidTokenError,
)


# Bearer token security scheme for Swagger UI
security = HTTPBearer()


@dataclass
class AuthenticatedUser:
    """
    Unified user model for both local and Keycloak auth modes.
    
    Attributes:
        id: User ID (UUID for local, sub claim for Keycloak)
        email: User's email address
        roles: User's roles (from Keycloak or empty for local)
        raw_token: Original JWT token
        keycloak_user: Original Keycloak AuthUser if in Keycloak mode
        local_user: Original local User if in local mode
    """
    id: str
    email: Optional[str]
    roles: list[str]
    raw_token: str
    keycloak_user: Optional[KeycloakAuthUser] = None
    local_user: Optional[User] = None
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.roles
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles


# Keycloak verifier (lazy initialized)
_keycloak_verifier: Optional[JWKSVerifier] = None


def get_keycloak_verifier() -> JWKSVerifier:
    """Get or create the Keycloak JWKS verifier."""
    global _keycloak_verifier
    if _keycloak_verifier is None:
        config = KeycloakConfig(
            server_url=settings.keycloak_server_url,
            realm=settings.keycloak_realm,
            client_id=settings.keycloak_client_id,
            verify_audience=False,  # Keycloak doesn't always include audience
        )
        _keycloak_verifier = JWKSVerifier(config)
    return _keycloak_verifier


async def get_current_user_keycloak(
    credentials: HTTPAuthorizationCredentials,
) -> AuthenticatedUser:
    """
    Validate JWT using Keycloak JWKS endpoint.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        AuthenticatedUser with Keycloak user info
        
    Raises:
        HTTPException 401: If token is invalid or expired
    """
    token = credentials.credentials
    verifier = get_keycloak_verifier()
    
    try:
        payload = await verifier.verify_token_with_retry(token)
        keycloak_user = KeycloakAuthUser.from_token_payload(payload, token)
        
        return AuthenticatedUser(
            id=keycloak_user.sub,
            email=keycloak_user.email,
            roles=keycloak_user.roles,
            raw_token=token,
            keycloak_user=keycloak_user,
        )
        
    except JWKSTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Token has expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWKSInvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": str(e)},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWKSVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "VERIFICATION_FAILED", "message": str(e)},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_local(
    credentials: HTTPAuthorizationCredentials,
    session: AsyncSession,
) -> AuthenticatedUser:
    """
    Validate JWT using local HS256 secret.
    
    Args:
        credentials: Bearer token from Authorization header
        session: Database session
        
    Returns:
        AuthenticatedUser with local user info
        
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
        return AuthenticatedUser(
            id=user.id,
            email=user.email,
            roles=[],  # Local mode doesn't have roles
            raw_token=token,
            local_user=user,
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User no longer exists"},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthenticatedUser:
    """
    FastAPI dependency that extracts and validates JWT from Authorization header.
    
    Automatically selects verification method based on auth_mode setting:
    - "keycloak": Verifies using RS256 with JWKS endpoint
    - "local": Verifies using HS256 with local secret
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: AuthenticatedUser = Depends(get_current_user)):
            return {"user_id": user.id, "roles": user.roles}
    
    Args:
        credentials: Bearer token from Authorization header
        session: Database session (injected)
        
    Returns:
        AuthenticatedUser object
        
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    if settings.auth_mode == "keycloak":
        return await get_current_user_keycloak(credentials)
    else:
        return await get_current_user_local(credentials, session)


def require_roles(*required_roles: str, any_role: bool = False):
    """
    Create a dependency that requires specific roles.
    
    Args:
        *required_roles: Role names to require
        any_role: If True, user needs any role. If False, needs all.
        
    Returns:
        FastAPI dependency
        
    Usage:
        @router.get("/admin")
        async def admin_route(
            user: AuthenticatedUser = Depends(get_current_user),
            _: None = Depends(require_roles("admin"))
        ):
            return {"admin": user.email}
    """
    async def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> None:
        roles = list(required_roles)
        
        if any_role:
            if not any(role in user.roles for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message": f"Requires any of roles: {roles}"},
                )
        else:
            if not all(role in user.roles for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message": f"Requires roles: {roles}"},
                )
    
    return dependency


# Type alias for cleaner route signatures
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]

# Legacy type alias for backward compatibility
# Note: This now returns AuthenticatedUser instead of User

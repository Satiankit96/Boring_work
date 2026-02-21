"""
FastAPI middleware for JWT authentication.
"""

from typing import Callable, Optional
from functools import lru_cache

from auth_client.config import KeycloakConfig
from auth_client.models import AuthUser, TokenPayload
from auth_client.verifier import (
    JWKSVerifier,
    JWKSVerificationError,
    TokenExpiredError,
    InvalidTokenError,
)

# Cache verifiers by config to avoid recreating them
_verifier_cache: dict[int, JWKSVerifier] = {}


def _get_verifier(config: KeycloakConfig) -> JWKSVerifier:
    """Get or create a verifier for the given config."""
    config_hash = hash((config.server_url, config.realm))
    if config_hash not in _verifier_cache:
        _verifier_cache[config_hash] = JWKSVerifier(config)
    return _verifier_cache[config_hash]


def require_auth(
    config: KeycloakConfig,
    *,
    required_roles: Optional[list[str]] = None,
    any_role: bool = False,
) -> Callable:
    """
    Create a FastAPI dependency that requires valid JWT authentication.
    
    This dependency extracts the Bearer token from the Authorization header,
    verifies it using the JWKS endpoint, and returns an AuthUser object.
    
    Args:
        config: Keycloak configuration
        required_roles: Optional list of roles the user must have
        any_role: If True, user needs any of required_roles. If False, needs all.
        
    Returns:
        FastAPI dependency function
        
    Example:
        ```python
        from fastapi import FastAPI, Depends
        from auth_client import require_auth, AuthUser, KeycloakConfig
        
        config = KeycloakConfig(
            server_url="http://localhost:8080",
            realm="my-app"
        )
        
        @app.get("/protected")
        async def protected(user: AuthUser = Depends(require_auth(config))):
            return {"user": user.email}
        
        # With role requirements
        @app.get("/admin")
        async def admin_only(
            user: AuthUser = Depends(require_auth(config, required_roles=["admin"]))
        ):
            return {"admin": user.email}
        ```
    
    Raises:
        HTTPException(401): If token is missing, invalid, or expired
        HTTPException(403): If user lacks required roles
    """
    # Import here to make FastAPI optional
    try:
        from fastapi import HTTPException, Request
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    except ImportError:
        raise ImportError(
            "FastAPI is required for middleware. "
            "Install with: pip install auth-client[fastapi]"
        )
    
    security = HTTPBearer(auto_error=False)
    verifier = _get_verifier(config)
    
    async def dependency(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> AuthUser:
        # Try to get credentials from HTTPBearer
        if credentials is None:
            # Manually check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=401,
                    detail="Missing authorization header",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authorization header format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token = auth_header[7:]
        else:
            token = credentials.credentials
        
        try:
            payload = await verifier.verify_token_with_retry(token)
        except TokenExpiredError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except InvalidTokenError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWKSVerificationError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Token verification failed: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = AuthUser.from_token_payload(payload, token)
        
        # Check required roles
        if required_roles:
            if any_role:
                if not user.has_any_role(required_roles):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User lacks any of required roles: {required_roles}",
                    )
            else:
                if not user.has_all_roles(required_roles):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User lacks required roles: {required_roles}",
                    )
        
        return user
    
    return dependency


def optional_auth(config: KeycloakConfig) -> Callable:
    """
    Create a FastAPI dependency that optionally authenticates.
    
    If a valid Bearer token is provided, returns AuthUser.
    If no token or invalid token, returns None.
    
    Args:
        config: Keycloak configuration
        
    Returns:
        FastAPI dependency function
        
    Example:
        ```python
        @app.get("/optional")
        async def optional_auth_route(
            user: AuthUser | None = Depends(optional_auth(config))
        ):
            if user:
                return {"message": f"Hello, {user.email}!"}
            return {"message": "Hello, anonymous!"}
        ```
    """
    try:
        from fastapi import Request
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    except ImportError:
        raise ImportError(
            "FastAPI is required for middleware. "
            "Install with: pip install auth-client[fastapi]"
        )
    
    security = HTTPBearer(auto_error=False)
    verifier = _get_verifier(config)
    
    async def dependency(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> Optional[AuthUser]:
        # Get token from credentials or header
        token: Optional[str] = None
        
        if credentials:
            token = credentials.credentials
        else:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            return None
        
        try:
            payload = await verifier.verify_token_with_retry(token)
            return AuthUser.from_token_payload(payload, token)
        except JWKSVerificationError:
            return None
    
    return dependency


def require_roles(*roles: str, any_role: bool = False) -> Callable:
    """
    Create a role-checking dependency to use with require_auth.
    
    This is a helper that can be combined with an AuthUser parameter
    to check roles without creating a new verifier.
    
    Args:
        *roles: Role names to require
        any_role: If True, user needs any role. If False, needs all.
        
    Returns:
        FastAPI dependency function
        
    Example:
        ```python
        @app.get("/admin")
        async def admin_route(
            user: AuthUser = Depends(require_auth(config)),
            _: None = Depends(require_roles("admin"))
        ):
            return {"admin": user.email}
        ```
    """
    try:
        from fastapi import HTTPException, Request
    except ImportError:
        raise ImportError("FastAPI is required for middleware.")
    
    def dependency(request: Request) -> None:
        # Get user from request state (must be set by require_auth first)
        user: Optional[AuthUser] = getattr(request.state, "auth_user", None)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )
        
        required_roles = list(roles)
        
        if any_role:
            if not user.has_any_role(required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"User lacks any of required roles: {required_roles}",
                )
        else:
            if not user.has_all_roles(required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"User lacks required roles: {required_roles}",
                )
    
    return dependency

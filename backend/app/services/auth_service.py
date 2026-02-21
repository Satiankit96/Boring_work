"""
Authentication Service
======================
Role: Business logic for authentication — register, login, get current user.
This layer orchestrates repositories and security utilities.
Supports both local (bcrypt/JWT) and Keycloak authentication modes.
NEVER writes SQL or returns HTTP responses — pure business logic only.
"""

import uuid
from typing import Optional
from dataclasses import dataclass

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
)
from app.core.keycloak_client import (
    keycloak_client,
    KeycloakAuthenticationError,
    KeycloakTokenError,
    TokenResponse,
)
from app.models.user import User
from app.models.schemas import UserOut
from app.repositories.base import IUserRepository


@dataclass
class AuthTokens:
    """Token response containing access and refresh tokens."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 300


class AuthService:
    """
    Authentication service handling registration, login, and user retrieval.
    
    Depends ONLY on IUserRepository interface — never on a concrete implementation.
    This allows swapping storage backends without changing any business logic.
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize service with a user repository.
        
        Args:
            user_repository: Any implementation of IUserRepository
        """
        self._user_repo = user_repository

    async def register(self, email: str, password: str) -> tuple[str, str]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: Plaintext password (will be hashed)
            
        Returns:
            Tuple of (user_id, message)
            
        Raises:
            EmailAlreadyExistsError: If email is already registered
        """
        # Check if email already exists
        if await self._user_repo.exists_by_email(email):
            raise EmailAlreadyExistsError()
        
        # Generate UUID and hash password
        user_id = str(uuid.uuid4())
        hashed = hash_password(password)
        
        # Create user in storage
        await self._user_repo.create(user_id, email, hashed)
        
        return user_id, "Account created"

    async def login(self, email: str, password: str) -> tuple[AuthTokens, Optional[User]]:
        """
        Authenticate a user and generate access token.
        
        In Keycloak mode, delegates authentication to Keycloak.
        In local mode, verifies password against local hash.
        
        Args:
            email: User's email address
            password: Plaintext password to verify
            
        Returns:
            Tuple of (AuthTokens, user or None)
            
        Raises:
            InvalidCredentialsError: If email not found or password incorrect
        """
        if settings.auth_mode == "keycloak":
            return await self._login_keycloak(email, password)
        else:
            return await self._login_local(email, password)
    
    async def _login_keycloak(self, email: str, password: str) -> tuple[AuthTokens, None]:
        """Login via Keycloak token exchange."""
        try:
            token_response = await keycloak_client.token_exchange(
                username=email,
                password=password,
            )
            
            tokens = AuthTokens(
                access_token=token_response.access_token,
                refresh_token=token_response.refresh_token,
                token_type=token_response.token_type,
                expires_in=token_response.expires_in,
            )
            
            return tokens, None
            
        except KeycloakAuthenticationError:
            raise InvalidCredentialsError()
        except KeycloakTokenError as e:
            raise InvalidCredentialsError(str(e))
    
    async def _login_local(self, email: str, password: str) -> tuple[AuthTokens, User]:
        """Login with local bcrypt password verification."""
        # Find user by email
        user = await self._user_repo.get_by_email(email)
        
        # Use same error for both cases (prevent email enumeration)
        if user is None:
            raise InvalidCredentialsError()
        
        # Verify password
        if not verify_password(password, user.password):
            raise InvalidCredentialsError()
        
        # Generate JWT token
        access_token = create_access_token(data={"sub": user.id})
        
        tokens = AuthTokens(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
        
        return tokens, user
    
    async def refresh_token(self, refresh_token: str) -> AuthTokens:
        """
        Refresh access token using a refresh token.
        
        Only available in Keycloak mode.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New AuthTokens with fresh access and refresh tokens
            
        Raises:
            InvalidCredentialsError: If refresh fails
        """
        if settings.auth_mode != "keycloak":
            raise InvalidCredentialsError("Token refresh not supported in local mode")
        
        try:
            token_response = await keycloak_client.refresh_token(refresh_token)
            
            return AuthTokens(
                access_token=token_response.access_token,
                refresh_token=token_response.refresh_token,
                token_type=token_response.token_type,
                expires_in=token_response.expires_in,
            )
            
        except KeycloakTokenError as e:
            raise InvalidCredentialsError(str(e))
    
    async def logout(self, refresh_token: str) -> bool:
        """
        Logout user by invalidating refresh token.
        
        Only functional in Keycloak mode.
        
        Args:
            refresh_token: Refresh token to invalidate
            
        Returns:
            True if logout successful
        """
        if settings.auth_mode != "keycloak":
            return True  # No server-side logout in local mode
        
        try:
            return await keycloak_client.logout(refresh_token)
        except Exception:
            return False

    async def get_current_user(self, user_id: str) -> User:
        """
        Retrieve user by ID (for authenticated requests).
        
        Args:
            user_id: The user's UUID (from decoded JWT)
            
        Returns:
            User object
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = await self._user_repo.get_by_id(user_id)
        
        if user is None:
            raise UserNotFoundError()
        
        return user

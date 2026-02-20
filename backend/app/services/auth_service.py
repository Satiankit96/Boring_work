"""
Authentication Service
======================
Role: Business logic for authentication — register, login, get current user.
This layer orchestrates repositories and security utilities.
NEVER writes SQL or returns HTTP responses — pure business logic only.
"""

import uuid
from typing import Optional

from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
)
from app.models.user import User
from app.models.schemas import UserOut
from app.repositories.base import IUserRepository


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

    async def login(self, email: str, password: str) -> tuple[str, User]:
        """
        Authenticate a user and generate access token.
        
        Args:
            email: User's email address
            password: Plaintext password to verify
            
        Returns:
            Tuple of (access_token, user)
            
        Raises:
            InvalidCredentialsError: If email not found or password incorrect
        """
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
        
        return access_token, user

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

# services/auth_service.py
# Role: All business logic for authentication — register, login, get current user.
# Depends ONLY on IUserRepository (abstract). Never imports SQLite, never writes SQL.
# Never returns HTTP responses — raises domain exceptions instead.

import uuid
from jose import JWTError
from app.repositories.base import IUserRepository
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.core.exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
    InvalidTokenError,
)
from app.models.user import User
from app.models.schemas import LoginResponse, RegisterResponse, UserOut


class AuthService:
    def __init__(self, repository: IUserRepository):
        self._repo = repository

    async def register(self, email: str, password: str) -> RegisterResponse:
        """Register a new user. Raises EmailAlreadyExistsError if email is taken."""
        existing = await self._repo.get_by_email(email)
        if existing:
            raise EmailAlreadyExistsError()

        user_id = str(uuid.uuid4())
        hashed = hash_password(password)
        user = await self._repo.create(id=user_id, email=email, hashed_password=hashed)
        return RegisterResponse(message="Account created", user_id=user.id)

    async def login(self, email: str, password: str) -> LoginResponse:
        """Authenticate a user. Always raises InvalidCredentialsError on any failure (no enumeration)."""
        user = await self._repo.get_by_email(email)
        if not user or not verify_password(password, user.password):
            raise InvalidCredentialsError()

        token = create_access_token({"sub": user.id})
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )

    async def get_current_user(self, token: str) -> UserOut:
        """Validate a JWT and return the associated user. Raises InvalidTokenError if invalid."""
        try:
            payload = decode_token(token)
            user_id: str = payload.get("sub")
            if not user_id:
                raise InvalidTokenError()
        except JWTError:
            raise InvalidTokenError()

        user = await self._repo.get_by_id(user_id)
        if not user:
            raise InvalidTokenError()

        return UserOut.model_validate(user)

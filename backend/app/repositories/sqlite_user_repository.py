"""
SQLite User Repository Implementation
=====================================
Role: Concrete implementation of IUserRepository using SQLite via SQLAlchemy async.
This is the ACTIVE storage backend for local development.
To switch to PostgreSQL: create PostgresUserRepository, change import in main.py.
"""

from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import IUserRepository


class SqliteUserRepository(IUserRepository):
    """
    SQLite implementation of the user repository.
    
    Uses SQLAlchemy async with aiosqlite for local development.
    Swap this class to change storage backend — no service code changes needed.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with an async database session.
        
        Args:
            session: SQLAlchemy AsyncSession (injected by FastAPI dependency)
        """
        self._session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            User if found, None otherwise
        """
        query = select(User).where(User.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their unique ID.
        
        Args:
            user_id: The UUID string to search for
            
        Returns:
            User if found, None otherwise
        """
        query = select(User).where(User.id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_id: str, email: str, hashed_password: str) -> User:
        """
        Create a new user in SQLite.
        
        Args:
            user_id: Pre-generated UUID for the user
            email: User's email address
            hashed_password: bcrypt-hashed password
            
        Returns:
            The created User object
        """
        user = User(
            id=user_id,
            email=email,
            password=hashed_password,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email already exists.
        
        Args:
            email: The email address to check
            
        Returns:
            True if exists, False otherwise
        """
        query = select(User.id).where(User.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none() is not None

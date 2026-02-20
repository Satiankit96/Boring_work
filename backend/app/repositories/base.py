"""
Repository Interface (Abstract Base Class)
==========================================
Role: Define the contract that ALL user storage implementations must follow.
The service layer ONLY depends on this interface, never on concrete implementations.
This enables swapping SQLite → PostgreSQL → DynamoDB with zero service code changes.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.user import User


class IUserRepository(ABC):
    """
    Abstract interface for user data access.
    
    Every storage backend (SQLite, PostgreSQL, DynamoDB) must implement these methods.
    The service layer depends ONLY on this interface — never on a concrete class.
    This is the Repository Pattern in action.
    """

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            User if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their unique ID.
        
        Args:
            user_id: The UUID string to search for
            
        Returns:
            User if found, None otherwise
        """
        ...

    @abstractmethod
    async def create(self, user_id: str, email: str, hashed_password: str) -> User:
        """
        Create a new user in the storage.
        
        Args:
            user_id: Pre-generated UUID for the user
            email: User's email address
            hashed_password: bcrypt-hashed password (NEVER plaintext)
            
        Returns:
            The created User object
        """
        ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email already exists.
        
        Args:
            email: The email address to check
            
        Returns:
            True if exists, False otherwise
        """
        ...

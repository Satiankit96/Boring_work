# repositories/base.py
# Role: Abstract interface (contract) for user data access.
# The service layer depends ONLY on this interface — never on a concrete implementation.
# To swap storage backends, implement this interface and change one line in main.py.

from abc import ABC, abstractmethod
from app.models.user import User


class IUserRepository(ABC):
    """
    CONTRACT: Every storage backend must implement these methods.
    Services only ever depend on this interface, never on SQLite / Postgres / etc.
    """

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def create(self, id: str, email: str, hashed_password: str) -> User: ...

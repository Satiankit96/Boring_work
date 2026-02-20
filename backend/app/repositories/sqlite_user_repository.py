# repositories/sqlite_user_repository.py
# Role: Concrete SQLite implementation of IUserRepository.
# All SQLAlchemy queries live here — nowhere else.
# To move to Postgres: write PostgresUserRepository implementing IUserRepository, change main.py import.

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import IUserRepository
from app.models.user import User
from datetime import datetime, timezone


class SqliteUserRepository(IUserRepository):
    """Concrete data-access layer backed by SQLite via SQLAlchemy async."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, id: str, email: str, hashed_password: str) -> User:
        now = datetime.now(timezone.utc).isoformat()
        user = User(id=id, email=email, password=hashed_password, created_at=now, updated_at=now)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

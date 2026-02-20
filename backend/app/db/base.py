"""
Database Base Module
====================
Role: Set up SQLAlchemy async engine and session factory.
This is the only place database connection details are configured.
All repositories use the async session factory from here.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Create async engine with SQLite (swap URL for Postgres later)
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",  # Log SQL in dev mode
    future=True,
)

# Async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base class.
    All ORM models inherit from this.
    """
    pass


async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that yields an async database session.
    Automatically closes session after request completes.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize the database by creating all tables.
    Called on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database connections.
    Called on application shutdown.
    """
    await engine.dispose()

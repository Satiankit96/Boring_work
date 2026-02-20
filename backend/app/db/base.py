# db/base.py
# Role: SQLAlchemy async engine + session factory. Everything DB-connection-related lives here.
# Imported by repositories only — never by services or routes.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base that all ORM models inherit from."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields a DB session, closes it after the request."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables defined in ORM models. Called on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

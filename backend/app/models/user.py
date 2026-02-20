"""
User ORM Model
==============
Role: Define the SQLAlchemy ORM model for the users table.
This is the database representation — use Pydantic schemas for API input/output.
"""

from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """
    SQLAlchemy ORM model representing a user in the database.
    Maps to the 'users' table defined in migrations.
    """
    
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)  # bcrypt hash
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

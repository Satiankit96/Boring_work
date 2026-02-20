# models/user.py
# Role: SQLAlchemy ORM model for the users table. Maps DB rows to Python objects.
# No business logic here — just column definitions.

from sqlalchemy import Column, String, Text
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Text, primary_key=True)
    email = Column(Text, nullable=False, unique=True, index=True)
    password = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, default=func.now())
    updated_at = Column(Text, nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"

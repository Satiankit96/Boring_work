# models/schemas.py
# Role: Pydantic v2 schemas for all API request bodies and response shapes.
# These are the ONLY types that cross the HTTP boundary — never expose ORM models directly.

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ── Request Schemas ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Response Schemas ─────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    email: str
    created_at: str

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    message: str
    user_id: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Error Schema ─────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail

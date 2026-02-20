"""
Pydantic Schemas Module
=======================
Role: Define all request and response schemas for the API.
These are used by FastAPI for automatic validation and documentation.
Separate from ORM models — these are for API contracts only.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# Request Schemas
# =============================================================================

class UserRegisterRequest(BaseModel):
    """Request body for user registration."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)"
    )


class UserLoginRequest(BaseModel):
    """Request body for user login."""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


# =============================================================================
# Response Schemas
# =============================================================================

class UserOut(BaseModel):
    """User data returned in API responses (never includes password)."""
    
    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allows creation from ORM model


class RegisterResponse(BaseModel):
    """Response body for successful registration."""
    
    message: str = "Account created"
    user_id: str


class LoginResponse(BaseModel):
    """Response body for successful login."""
    
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MeResponse(BaseModel):
    """Response body for GET /me endpoint."""
    
    id: str
    email: str
    created_at: datetime


# =============================================================================
# Error Schemas
# =============================================================================

class ErrorDetail(BaseModel):
    """Standard error detail structure."""
    
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    
    detail: ErrorDetail

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


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    
    refresh_token: str = Field(..., description="Refresh token from login")


class LogoutRequest(BaseModel):
    """Request body for logout."""
    
    refresh_token: str = Field(..., description="Refresh token to invalidate")


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
    expires_in: int = Field(default=300, description="Access token lifetime in seconds")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token (Keycloak mode only)")
    user: Optional[UserOut] = Field(default=None, description="User info (local mode only)")


class RefreshResponse(BaseModel):
    """Response body for successful token refresh."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=300, description="Access token lifetime in seconds")
    refresh_token: Optional[str] = Field(default=None, description="New refresh token")


class LogoutResponse(BaseModel):
    """Response body for successful logout."""
    
    message: str = "Logged out successfully"


class MeResponse(BaseModel):
    """Response body for GET /me endpoint."""
    
    id: str
    email: Optional[str] = None
    roles: list[str] = Field(default_factory=list, description="User roles (Keycloak mode)")
    created_at: Optional[datetime] = Field(default=None, description="Account creation time (local mode)")


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

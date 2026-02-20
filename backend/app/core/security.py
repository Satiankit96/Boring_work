"""
Security Utilities Module
=========================
Role: Handle all cryptographic operations — password hashing and JWT tokens.
This module is imported ONLY by the service layer, never by routes or repositories.
Contains pure utility functions with no business logic or side effects.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Password hashing context using bcrypt with 12 rounds
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    
    Args:
        plain_password: The raw password from user input
        
    Returns:
        The bcrypt hash string (includes salt)
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    
    Args:
        plain_password: The raw password from login attempt
        hashed_password: The stored bcrypt hash from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode in the token (typically {"sub": user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: The JWT string to decode
        
    Returns:
        The decoded payload dict, or None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None

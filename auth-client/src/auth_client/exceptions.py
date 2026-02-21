"""
Exception classes for auth-client library.
"""

from auth_client.verifier import (
    JWKSVerificationError,
    JWKSFetchError,
    TokenExpiredError,
    InvalidTokenError,
    InvalidSignatureError,
    InvalidIssuerError,
    InvalidAudienceError,
)

__all__ = [
    "JWKSVerificationError",
    "JWKSFetchError",
    "TokenExpiredError",
    "InvalidTokenError",
    "InvalidSignatureError",
    "InvalidIssuerError",
    "InvalidAudienceError",
]

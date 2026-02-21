"""
Auth Client Library

A standalone authentication client library for Keycloak/OIDC JWT verification.
"""

from auth_client.config import KeycloakConfig
from auth_client.models import AuthUser, TokenPayload
from auth_client.verifier import JWKSVerifier
from auth_client.middleware import require_auth, optional_auth

__version__ = "0.1.0"

__all__ = [
    "KeycloakConfig",
    "AuthUser",
    "TokenPayload",
    "JWKSVerifier",
    "require_auth",
    "optional_auth",
]

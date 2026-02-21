"""
Configuration module for Keycloak/OIDC authentication.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class KeycloakConfig:
    """
    Configuration for Keycloak/OIDC authentication.
    
    Attributes:
        server_url: Base URL of the Keycloak server (e.g., http://localhost:8080)
        realm: Name of the Keycloak realm
        client_id: Client ID for token exchange operations (optional)
        client_secret: Client secret for confidential clients (optional)
        jwks_cache_ttl: Time-to-live for JWKS cache in seconds (default: 3600)
        verify_audience: Whether to verify the audience claim (default: True)
        expected_audience: Expected audience value (defaults to client_id)
    """
    
    server_url: str
    realm: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    jwks_cache_ttl: int = 3600
    verify_audience: bool = True
    expected_audience: Optional[str] = None
    
    @property
    def issuer(self) -> str:
        """Get the expected token issuer URL."""
        return f"{self.server_url}/realms/{self.realm}"
    
    @property
    def jwks_uri(self) -> str:
        """Get the JWKS endpoint URL."""
        return f"{self.issuer}/protocol/openid-connect/certs"
    
    @property
    def token_endpoint(self) -> str:
        """Get the token endpoint URL."""
        return f"{self.issuer}/protocol/openid-connect/token"
    
    @property
    def userinfo_endpoint(self) -> str:
        """Get the userinfo endpoint URL."""
        return f"{self.issuer}/protocol/openid-connect/userinfo"
    
    @property
    def authorization_endpoint(self) -> str:
        """Get the authorization endpoint URL."""
        return f"{self.issuer}/protocol/openid-connect/auth"
    
    @property
    def logout_endpoint(self) -> str:
        """Get the logout endpoint URL."""
        return f"{self.issuer}/protocol/openid-connect/logout"
    
    @property
    def introspection_endpoint(self) -> str:
        """Get the token introspection endpoint URL."""
        return f"{self.issuer}/protocol/openid-connect/token/introspect"
    
    def get_audience(self) -> Optional[str]:
        """Get the expected audience for token verification."""
        if self.expected_audience:
            return self.expected_audience
        return self.client_id

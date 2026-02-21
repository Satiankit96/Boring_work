"""
Keycloak Client Module
======================
Async HTTP client for interacting with Keycloak token endpoints.
Handles token exchange, refresh, and logout operations.
"""

from typing import Optional
import httpx
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.config import settings


@dataclass
class TokenResponse:
    """Response from Keycloak token endpoint."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    refresh_expires_in: Optional[int] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    
    @property
    def expires_at(self) -> datetime:
        """Calculate when the access token expires."""
        return datetime.now() + timedelta(seconds=self.expires_in)
    
    @property
    def refresh_expires_at(self) -> Optional[datetime]:
        """Calculate when the refresh token expires."""
        if self.refresh_expires_in:
            return datetime.now() + timedelta(seconds=self.refresh_expires_in)
        return None


class KeycloakError(Exception):
    """Base exception for Keycloak errors."""
    pass


class KeycloakAuthenticationError(KeycloakError):
    """Raised when authentication fails."""
    pass


class KeycloakTokenError(KeycloakError):
    """Raised when token operations fail."""
    pass


class KeycloakClient:
    """
    Async client for Keycloak operations.
    
    Uses httpx for async HTTP requests to Keycloak endpoints.
    Handles password grant, token refresh, and logout.
    """
    
    def __init__(
        self,
        server_url: Optional[str] = None,
        realm: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize the Keycloak client.
        
        Args:
            server_url: Keycloak server URL (default: from settings)
            realm: Keycloak realm (default: from settings)
            client_id: Client ID (default: from settings)
            client_secret: Client secret (default: from settings)
        """
        self.server_url = server_url or settings.keycloak_server_url
        self.realm = realm or settings.keycloak_realm
        self.client_id = client_id or settings.keycloak_client_id
        self.client_secret = client_secret or settings.keycloak_client_secret
        
    @property
    def token_endpoint(self) -> str:
        """Get the token endpoint URL."""
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
    
    @property
    def logout_endpoint(self) -> str:
        """Get the logout endpoint URL."""
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/logout"
    
    @property
    def userinfo_endpoint(self) -> str:
        """Get the userinfo endpoint URL."""
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
    
    async def token_exchange(
        self,
        username: str,
        password: str,
        scope: str = "openid email profile",
    ) -> TokenResponse:
        """
        Exchange username/password for tokens using Resource Owner Password Grant.
        
        Args:
            username: User's username or email
            password: User's password
            scope: OAuth scopes to request
            
        Returns:
            TokenResponse with access and refresh tokens
            
        Raises:
            KeycloakAuthenticationError: If credentials are invalid
            KeycloakTokenError: If token exchange fails
        """
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password,
            "scope": scope,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    timeout=10.0,
                )
                
                if response.status_code == 401:
                    raise KeycloakAuthenticationError("Invalid username or password")
                
                if response.status_code == 400:
                    error_data = response.json()
                    error_desc = error_data.get("error_description", "Bad request")
                    if "invalid_grant" in str(error_data.get("error", "")):
                        raise KeycloakAuthenticationError(error_desc)
                    raise KeycloakTokenError(error_desc)
                
                response.raise_for_status()
                
                data = response.json()
                return TokenResponse(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_in=data.get("expires_in", 300),
                    refresh_token=data.get("refresh_token"),
                    refresh_expires_in=data.get("refresh_expires_in"),
                    scope=data.get("scope"),
                    id_token=data.get("id_token"),
                )
                
            except httpx.HTTPError as e:
                raise KeycloakTokenError(f"Token exchange failed: {e}")
    
    async def refresh_token(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        """
        Refresh tokens using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            TokenResponse with new access and refresh tokens
            
        Raises:
            KeycloakTokenError: If refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    timeout=10.0,
                )
                
                if response.status_code == 400:
                    error_data = response.json()
                    error_desc = error_data.get("error_description", "Refresh failed")
                    raise KeycloakTokenError(error_desc)
                
                response.raise_for_status()
                
                data = response.json()
                return TokenResponse(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_in=data.get("expires_in", 300),
                    refresh_token=data.get("refresh_token"),
                    refresh_expires_in=data.get("refresh_expires_in"),
                    scope=data.get("scope"),
                    id_token=data.get("id_token"),
                )
                
            except httpx.HTTPError as e:
                raise KeycloakTokenError(f"Token refresh failed: {e}")
    
    async def logout(
        self,
        refresh_token: str,
    ) -> bool:
        """
        Logout user by invalidating refresh token.
        
        Args:
            refresh_token: Refresh token to invalidate
            
        Returns:
            True if logout successful
            
        Raises:
            KeycloakError: If logout fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.logout_endpoint,
                    data=data,
                    timeout=10.0,
                )
                
                # Keycloak returns 204 No Content on success
                # Also accept 200 as success
                if response.status_code in (200, 204):
                    return True
                    
                # Log but don't fail on other responses
                return False
                
            except httpx.HTTPError as e:
                raise KeycloakError(f"Logout failed: {e}")
    
    async def get_userinfo(
        self,
        access_token: str,
    ) -> dict:
        """
        Get user information from Keycloak userinfo endpoint.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User information dictionary
            
        Raises:
            KeycloakError: If request fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                raise KeycloakError(f"Failed to get user info: {e}")


# Singleton instance
keycloak_client = KeycloakClient()

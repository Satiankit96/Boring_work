"""
Core Configuration Module
=========================
Role: Load and validate all environment variables using pydantic-settings.
This is the single source of truth for application configuration.
Never hardcode values — everything comes from .env via this module.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

# Get the backend directory (where this module lives)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Pydantic automatically reads from .env file and validates types.
    """
    
    # Application
    app_env: str = "development"
    
    # Security (legacy - kept for backward compatibility)
    secret_key: str = "change_me_min_32_characters_long_please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    
    # Keycloak Configuration
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "my-app"
    keycloak_client_id: str = "my-backend"
    keycloak_client_secret: str = "backend-secret-change-in-production"
    keycloak_frontend_client_id: str = "my-frontend"
    
    # Auth mode: "local" for bcrypt/JWT, "keycloak" for Keycloak IdP
    auth_mode: str = "keycloak"
    
    # Database - use absolute path
    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'auth.db'}"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def keycloak_issuer(self) -> str:
        """Get the Keycloak issuer URL."""
        return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}"
    
    @property
    def keycloak_token_endpoint(self) -> str:
        """Get the Keycloak token endpoint."""
        return f"{self.keycloak_issuer}/protocol/openid-connect/token"
    
    @property
    def keycloak_jwks_uri(self) -> str:
        """Get the Keycloak JWKS endpoint."""
        return f"{self.keycloak_issuer}/protocol/openid-connect/certs"
    
    @property
    def keycloak_logout_endpoint(self) -> str:
        """Get the Keycloak logout endpoint."""
        return f"{self.keycloak_issuer}/protocol/openid-connect/logout"


# Singleton instance — import this throughout the app
settings = Settings()

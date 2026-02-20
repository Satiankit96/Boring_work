"""
Core Configuration Module
=========================
Role: Load and validate all environment variables using pydantic-settings.
This is the single source of truth for application configuration.
Never hardcode values — everything comes from .env via this module.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Pydantic automatically reads from .env file and validates types.
    """
    
    # Application
    app_env: str = "development"
    
    # Security
    secret_key: str = "change_me_min_32_characters_long_please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/auth.db"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton instance — import this throughout the app
settings = Settings()

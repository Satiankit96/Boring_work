# core/config.py
# Role: Loads all application configuration from environment variables via pydantic-settings.
# This is the single source of truth for config. Nothing else reads os.environ directly.

from pydantic_settings import BaseSettings
from pydantic import field_validator
import json


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "change_me_min_32_characters_long_please_default"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    database_url: str = "sqlite+aiosqlite:///./data/auth.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

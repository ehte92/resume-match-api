"""
Application configuration management using Pydantic Settings.
Loads environment variables from .env file with type validation.
"""

import json
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    """

    # Database Configuration
    DATABASE_URL: str

    # Security Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Application Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # File Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = 5
    UPLOAD_TEMP_DIR: str = "/tmp/resume_uploads"
    # fmt: off
    ALLOWED_UPLOAD_TYPES: str = '["application/pdf","application/vnd.openxmlformats-officedocument.wordprocessingml.document"]'  # noqa: E501
    # fmt: on

    # Cloudflare R2 / S3 Storage Configuration
    STORAGE_BACKEND: str = "local"  # local or r2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "resume-uploads"
    R2_REGION: str = "auto"  # R2 uses "auto" for region
    R2_PUBLIC_URL: str = ""  # Optional: Custom domain for public access

    # OpenRouter AI Configuration
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_MAX_TOKENS: int = 2000
    OPENROUTER_TEMPERATURE: float = 0.7
    OPENROUTER_SITE_URL: str = "https://resumematch.ai"
    OPENROUTER_APP_NAME: str = "ResumeMatch-AI"
    ENABLE_AI_SUGGESTIONS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from JSON string to list."""
        if isinstance(v, str):
            try:
                origins = json.loads(v)
                if isinstance(origins, list):
                    return origins
            except json.JSONDecodeError:
                pass
        return ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("ALLOWED_UPLOAD_TYPES")
    @classmethod
    def parse_allowed_upload_types(cls, v: str) -> List[str]:
        """Parse allowed upload types from JSON string to list."""
        if isinstance(v, str):
            try:
                types = json.loads(v)
                if isinstance(types, list):
                    return types
            except json.JSONDecodeError:
                pass
        return [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are loaded once and reused.
    This improves performance and ensures consistency.

    Returns:
        Settings: Application settings instance
    """
    return Settings()

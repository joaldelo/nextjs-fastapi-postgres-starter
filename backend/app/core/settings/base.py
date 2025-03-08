from typing import Any, Dict, Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator


class BaseAppSettings(BaseSettings):
    """Base settings class that all environment settings inherit from."""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Chatbot API"
    VERSION: str = "0.1.0"
    
    # Database Connection Pool Settings - Common defaults that can be overridden
    DB_POOL_TIMEOUT: int = 30
    
    # Required fields for environment-specific settings
    BACKEND_CORS_ORIGINS: List[str]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Validate and process CORS origins."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    model_config = SettingsConfigDict(
        # Environment variables take precedence over .env file
        env_file=None,  # Don't load from .env by default in container
        
        # Use case-sensitive environment variables
        case_sensitive=True,
        
        # Allow extra fields in case we need to add more settings
        extra="allow",
        
        # Validate all fields during assignment
        validate_assignment=True,
        
        # Use environment variables with this prefix
        env_prefix="APP_"
    ) 
from .base import BaseAppSettings
from pydantic import Field, field_validator
from typing import List
import logging


class DevelopmentSettings(BaseAppSettings):
    """Development environment settings."""
    
    # Environment Settings
    ENV: str = "development"
    DEBUG: bool = True
    
    # Development-specific settings
    RELOAD: bool = True
    LOG_LEVEL: str = "debug"
    LOG_FORMAT: str = "json"
    
    @property
    def LOGGING_LEVEL(self) -> str:
        """Get the uppercase logging level for Python's logging module."""
        return self.LOG_LEVEL.upper()
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["critical", "error", "warning", "info", "debug", "trace"]
        v = v.lower()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v
    
    # CORS Settings - Development specific
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="List of origins that are allowed to make cross-site HTTP requests"
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Database Settings - These defaults can be overridden by environment variables
    POSTGRES_USER: str = Field(
        default="postgres",
        description="Database user, can be overridden by APP_POSTGRES_USER"
    )
    POSTGRES_PASSWORD: str = Field(
        default="postgres",
        description="Database password, can be overridden by APP_POSTGRES_PASSWORD"
    )
    POSTGRES_HOST: str = Field(
        default="localhost",
        description="Database host, can be overridden by APP_POSTGRES_HOST"
    )
    POSTGRES_PORT: int = Field(
        default=5432,
        description="Database port, can be overridden by APP_POSTGRES_PORT"
    )
    POSTGRES_DB: str = Field(
        default="postgres",
        description="Database name, can be overridden by APP_POSTGRES_DB"
    )
    
    # Database Pool Settings - Development specific
    DB_POOL_SIZE: int = Field(
        default=5,
        description="Database pool size, can be overridden by APP_DB_POOL_SIZE"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        description="Database max overflow, can be overridden by APP_DB_MAX_OVERFLOW"
    )
    
    # Computed Settings
    @property
    def DATABASE_URL(self) -> str:
        """Get the PostgreSQL database URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        """Get the async PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def display_config(self) -> dict:
        """Display the current configuration with source information."""
        return {
            "database": {
                "user": f"{self.POSTGRES_USER} (from {'env' if 'APP_POSTGRES_USER' in self.model_fields_set else 'default'})",
                "host": f"{self.POSTGRES_HOST} (from {'env' if 'APP_POSTGRES_HOST' in self.model_fields_set else 'default'})",
                "port": f"{self.POSTGRES_PORT} (from {'env' if 'APP_POSTGRES_PORT' in self.model_fields_set else 'default'})",
                "database": f"{self.POSTGRES_DB} (from {'env' if 'APP_POSTGRES_DB' in self.model_fields_set else 'default'})",
                "pool_size": f"{self.DB_POOL_SIZE} (from {'env' if 'APP_DB_POOL_SIZE' in self.model_fields_set else 'default'})",
                "max_overflow": f"{self.DB_MAX_OVERFLOW} (from {'env' if 'APP_DB_MAX_OVERFLOW' in self.model_fields_set else 'default'})",
            },
            "computed_urls": {
                "sync_url": self.DATABASE_URL,
                "async_url": self.DATABASE_URL_ASYNC,
            }
        }

    model_config = BaseAppSettings.model_config 
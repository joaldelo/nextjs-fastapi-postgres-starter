from app.core.settings import settings
from app.core.logging import logger


def log_startup_config() -> None:
    """Log the application configuration on startup."""
    config = settings.display_config()
    
    logger.info(
        "Application starting",
        extra={
            "environment": settings.ENV,
            "debug_mode": settings.DEBUG,
            "database_config": config["database"],
            "database_urls": config["computed_urls"]
        }
    ) 
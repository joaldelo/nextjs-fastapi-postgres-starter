from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.core.settings import settings
from app.core.logging import logger

logger.info(
    "Initializing database connections",
    extra={
        "database_host": settings.POSTGRES_HOST,
        "database_name": settings.POSTGRES_DB,
        "pool_size": settings.DB_POOL_SIZE
    }
)

# Create engines using settings
sync_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

try:
    # Create tables
    Base.metadata.create_all(sync_engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(
        "Failed to create database tables",
        extra={"error": str(e)}
    )
    raise

# Async engine
engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT
)


def get_db():
    """Dependency function to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed") 
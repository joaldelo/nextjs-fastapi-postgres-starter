from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

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

# Async engine
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

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

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get an async database session.
    Usage in FastAPI:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_async_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            logger.debug("Async database session closed")

def get_db():
    """Dependency function to get a synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed") 
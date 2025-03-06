from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

_main_uri = "postgres:postgres@localhost:5432/postgres"
_sync_uri = f"postgresql://{_main_uri}"
_async_uri = f"postgresql+asyncpg://{_main_uri}"

sync_engine = create_engine(_sync_uri)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base.metadata.create_all(sync_engine)

engine = create_async_engine(_async_uri)


def get_db():
    """Dependency function to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

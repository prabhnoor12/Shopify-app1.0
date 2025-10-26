from typing import AsyncGenerator
import logging
from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from my_app.dependencies.config import get_settings
import redis.asyncio as redis

# Get settings
settings = get_settings()

# Database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create the SQLAlchemy async engine with connection pooling
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DB_ECHO,  # Log SQL queries
)

# Create a SyncEngine for use in background threads
sync_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DB_ECHO,
)

# Create a AsyncSessionLocal class
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Create a SessionLocal class for synchronous sessions
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Synchronous DB session generator for jobs and scripts
def get_db_session():
    """
    Yields a synchronous database session for use in jobs and scripts.
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a declarative base for SQLAlchemy models
Base = declarative_base()

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


# Dependency to get a database session with transaction management
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    This dependency provides an async database session with proper transaction management.
    It yields a session, and handles commit, rollback, and closing.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error(f"Database transaction failed: {e}")
            raise


async def get_redis():
    """Dependency to get a Redis client."""
    return redis_client


async def check_db_connection():
    """Check if the database connection is alive."""
    try:
        async with engine.connect():
            return True
    except Exception as e:
        logging.error(f"Database connection check failed: {e}")
        return False


async def init_db():
    """Initialize the database and create tables."""
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Use with caution
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database initialized.")


# Optional: Add logging for connection pool events
@event.listens_for(Engine, "connect")
def connect(dbapi_connection, connection_record):
    logging.info("New DB connection")


@event.listens_for(Engine, "close")
def close(dbapi_connection, connection_record):
    logging.info("DB connection closed")

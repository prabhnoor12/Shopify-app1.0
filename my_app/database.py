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


def _mask_password(url: str) -> str:
    """Return a masked version of the DB URL for safe logging (hide password)."""
    try:
        # naive mask: replace everything between first ':' after '//' and the next '@'
        if "@" in url and "//" in url:
            prefix, rest = url.split("//", 1)
            userinfo, host = rest.split("@", 1)
            if ":" in userinfo:
                user, _pw = userinfo.split(":", 1)
                return f"{prefix}//{user}:***@{host}"
    except Exception:
        pass
    return url


def print_db_url_and_test():
    import asyncio
    print(f"[Startup] Raw DATABASE_URL: {SQLALCHEMY_DATABASE_URL}")
    print(f"[Startup] Async DB URL: {async_url}")
    print(f"[Startup] Sync DB URL: {sync_url}")
    try:
        async def test():
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
        asyncio.run(test())
        print("[Startup] Database connection test succeeded.")
    except Exception as e:
        print(f"[Startup] Database connection test failed: {e}")

print_db_url_and_test()


if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set or is empty. Set the DATABASE_URL environment variable to a valid SQLAlchemy URL."
    )

# Normalize/derive async and sync URLs
# If the URL is 'postgresql+asyncpg://', use it for async engine and strip '+asyncpg' for sync engine.
# If the URL is 'postgresql://', auto-add '+asyncpg' for the async engine.
async_url = SQLALCHEMY_DATABASE_URL
sync_url = SQLALCHEMY_DATABASE_URL

if SQLALCHEMY_DATABASE_URL.startswith("postgresql+asyncpg://"):
    sync_url = SQLALCHEMY_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    async_url = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

masked = _mask_password(SQLALCHEMY_DATABASE_URL)
logging.info(f"Using database URL: {masked}")

try:
    # Create the SQLAlchemy async engine with connection pooling
    engine = create_async_engine(
        async_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        echo=settings.DB_ECHO,  # Log SQL queries
    )

    # Create a SyncEngine for use in background threads (use sync driver)
    sync_engine = create_engine(
        sync_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        echo=settings.DB_ECHO,
    )
except Exception as exc:
    logging.error(
        "Failed to create database engine. Please check DATABASE_URL format and installed DB drivers."
    )
    logging.debug(f"Raw DATABASE_URL (masked): {masked}")
    raise

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

import pytest
import pytest_asyncio
import json
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis as AsyncRedis
import fakeredis.aioredis

from .my_app.models.base import Base
from my_app.services.session_service import SessionService
from my_app.crud import session_crud
from my_app.schemas.session import SessionCreate

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create an in-memory SQLite async engine for tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine):
    """Create a session factory for tests."""
    return async_sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
    )


@pytest_asyncio.fixture(scope="function")
async def mock_redis_client():
    """Create a mock Redis client for tests."""
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.flushall()


@pytest_asyncio.fixture(scope="function")
def session_service(test_session_factory, mock_redis_client):
    """Create an instance of the SessionService for tests."""
    return SessionService(
        session_factory=test_session_factory, redis_client=mock_redis_client
    )


@pytest.mark.asyncio
async def test_create_session(
    session_service: SessionService,
    test_session_factory: async_sessionmaker[AsyncSession],
    mock_redis_client: AsyncRedis,
):
    """Test creating a new session."""
    user_id = 1
    ip_address = "127.0.0.1"
    user_agent = "TestAgent"

    session = await session_service.create_session(user_id, ip_address, user_agent)

    assert session is not None
    assert session.user_id == user_id
    assert session.ip_address == ip_address
    assert session.user_agent == user_agent
    assert session.expires_at > datetime.now(UTC)

    # Verify it's in the database
    async with test_session_factory() as db:
        db_session = await session_crud.get_session(db, session.id)
        assert db_session is not None
        assert db_session.id == session.id

    # Verify it's in Redis
    cached_session_json = await mock_redis_client.get(f"session:{session.id}")
    assert cached_session_json is not None
    cached_session = json.loads(cached_session_json)
    assert cached_session["id"] == session.id


@pytest.mark.asyncio
async def test_get_session_from_cache(
    session_service: SessionService, mock_redis_client: AsyncRedis
):
    """Test retrieving a session from the Redis cache."""
    session_id = "test_session_123"
    session_data = {
        "id": session_id,
        "user_id": 1,
        "ip_address": "127.0.0.1",
        "user_agent": "TestAgent",
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "last_activity": datetime.now(UTC).isoformat(),
        "data": {},
    }
    await mock_redis_client.set(f"session:{session_id}", json.dumps(session_data))

    retrieved_session = await session_service.get_session(session_id)

    assert retrieved_session is not None
    assert retrieved_session.id == session_id
    assert retrieved_session.user_id == session_data["user_id"]


@pytest.mark.asyncio
async def test_get_session_from_db(
    session_service: SessionService,
    test_session_factory: async_sessionmaker[AsyncSession],
    mock_redis_client: AsyncRedis,
):
    """Test retrieving a session from the DB when not in cache."""
    user_id = 2
    session_create = SessionCreate(
        id="db_session_456",
        user_id=user_id,
        ip_address="192.168.1.1",
        user_agent="DBAgent",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    async with test_session_factory() as db:
        await session_crud.create_session(db, session_create.model_dump())

    # Ensure cache is empty
    assert await mock_redis_client.get(f"session:{session_create.id}") is None

    retrieved_session = await session_service.get_session(session_create.id)

    assert retrieved_session is not None
    assert retrieved_session.id == session_create.id
    assert retrieved_session.user_id == user_id

    # Verify it's now in Redis
    cached_session_json = await mock_redis_client.get(f"session:{session_create.id}")
    assert cached_session_json is not None


@pytest.mark.asyncio
async def test_get_expired_session(
    session_service: SessionService,
    test_session_factory: async_sessionmaker[AsyncSession],
):
    """Test that an expired session is not returned."""
    session_create = SessionCreate(
        id="expired_session_789",
        user_id=3,
        ip_address="10.0.0.1",
        user_agent="ExpiredAgent",
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )

    async with test_session_factory() as db:
        await session_crud.create_session(db, session_create.model_dump())

    retrieved_session = await session_service.get_session(session_create.id)
    assert retrieved_session is None


@pytest.mark.asyncio
async def test_invalidate_session(
    session_service: SessionService,
    test_session_factory: async_sessionmaker[AsyncSession],
    mock_redis_client: AsyncRedis,
):
    """Test invalidating (deleting) a session."""
    session = await session_service.create_session(4, "1.1.1.1", "InvalidateAgent")

    # Verify it exists before invalidation
    assert await mock_redis_client.get(f"session:{session.id}") is not None

    result = await session_service.invalidate_session(session.id)
    assert result is True

    # Verify it's deleted from Redis and DB
    assert await mock_redis_client.get(f"session:{session.id}") is None
    async with test_session_factory() as db:
        db_session = await session_crud.get_session(db, session.id)
        assert db_session is None


@pytest.mark.asyncio
async def test_update_session_data(
    session_service: SessionService, mock_redis_client: AsyncRedis
):
    """Test updating custom data in a session."""
    session = await session_service.create_session(5, "2.2.2.2", "UpdateAgent")
    new_data = {"theme": "dark", "notifications": "off"}

    updated_session = await session_service.update_session_data(session.id, new_data)

    assert updated_session is not None
    assert updated_session.data == new_data

    # Verify the updated data is in Redis
    cached_session_json = await mock_redis_client.get(f"session:{session.id}")
    cached_session = json.loads(cached_session_json)
    assert cached_session["data"] == new_data


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(
    session_service: SessionService,
    test_session_factory: async_sessionmaker[AsyncSession],
):
    """Test the cleanup of expired sessions from the database."""
    # Create a valid session
    valid_session_create = SessionCreate(
        id="valid_session",
        user_id=6,
        ip_address="3.3.3.3",
        user_agent="ValidAgent",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    # Create an expired session
    expired_session_create = SessionCreate(
        id="expired_session",
        user_id=7,
        ip_address="4.4.4.4",
        user_agent="ExpiredAgent",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    async with test_session_factory() as db:
        await session_crud.create_session(db, valid_session_create.model_dump())
        await session_crud.create_session(db, expired_session_create.model_dump())

    await session_service.cleanup_expired_sessions()

    async with test_session_factory() as db:
        # The valid session should still exist
        assert await session_crud.get_session(db, "valid_session") is not None
        # The expired session should be deleted
        assert await session_crud.get_session(db, "expired_session") is None

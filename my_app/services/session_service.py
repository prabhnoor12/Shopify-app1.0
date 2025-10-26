import secrets
import json
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models.session import Session as SessionModel
from ..crud import session_crud
from ..schemas.session import SessionCreate, SessionUpdate


class SessionService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        redis_client: Redis,
    ):
        self.session_factory = session_factory
        self.redis_client = redis_client
        self.session_duration = timedelta(hours=24)  # Default session duration

    def _generate_session_id(self) -> str:
        return secrets.token_urlsafe(32)

    async def create_session(
        self, user_id: int, ip_address: str, user_agent: str
    ) -> SessionModel:
        session_id = self._generate_session_id()
        expires_at = datetime.now(UTC) + self.session_duration
        session_create = SessionCreate(
            id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        async with self.session_factory() as session:
            db_session = await session_crud.create_session(
                session, session_create.model_dump()
            )
            await self.redis_client.set(
                f"session:{session_id}",
                json.dumps(db_session.to_dict()),
                ex=self.session_duration,
            )
            return db_session

    async def get_session(self, session_id: str) -> Optional[SessionModel]:
        cached_session = await self.redis_client.get(f"session:{session_id}")
        if cached_session:
            session_data = json.loads(cached_session)
            session_data["created_at"] = datetime.fromisoformat(
                session_data["created_at"]
            )
            session_data["expires_at"] = datetime.fromisoformat(
                session_data["expires_at"]
            )
            return SessionModel(**session_data)

        async with self.session_factory() as session:
            db_session = await session_crud.get_session(session, session_id)
            if db_session and db_session.expires_at > datetime.now(UTC):
                await self.redis_client.set(
                    f"session:{session_id}",
                    json.dumps(db_session.to_dict()),
                    ex=self.session_duration,
                )
                return db_session
        return None

    async def list_sessions(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[SessionModel]:
        async with self.session_factory() as session:
            return await session_crud.get_sessions_by_user(
                session, user_id, skip=skip, limit=limit
            )

    async def update_session_data(
        self, session_id: str, data: Dict[str, Any]
    ) -> Optional[SessionModel]:
        async with self.session_factory() as session:
            session_update = SessionUpdate(data=data, last_activity=datetime.now(UTC))
            db_session = await session_crud.update_session(
                session, session_id, session_update.model_dump(exclude_unset=True)
            )
            if db_session:
                await self.redis_client.set(
                    f"session:{session_id}",
                    json.dumps(db_session.to_dict()),
                    ex=self.session_duration,
                )
            return db_session

    async def invalidate_session(self, session_id: str) -> bool:
        await self.redis_client.delete(f"session:{session_id}")
        async with self.session_factory() as session:
            db_session = await session_crud.delete_session(session, session_id)
            return db_session is not None

    async def cleanup_expired_sessions(self):
        async with self.session_factory() as session:
            await session_crud.delete_expired_sessions(session)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from my_app.models.session import Session as SessionModel


async def get_session(db: AsyncSession, session_id: str):
    result = await db.execute(
        select(SessionModel).filter(SessionModel.id == session_id)
    )
    return result.scalars().first()


async def get_sessions(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(SessionModel).offset(skip).limit(limit))
    return result.scalars().all()


async def create_session(db: AsyncSession, session: dict):
    db_session = SessionModel(**session)
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


async def update_session(db: AsyncSession, session_id: str, session_update: dict):
    db_session = await get_session(db, session_id)
    if db_session:
        for key, value in session_update.items():
            setattr(db_session, key, value)
        await db.commit()
        await db.refresh(db_session)
    return db_session


async def delete_session(db: AsyncSession, session_id: str):
    db_session = await get_session(db, session_id)
    if db_session:
        await db.delete(db_session)
        await db.commit()
    return db_session

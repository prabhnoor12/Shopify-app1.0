from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from ..models.shop import ShopifyUser
import logging
import json
from ..dependencies.redis import get_redis_client

logger = logging.getLogger(__name__)


# STUB: revoke_user_token implementation for compatibility
async def revoke_user_token(db: AsyncSession, shop_domain: str) -> bool:
    """
    Stub for revoking a user's token. Implement actual logic as needed.
    """
    try:
        result = await db.execute(
            select(ShopifyUser).filter(ShopifyUser.shop_domain == shop_domain)
        )
        user = result.scalars().first()
        if user:
            user.access_token = None
            await db.commit()
            await db.refresh(user)
            redis = get_redis_client()
            await redis.delete(f"user:{shop_domain}")
            return True
        return False
    except Exception as e:
        await db.rollback()
        logger.error(f"Error revoking user token: {e}")
        raise


async def create_or_update_user(
    db: AsyncSession, shop_domain: str, access_token: str
) -> ShopifyUser:
    """
    Creates a new ShopifyUser or updates an existing one.
    """
    try:
        result = await db.execute(
            select(ShopifyUser).filter(ShopifyUser.shop_domain == shop_domain)
        )
        user = result.scalars().first()
        if user:
            user.access_token = access_token
        else:
            user = ShopifyUser(shop_domain=shop_domain, access_token=access_token)
            db.add(user)
        await db.commit()
        await db.refresh(user)
        # Invalidate cache
        redis = get_redis_client()
        await redis.delete(f"user:{shop_domain}")
        return user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating or updating user: {e}")
        raise


async def get_user_by_domain(
    db: AsyncSession, shop_domain: str
) -> Optional[ShopifyUser]:
    """
    Retrieve a ShopifyUser by shop domain.
    """
    redis = get_redis_client()
    cached_user = await redis.get(f"user:{shop_domain}")
    if cached_user:
        user_dict = json.loads(cached_user)
        return ShopifyUser(**user_dict)

    result = await db.execute(
        select(ShopifyUser).filter(ShopifyUser.shop_domain == shop_domain)
    )
    user = result.scalars().first()
    if user:
        user_dict = {c.name: getattr(user, c.name) for c in user.__table__.columns}
        await redis.set(
            f"user:{shop_domain}", json.dumps(user_dict, default=str), ex=3600
        )  # Cache for 1 hour
    return user


async def get_all_users(db: AsyncSession) -> List[ShopifyUser]:
    """
    Retrieve all Shopify users.
    """
    result = await db.execute(select(ShopifyUser))
    return result.scalars().all()


async def update_user_access_token(
    db: AsyncSession, shop_domain: str, new_token: str
) -> Optional[ShopifyUser]:
    """
    Update the access token for a ShopifyUser.
    """
    try:
        result = await db.execute(
            select(ShopifyUser).filter(ShopifyUser.shop_domain == shop_domain)
        )
        user = result.scalars().first()
        if user:
            user.access_token = new_token
            await db.commit()
            await db.refresh(user)
            # Invalidate cache
            redis = get_redis_client()
            await redis.delete(f"user:{shop_domain}")
        return user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user access token: {e}")
        raise


async def delete_user(db: AsyncSession, shop_domain: str) -> bool:
    """
    Delete a ShopifyUser by shop domain.
    Returns True if deleted, False if not found.
    """
    try:
        result = await db.execute(
            select(ShopifyUser).filter(ShopifyUser.shop_domain == shop_domain)
        )
        user = result.scalars().first()
        if user:
            await db.delete(user)
            await db.commit()
            # Invalidate cache
            redis = get_redis_client()
            await redis.delete(f"user:{shop_domain}")
            return True
        return False
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise

"""
User Limit CRUD operations.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserLimit
from utils.logs import get_logger

db_limits_logger = get_logger("db.limits")


class UserLimitCRUD:
    """CRUD operations for UserLimit table."""
    
    @staticmethod
    async def set_limit(db: AsyncSession, username: str, limit: int) -> UserLimit:
        """Set or update limit for a user."""
        db_limits_logger.debug(f"📝 Setting limit for user: {username} -> {limit}")
        result = await db.execute(select(UserLimit).where(UserLimit.username == username))
        user_limit = result.scalar_one_or_none()
        
        if user_limit:
            db_limits_logger.debug(f"✏️ Updating existing limit for: {username}")
            user_limit.limit = limit
            user_limit.updated_at = datetime.utcnow()
        else:
            db_limits_logger.debug(f"➕ Creating new limit for: {username}")
            user_limit = UserLimit(username=username, limit=limit)
            db.add(user_limit)
        
        await db.flush()
        db_limits_logger.info(f"✅ Limit set for {username}: {limit}")
        return user_limit
    
    @staticmethod
    async def get_limit(db: AsyncSession, username: str) -> Optional[int]:
        """Get limit for a user. Returns None if no special limit set."""
        db_limits_logger.debug(f"🔍 Getting limit for user: {username}")
        result = await db.execute(select(UserLimit).where(UserLimit.username == username))
        user_limit = result.scalar_one_or_none()
        if user_limit:
            db_limits_logger.debug(f"✅ Found limit for {username}: {user_limit.limit}")
        else:
            db_limits_logger.debug(f"ℹ️ No special limit for {username}")
        return user_limit.limit if user_limit else None
    
    @staticmethod
    async def get_all(db: AsyncSession) -> dict[str, int]:
        """Get all special limits as a dictionary."""
        db_limits_logger.debug("📋 Getting all special limits")
        result = await db.execute(select(UserLimit))
        limits = result.scalars().all()
        limits_dict = {ul.username: ul.limit for ul in limits}
        db_limits_logger.debug(f"✅ Retrieved {len(limits_dict)} special limits")
        return limits_dict
    
    @staticmethod
    async def delete(db: AsyncSession, username: str) -> bool:
        """Remove special limit for a user (will use general limit)."""
        db_limits_logger.debug(f"🗑️ Deleting limit for user: {username}")
        result = await db.execute(delete(UserLimit).where(UserLimit.username == username))
        deleted = result.rowcount > 0
        if deleted:
            db_limits_logger.info(f"✅ Deleted special limit for {username}")
        else:
            db_limits_logger.debug(f"ℹ️ No special limit found for {username}")
        return deleted

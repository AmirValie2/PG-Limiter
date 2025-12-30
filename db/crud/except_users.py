"""
Except User CRUD operations (whitelist).
"""

from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ExceptUser
from utils.logs import get_logger

db_except_logger = get_logger("db.except")


class ExceptUserCRUD:
    """CRUD operations for ExceptUser table (whitelist)."""
    
    @staticmethod
    async def add(db: AsyncSession, username: str, reason: Optional[str] = None, created_by: Optional[str] = None) -> ExceptUser:
        """Add user to exception list."""
        db_except_logger.debug(f"📝 Adding to exception list: {username}")
        result = await db.execute(select(ExceptUser).where(ExceptUser.username == username))
        except_user = result.scalar_one_or_none()
        
        if except_user:
            db_except_logger.debug(f"✏️ Updating exception for: {username}")
            except_user.reason = reason
            except_user.created_by = created_by
        else:
            db_except_logger.debug(f"➕ Creating new exception for: {username}")
            except_user = ExceptUser(username=username, reason=reason, created_by=created_by)
            db.add(except_user)
        
        await db.flush()
        db_except_logger.info(f"✅ User {username} added to exception list")
        return except_user
    
    @staticmethod
    async def remove(db: AsyncSession, username: str) -> bool:
        """Remove user from exception list."""
        db_except_logger.debug(f"🗑️ Removing from exception list: {username}")
        result = await db.execute(delete(ExceptUser).where(ExceptUser.username == username))
        removed = result.rowcount > 0
        if removed:
            db_except_logger.info(f"✅ User {username} removed from exception list")
        else:
            db_except_logger.debug(f"ℹ️ User {username} was not in exception list")
        return removed
    
    @staticmethod
    async def is_excepted(db: AsyncSession, username: str) -> bool:
        """Check if user is in exception list."""
        db_except_logger.debug(f"🔍 Checking if excepted: {username}")
        result = await db.execute(select(ExceptUser).where(ExceptUser.username == username))
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[str]:
        """Get all excepted usernames."""
        db_except_logger.debug("📋 Getting all excepted usernames")
        result = await db.execute(select(ExceptUser))
        users = [eu.username for eu in result.scalars().all()]
        db_except_logger.debug(f"✅ Found {len(users)} excepted users")
        return users
    
    @staticmethod
    async def get_all_with_details(db: AsyncSession) -> List[ExceptUser]:
        """Get all excepted users with full details."""
        db_except_logger.debug("📋 Getting all excepted users with details")
        result = await db.execute(select(ExceptUser))
        users = result.scalars().all()
        db_except_logger.debug(f"✅ Retrieved {len(users)} excepted users")
        return users

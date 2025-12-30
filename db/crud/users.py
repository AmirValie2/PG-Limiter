"""
User CRUD operations.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from utils.logs import get_logger

db_users_logger = get_logger("db.users")


class UserCRUD:
    """CRUD operations for Users table."""
    
    @staticmethod
    async def create_or_update(
        db: AsyncSession,
        username: str,
        status: str = "active",
        owner_id: Optional[int] = None,
        owner_username: Optional[str] = None,
        group_ids: Optional[List[int]] = None,
        data_limit: Optional[float] = None,
        used_traffic: float = 0,
        expire_at: Optional[datetime] = None,
        note: Optional[str] = None,
    ) -> User:
        """Create or update a user."""
        db_users_logger.debug(f"📝 Creating/updating user: {username}")
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if user:
            db_users_logger.debug(f"✏️ Updating existing user: {username}")
            user.status = status
            user.owner_id = owner_id
            user.owner_username = owner_username
            user.group_ids = group_ids or []
            user.data_limit = data_limit
            user.used_traffic = used_traffic
            user.expire_at = expire_at
            user.note = note
            user.last_synced_at = datetime.utcnow()
        else:
            db_users_logger.debug(f"➕ Creating new user: {username}")
            user = User(
                username=username,
                status=status,
                owner_id=owner_id,
                owner_username=owner_username,
                group_ids=group_ids or [],
                data_limit=data_limit,
                used_traffic=used_traffic,
                expire_at=expire_at,
                note=note,
            )
            db.add(user)
        
        await db.flush()
        return user
    
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        db_users_logger.debug(f"🔍 Getting user by username: {username}")
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user:
            db_users_logger.debug(f"✅ Found user: {username}")
        else:
            db_users_logger.debug(f"⚠️ User not found: {username}")
        return user
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[User]:
        """Get all users."""
        db_users_logger.debug("📋 Getting all users from database")
        result = await db.execute(select(User))
        users = result.scalars().all()
        db_users_logger.debug(f"✅ Retrieved {len(users)} users")
        return users
    
    @staticmethod
    async def get_by_owner(db: AsyncSession, owner_id: int) -> List[User]:
        """Get users by owner/admin ID."""
        db_users_logger.debug(f"🔍 Getting users by owner ID: {owner_id}")
        result = await db.execute(select(User).where(User.owner_id == owner_id))
        users = result.scalars().all()
        db_users_logger.debug(f"✅ Found {len(users)} users for owner ID {owner_id}")
        return users
    
    @staticmethod
    async def get_by_owner_username(db: AsyncSession, owner_username: str) -> List[User]:
        """Get users by owner/admin username."""
        db_users_logger.debug(f"🔍 Getting users by owner username: {owner_username}")
        result = await db.execute(select(User).where(User.owner_username == owner_username))
        users = result.scalars().all()
        db_users_logger.debug(f"✅ Found {len(users)} users for owner {owner_username}")
        return users
    
    @staticmethod
    async def get_by_group(db: AsyncSession, group_id: int) -> List[User]:
        """Get users in a specific group."""
        db_users_logger.debug(f"🔍 Getting users by group ID: {group_id}")
        result = await db.execute(select(User))
        users = result.scalars().all()
        filtered = [u for u in users if group_id in (u.group_ids or [])]
        db_users_logger.debug(f"✅ Found {len(filtered)} users in group {group_id}")
        return filtered
    
    @staticmethod
    async def get_by_status(db: AsyncSession, status: str) -> List[User]:
        """Get users by status."""
        db_users_logger.debug(f"🔍 Getting users by status: {status}")
        result = await db.execute(select(User).where(User.status == status))
        users = result.scalars().all()
        db_users_logger.debug(f"✅ Found {len(users)} users with status {status}")
        return users
    
    @staticmethod
    async def delete(db: AsyncSession, username: str) -> bool:
        """Delete a user."""
        db_users_logger.debug(f"🗑️ Deleting user: {username}")
        result = await db.execute(delete(User).where(User.username == username))
        deleted = result.rowcount > 0
        if deleted:
            db_users_logger.info(f"✅ Deleted user: {username}")
        else:
            db_users_logger.warning(f"⚠️ User not found for deletion: {username}")
        return deleted
    
    @staticmethod
    async def bulk_sync(db: AsyncSession, users_data: List[dict]) -> int:
        """
        Bulk sync users from panel data.
        Creates new users and updates existing ones.
        Returns count of synced users.
        """
        db_users_logger.info(f"🔄 Starting bulk sync for {len(users_data)} users")
        count = 0
        for data in users_data:
            await UserCRUD.create_or_update(
                db,
                username=data.get("username"),
                status=data.get("status", "active"),
                owner_id=data.get("owner_id") or data.get("admin_id"),
                owner_username=data.get("owner_username") or data.get("admin_username"),
                group_ids=data.get("group_ids") or data.get("groups") or [],
                data_limit=data.get("data_limit"),
                used_traffic=data.get("used_traffic", 0),
                expire_at=data.get("expire_at"),
                note=data.get("note"),
            )
            count += 1
        
        await db.flush()
        db_users_logger.info(f"✅ Synced {count} users to database")
        return count

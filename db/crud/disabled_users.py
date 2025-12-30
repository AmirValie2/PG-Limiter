"""
Disabled User CRUD operations.
"""

import time
from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DisabledUser
from utils.logs import get_logger

db_disabled_logger = get_logger("db.disabled")


class DisabledUserCRUD:
    """CRUD operations for DisabledUser table."""
    
    @staticmethod
    async def add(
        db: AsyncSession,
        username: str,
        disabled_at: Optional[float] = None,
        enable_at: Optional[float] = None,
        original_groups: Optional[List[int]] = None,
        reason: Optional[str] = None,
        punishment_step: int = 0,
    ) -> DisabledUser:
        """Add user to disabled list."""
        db_disabled_logger.debug(f"📝 Adding to disabled list: {username}")
        if disabled_at is None:
            disabled_at = time.time()
        
        result = await db.execute(select(DisabledUser).where(DisabledUser.username == username))
        disabled = result.scalar_one_or_none()
        
        if disabled:
            db_disabled_logger.debug(f"✏️ Updating disabled record for: {username}")
            disabled.disabled_at = disabled_at
            disabled.enable_at = enable_at
            disabled.original_groups = original_groups or []
            disabled.reason = reason
            disabled.punishment_step = punishment_step
        else:
            db_disabled_logger.debug(f"➕ Creating new disabled record for: {username}")
            disabled = DisabledUser(
                username=username,
                disabled_at=disabled_at,
                enable_at=enable_at,
                original_groups=original_groups or [],
                reason=reason,
                punishment_step=punishment_step,
            )
            db.add(disabled)
        
        await db.flush()
        db_disabled_logger.info(f"🚫 User {username} added to disabled list (step={punishment_step})")
        return disabled
    
    @staticmethod
    async def remove(db: AsyncSession, username: str) -> bool:
        """Remove user from disabled list (when re-enabling)."""
        db_disabled_logger.debug(f"🗑️ Removing from disabled list: {username}")
        result = await db.execute(delete(DisabledUser).where(DisabledUser.username == username))
        removed = result.rowcount > 0
        if removed:
            db_disabled_logger.info(f"✅ User {username} removed from disabled list")
        else:
            db_disabled_logger.debug(f"ℹ️ User {username} was not in disabled list")
        return removed
    
    @staticmethod
    async def get(db: AsyncSession, username: str) -> Optional[DisabledUser]:
        """Get disabled user record."""
        db_disabled_logger.debug(f"🔍 Getting disabled record for: {username}")
        result = await db.execute(select(DisabledUser).where(DisabledUser.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def is_disabled(db: AsyncSession, username: str) -> bool:
        """Check if user is disabled."""
        db_disabled_logger.debug(f"🔍 Checking if disabled: {username}")
        result = await db.execute(select(DisabledUser).where(DisabledUser.username == username))
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[DisabledUser]:
        """Get all disabled users."""
        db_disabled_logger.debug("📋 Getting all disabled users")
        result = await db.execute(select(DisabledUser))
        disabled = result.scalars().all()
        db_disabled_logger.debug(f"✅ Found {len(disabled)} disabled users")
        return disabled
    
    @staticmethod
    async def get_all_dict(db: AsyncSession) -> dict[str, float]:
        """Get all disabled users as {username: disabled_timestamp} dict."""
        db_disabled_logger.debug("📋 Getting disabled users as dict")
        result = await db.execute(select(DisabledUser))
        disabled = result.scalars().all()
        return {d.username: d.disabled_at for d in disabled}
    
    @staticmethod
    async def get_users_to_enable(db: AsyncSession, time_to_active: int) -> List[str]:
        """
        Get users that should be re-enabled based on time_to_active.
        
        Args:
            time_to_active: Seconds after which to re-enable users
            
        Returns:
            List of usernames to re-enable
        """
        db_disabled_logger.debug(f"🔍 Getting users to re-enable (time_to_active={time_to_active}s)")
        current_time = time.time()
        cutoff = current_time - time_to_active
        
        result = await db.execute(select(DisabledUser))
        disabled = result.scalars().all()
        
        to_enable = []
        for d in disabled:
            if d.enable_at is not None:
                if current_time >= d.enable_at:
                    to_enable.append(d.username)
            elif d.disabled_at <= cutoff:
                to_enable.append(d.username)
        
        if to_enable:
            db_disabled_logger.info(f"✅ Found {len(to_enable)} users to re-enable")
        return to_enable
    
    @staticmethod
    async def clear_all(db: AsyncSession) -> int:
        """Clear all disabled users. Returns count of cleared."""
        db_disabled_logger.debug("🗑️ Clearing all disabled users")
        result = await db.execute(delete(DisabledUser))
        db_disabled_logger.info(f"✅ Cleared {result.rowcount} disabled users")
        return result.rowcount

"""
JSON to Database Migration Script
Migrates data from JSON files to SQLite database.

Run this script once after upgrading to the database version:
    python -m db.migrate_from_json
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db, get_db
from db.crud import (
    UserLimitCRUD,
    ExceptUserCRUD,
    DisabledUserCRUD,
    ViolationHistoryCRUD,
    ConfigCRUD,
)
from utils.logs import logger


async def migrate_config(config_file: str = "config.json"):
    """Migrate config.json to database Config table."""
    if not os.path.exists(config_file):
        logger.warning(f"Config file not found: {config_file}")
        return 0
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read config file: {e}")
        return 0
    
    count = 0
    async with get_db() as db:
        # Migrate panel settings
        if "panel" in config:
            await ConfigCRUD.set(db, "panel", config["panel"])
            count += 1
        
        # Migrate telegram settings
        if "telegram" in config:
            await ConfigCRUD.set(db, "telegram", config["telegram"])
            count += 1
        
        # Migrate limits
        if "limits" in config:
            limits = config["limits"]
            
            # General limit
            if "general" in limits:
                await ConfigCRUD.set(db, "general_limit", limits["general"])
                count += 1
            
            # Special limits
            special_limits = limits.get("special", {})
            for username, limit in special_limits.items():
                await UserLimitCRUD.set_limit(db, username, limit)
                count += 1
            
            # Except users
            except_users = limits.get("except_users", [])
            for username in except_users:
                await ExceptUserCRUD.add(db, username, reason="Migrated from config.json")
                count += 1
        
        # Also check for old-style except_users at root level
        if "except_users" in config and isinstance(config["except_users"], list):
            for username in config["except_users"]:
                await ExceptUserCRUD.add(db, username, reason="Migrated from config.json")
                count += 1
        
        # Migrate timing settings
        if "timing" in config:
            await ConfigCRUD.set(db, "timing", config["timing"])
            count += 1
        elif "check_interval" in config or "time_to_active_users" in config:
            timing = {
                "check_interval": config.get("check_interval", 60),
                "time_to_active_users": config.get("time_to_active_users", 900),
            }
            await ConfigCRUD.set(db, "timing", timing)
            count += 1
        
        # Migrate display settings
        if "display" in config:
            await ConfigCRUD.set(db, "display", config["display"])
            count += 1
        
        # Migrate API settings
        if "api" in config:
            await ConfigCRUD.set(db, "api", config["api"])
            count += 1
        
        # Migrate country_code
        if "country_code" in config:
            await ConfigCRUD.set(db, "country_code", config["country_code"])
            count += 1
        
        # Migrate disable_method
        if "disable_method" in config:
            await ConfigCRUD.set(db, "disable_method", config["disable_method"])
            count += 1
        
        if "disabled_group_id" in config:
            await ConfigCRUD.set(db, "disabled_group_id", config["disabled_group_id"])
            count += 1
        
        # Migrate group_filter
        if "group_filter" in config:
            await ConfigCRUD.set(db, "group_filter", config["group_filter"])
            count += 1
        
        # Migrate punishment settings
        if "punishment" in config:
            await ConfigCRUD.set(db, "punishment", config["punishment"])
            count += 1
    
    logger.info(f"Migrated {count} config items from {config_file}")
    return count


async def migrate_disabled_users(disabled_file: str = ".disable_users.json"):
    """Migrate disabled users from JSON to database."""
    if not os.path.exists(disabled_file):
        logger.warning(f"Disabled users file not found: {disabled_file}")
        return 0
    
    try:
        with open(disabled_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read disabled users file: {e}")
        return 0
    
    count = 0
    async with get_db() as db:
        # Handle different formats
        disabled_users = data.get("disabled_users", data.get("disable_user", {}))
        enable_at = data.get("enable_at", {})
        
        if isinstance(disabled_users, list):
            # Old format: list of usernames
            import time
            current_time = time.time()
            for username in disabled_users:
                await DisabledUserCRUD.add(
                    db,
                    username=username,
                    disabled_at=current_time,
                    reason="Migrated from JSON",
                )
                count += 1
        elif isinstance(disabled_users, dict):
            # New format: {username: timestamp}
            for username, disabled_at in disabled_users.items():
                user_enable_at = enable_at.get(username)
                await DisabledUserCRUD.add(
                    db,
                    username=username,
                    disabled_at=disabled_at,
                    enable_at=user_enable_at,
                    reason="Migrated from JSON",
                )
                count += 1
    
    logger.info(f"Migrated {count} disabled users from {disabled_file}")
    return count


async def migrate_user_groups(groups_file: str = ".user_groups_backup.json"):
    """Migrate user groups backup from JSON to database."""
    if not os.path.exists(groups_file):
        logger.warning(f"User groups file not found: {groups_file}")
        return 0
    
    try:
        with open(groups_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read user groups file: {e}")
        return 0
    
    count = 0
    async with get_db() as db:
        user_groups = data.get("user_groups", {})
        
        for username, info in user_groups.items():
            groups = info.get("groups", [])
            
            # Check if user is disabled and update their original_groups
            disabled = await DisabledUserCRUD.get(db, username)
            if disabled:
                disabled.original_groups = groups
                count += 1
    
    logger.info(f"Migrated {count} user group backups from {groups_file}")
    return count


async def migrate_violation_history(violations_file: str = ".violation_history.json"):
    """Migrate violation history from JSON to database."""
    if not os.path.exists(violations_file):
        logger.warning(f"Violation history file not found: {violations_file}")
        return 0
    
    try:
        with open(violations_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read violation history file: {e}")
        return 0
    
    count = 0
    async with get_db() as db:
        violations = data.get("violations", {})
        
        for username, records in violations.items():
            for record in records:
                await ViolationHistoryCRUD.add(
                    db,
                    username=username,
                    step_applied=record.get("step_applied", 0),
                    disable_duration=record.get("disable_duration", 0),
                )
                count += 1
    
    logger.info(f"Migrated {count} violation records from {violations_file}")
    return count


async def backup_json_files():
    """Backup JSON files before migration."""
    backup_dir = "backup_json"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "config.json",
        ".disable_users.json",
        ".user_groups_backup.json",
        ".violation_history.json",
    ]
    
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for filename in files_to_backup:
        if os.path.exists(filename):
            backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
            shutil.copy2(filename, backup_path)
            logger.info(f"Backed up {filename} to {backup_path}")


async def main():
    """Run the full migration."""
    print("=" * 60)
    print("PG-Limiter: JSON to Database Migration")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    await init_db()
    print("   ✓ Database initialized")
    
    # Backup JSON files
    print("\n2. Backing up JSON files...")
    await backup_json_files()
    print("   ✓ JSON files backed up to backup_json/")
    
    # Migrate data
    print("\n3. Migrating data...")
    
    config_count = await migrate_config()
    print(f"   ✓ Migrated {config_count} config items")
    
    disabled_count = await migrate_disabled_users()
    print(f"   ✓ Migrated {disabled_count} disabled users")
    
    groups_count = await migrate_user_groups()
    print(f"   ✓ Migrated {groups_count} user group backups")
    
    violations_count = await migrate_violation_history()
    print(f"   ✓ Migrated {violations_count} violation records")
    
    total = config_count + disabled_count + groups_count + violations_count
    
    print("\n" + "=" * 60)
    print(f"Migration complete! Total items migrated: {total}")
    print("=" * 60)
    print("\nYour JSON files have been backed up to backup_json/")
    print("You can safely delete them after verifying the migration.")
    print("\nNote: Panel credentials and bot token are now in .env file.")
    print("Dynamic settings are stored in the database.")


if __name__ == "__main__":
    asyncio.run(main())

"""
Backup and restore handlers for the Telegram bot.
Includes functions for creating and restoring backups.
"""

import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from telegram_bot.constants import RESTORE_CONFIG
from telegram_bot.handlers.admin import check_admin_privilege


async def send_backup(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Send a comprehensive backup zip file to the user."""
    check = await check_admin_privilege(update)
    if check is not None:
        return check
    
    try:
        await update.message.reply_text("📦 Creating backup... Please wait.")
        
        # Create temp directory for backup
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"pg-limiter-backup-{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Check standard Docker paths first
            docker_config_dir = "/etc/opt/pg-limiter"
            if os.path.exists(docker_config_dir):
                for filename in os.listdir(docker_config_dir):
                    filepath = os.path.join(docker_config_dir, filename)
                    if os.path.isfile(filepath):
                        zipf.write(filepath, f"config/{filename}")
            
            # Also check local .env
            if os.path.exists(".env"):
                zipf.write(".env", "config/.env")
            
            # Add data files from /var/lib/pg-limiter/ (or local data/)
            data_dirs = [
                "/var/lib/pg-limiter/data",
                "data",
            ]
            for data_dir in data_dirs:
                if os.path.exists(data_dir) and os.path.isdir(data_dir):
                    for root, dirs, files in os.walk(data_dir):
                        for file in files:
                            filepath = os.path.join(root, file)
                            arcname = os.path.join("data", os.path.relpath(filepath, data_dir))
                            zipf.write(filepath, arcname)
                    break
            
            # Add legacy JSON files if they exist
            legacy_files = [
                ".disable_users.json",
                ".violation_history.json",
                ".user_groups_backup.json",
            ]
            for legacy_file in legacy_files:
                if os.path.exists(legacy_file):
                    zipf.write(legacy_file, f"legacy/{legacy_file}")
            
            # Add backup info
            hostname = "unknown"
            try:
                hostname = os.uname().nodename
            except AttributeError:
                pass
            
            backup_info = f"""PG-Limiter Backup
Created: {datetime.now().isoformat()}
Hostname: {hostname}

Contents:
- config/: Configuration files (.env)
- data/: Database and persistent data
- legacy/: Legacy JSON files (if any)

To restore:
1. Send this zip file to the bot with /restore command
2. Or use: pg-limiter restore <this-file.zip>
"""
            zipf.writestr("backup_info.txt", backup_info)
        
        # Send the zip file
        with open(zip_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=zip_name,
                caption=(
                    "✅ <b>Backup created successfully!</b>\n\n"
                    "📁 This backup includes:\n"
                    "• Configuration files\n"
                    "• Database (SQLite)\n"
                    "• Legacy JSON files (if any)\n\n"
                    "💡 To restore, use /restore command and send this file."
                ),
                parse_mode="HTML",
            )
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        await update.message.reply_html(
            f"❌ <b>Error creating backup:</b>\n<code>{str(e)}</code>"
        )


async def restore_config(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Start the restore process by asking for the backup file."""
    check = await check_admin_privilege(update)
    if check is not None:
        return check
    
    await update.message.reply_html(
        "📥 <b>Restore from Backup</b>\n\n"
        "Please send your backup file (zip or json format).\n\n"
        "<b>⚠️ Warning:</b> This will replace your current data!"
    )
    return RESTORE_CONFIG


async def restore_config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the uploaded backup file and restore it."""
    try:
        # Check if a document was sent
        if not update.message.document:
            await update.message.reply_html(
                "❌ Please send a valid backup file (zip or json).\n"
                "Use /restore to try again."
            )
            return ConversationHandler.END
        
        file_name = update.message.document.file_name
        
        # Download the file
        file = await update.message.document.get_file()
        file_content = await file.download_as_bytearray()
        
        if file_name.endswith('.zip'):
            # Handle zip backup (new format)
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "backup.zip")
            
            with open(zip_path, 'wb') as f:
                f.write(file_content)
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restore .env file if present
            env_restored = False
            for env_name in ["config/.env", ".env"]:
                src_path = os.path.join(temp_dir, env_name)
                if os.path.exists(src_path):
                    env_dst = "/etc/opt/pg-limiter/.env" if os.path.exists("/etc/opt/pg-limiter") else ".env"
                    shutil.copy(src_path, env_dst)
                    env_restored = True
                    break
            
            # Restore data files
            data_src = os.path.join(temp_dir, "data")
            if os.path.exists(data_src):
                data_dst = "/var/lib/pg-limiter/data" if os.path.exists("/var/lib/pg-limiter") else "data"
                
                # Copy database files
                for item in os.listdir(data_src):
                    src = os.path.join(data_src, item)
                    dst = os.path.join(data_dst, item)
                    if os.path.isfile(src):
                        os.makedirs(data_dst, exist_ok=True)
                        shutil.copy2(src, dst)
            
            # Restore legacy files (for migration)
            legacy_src = os.path.join(temp_dir, "legacy")
            if os.path.exists(legacy_src):
                for item in os.listdir(legacy_src):
                    src = os.path.join(legacy_src, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, item)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            await update.message.reply_html(
                "✅ <b>Backup restored successfully!</b>\n\n"
                f"• Environment file: {'✓' if env_restored else '✗'}\n"
                "• Database: ✓\n\n"
                "⚠️ Please restart the service for changes to take effect."
            )
            
        elif file_name.endswith('.json'):
            # Handle legacy JSON config - migrate to database
            try:
                config_data = json.loads(file_content.decode('utf-8'))
                
                from db import get_db, ConfigCRUD, UserLimitCRUD, ExceptUserCRUD
                
                async with get_db() as db:
                    # Import settings to database
                    if "disable_method" in config_data:
                        await ConfigCRUD.set(db, "disable_method", str(config_data["disable_method"]))
                    if config_data.get("disabled_group_id"):
                        await ConfigCRUD.set(db, "disabled_group_id", str(config_data["disabled_group_id"]))
                    if config_data.get("enhanced_details") is not None:
                        await ConfigCRUD.set(db, "enhanced_details", str(config_data["enhanced_details"]).lower())
                    
                    # Import special limits
                    special_limits = config_data.get("limits", {}).get("special", {})
                    for username, limit in special_limits.items():
                        await UserLimitCRUD.set(db, username, limit)
                    
                    # Import except users
                    except_users = config_data.get("except_users", [])
                    for username in except_users:
                        await ExceptUserCRUD.add(db, username, "Restored from backup")
                
                await update.message.reply_html(
                    "✅ <b>Legacy config imported to database!</b>\n\n"
                    "📝 Panel credentials should be set in .env file.\n"
                    "⚠️ Restart the service for changes to take effect."
                )
                
            except json.JSONDecodeError as e:
                await update.message.reply_html(
                    f"❌ Invalid JSON format: {str(e)}\nUse /restore to try again."
                )
                return ConversationHandler.END
        else:
            await update.message.reply_html(
                "❌ Unsupported file format. Please send a .zip or .json file.\n"
                "Use /restore to try again."
            )
            return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_html(
            f"❌ <b>Error during restore:</b>\n<code>{str(e)}</code>\n\nUse /restore to try again."
        )
    
    context.user_data["waiting_for"] = None
    return ConversationHandler.END

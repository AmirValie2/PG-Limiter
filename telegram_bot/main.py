"""
This module contains the main functionality of a Telegram bot.
It includes functions for adding admins,
listing admins, setting special limits, and creating a config and more...
"""

import asyncio
import os
import sys
import json
import shutil
import tempfile
import zipfile
from datetime import datetime

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        ConversationHandler,
        MessageHandler,
        CallbackQueryHandler,
        filters,
    )
except ImportError:
    print(
        "Module 'python-telegram-bot' is not installed use:"
        + " 'pip install python-telegram-bot' to install it"
    )
    sys.exit()

from telegram_bot.utils import (
    add_admin_to_config,
    add_base_information,
    add_except_user,
    check_admin,
    get_special_limit_list,
    handel_special_limit,
    read_json_file,
    remove_admin_from_config,
    remove_except_user_from_config,
    save_check_interval,
    save_general_limit,
    save_time_to_active_users,
    show_except_users_handler,
    write_country_code_json,
    write_json_file,
)
from utils.read_config import read_config, get_config_value
from utils.connection_analyzer import (
    generate_connection_report,
    generate_node_usage_report,
    get_multi_device_users,
    get_users_by_node,
    get_users_by_inbound_protocol
)

(
    GET_DOMAIN,
    GET_PORT,
    GET_USERNAME,
    GET_PASSWORD,
    GET_CONFIRMATION,
    GET_CHAT_ID,
    GET_SPECIAL_LIMIT,
    GET_LIMIT_NUMBER,
    GET_CHAT_ID_TO_REMOVE,
    SET_COUNTRY_CODE,
    SET_EXCEPT_USERS,
    REMOVE_EXCEPT_USER,
    GET_GENERAL_LIMIT_NUMBER,
    GET_CHECK_INTERVAL,
    GET_TIME_TO_ACTIVE_USERS,
    SET_IPINFO_TOKEN,
    SET_ENHANCED_DETAILS,
    RESTORE_CONFIG,
    WAITING_USERNAME_FOR_LIMIT,
) = range(19)


# Callback data constants for inline keyboards
class CallbackData:
    # Main menu
    MAIN_MENU = "main_menu"
    
    # Settings menu
    SETTINGS_MENU = "settings_menu"
    LIMITS_MENU = "limits_menu"
    USERS_MENU = "users_menu"
    MONITORING_MENU = "monitoring_menu"
    REPORTS_MENU = "reports_menu"
    ADMIN_MENU = "admin_menu"
    
    # Special limit options
    SPECIAL_LIMIT_1 = "special_limit_1"
    SPECIAL_LIMIT_2 = "special_limit_2"
    SPECIAL_LIMIT_CUSTOM = "special_limit_custom"
    
    # General limit options
    GENERAL_LIMIT_2 = "general_limit_2"
    GENERAL_LIMIT_3 = "general_limit_3"
    GENERAL_LIMIT_4 = "general_limit_4"
    GENERAL_LIMIT_CUSTOM = "general_limit_custom"
    
    # Country code options
    COUNTRY_IR = "country_ir"
    COUNTRY_RU = "country_ru"
    COUNTRY_CN = "country_cn"
    COUNTRY_NONE = "country_none"
    
    # Check interval options
    INTERVAL_120 = "interval_120"
    INTERVAL_180 = "interval_180"
    INTERVAL_240 = "interval_240"
    INTERVAL_CUSTOM = "interval_custom"
    
    # Time to active options
    TIME_300 = "time_300"
    TIME_600 = "time_600"
    TIME_900 = "time_900"
    TIME_CUSTOM = "time_custom"
    
    # Enhanced details toggle
    ENHANCED_ON = "enhanced_on"
    ENHANCED_OFF = "enhanced_off"
    
    # Single IP users toggle
    SINGLE_IP_ON = "single_ip_on"
    SINGLE_IP_OFF = "single_ip_off"
    
    # Monitoring actions
    MONITORING_STATUS = "monitoring_status"
    MONITORING_DETAILS = "monitoring_details"
    MONITORING_CLEAR = "monitoring_clear"
    
    # Reports
    REPORT_CONNECTION = "report_connection"
    REPORT_NODE_USAGE = "report_node_usage"
    REPORT_MULTI_DEVICE = "report_multi_device"
    REPORT_IP_12H = "report_ip_12h"
    REPORT_IP_48H = "report_ip_48h"
    
    # User management
    SHOW_EXCEPT_USERS = "show_except_users"
    SET_EXCEPT_USER = "set_except_user"
    REMOVE_EXCEPT_USER = "remove_except_user"
    SHOW_SPECIAL_LIMIT = "show_special_limit"
    SET_SPECIAL_LIMIT = "set_special_limit"
    SHOW_DISABLED_USERS = "show_disabled_users"
    ENABLE_ALL_DISABLED = "enable_all_disabled"
    
    # Admin management
    ADD_ADMIN = "add_admin"
    LIST_ADMINS = "list_admins"
    REMOVE_ADMIN = "remove_admin"
    
    # Backup/Restore
    BACKUP = "backup"
    RESTORE = "restore"
    
    # Config
    CREATE_CONFIG = "create_config"
    SET_IPINFO = "set_ipinfo"
    
    # Disable method settings
    DISABLE_METHOD_MENU = "disable_method_menu"
    DISABLE_BY_STATUS = "disable_by_status"
    DISABLE_BY_GROUP = "disable_by_group"
    SELECT_DISABLED_GROUP = "select_disabled_group"
    
    # Punishment system
    PUNISHMENT_MENU = "punishment_menu"
    PUNISHMENT_TOGGLE = "punishment_toggle"
    PUNISHMENT_WINDOW_24 = "punishment_window_24"
    PUNISHMENT_WINDOW_48 = "punishment_window_48"
    PUNISHMENT_WINDOW_72 = "punishment_window_72"
    PUNISHMENT_WINDOW_CUSTOM = "punishment_window_custom"
    
    # Group filter
    GROUP_FILTER_MENU = "group_filter_menu"
    GROUP_FILTER_TOGGLE = "group_filter_toggle"
    GROUP_FILTER_MODE_INCLUDE = "group_filter_mode_include"
    GROUP_FILTER_MODE_EXCLUDE = "group_filter_mode_exclude"
    
    # Admin filter
    ADMIN_FILTER_MENU = "admin_filter_menu"
    ADMIN_FILTER_TOGGLE = "admin_filter_toggle"
    ADMIN_FILTER_MODE_INCLUDE = "admin_filter_mode_include"
    ADMIN_FILTER_MODE_EXCLUDE = "admin_filter_mode_exclude"
    
    # Cleanup
    CLEANUP_DELETED_USERS = "cleanup_deleted_users"
    
    # Back buttons
    BACK_MAIN = "back_main"
    BACK_SETTINGS = "back_settings"
    BACK_LIMITS = "back_limits"

# Try to load bot token at module level but don't fail if not available
# This will be set properly when run_telegram_bot is called
bot_token = None
try:
    # First try environment variable (preferred)
    bot_token = os.environ.get("BOT_TOKEN", "")
    if bot_token:
        print("✓ Bot token loaded from environment")
except Exception as e:
    print(f"⚠ Error loading config at module import: {e}")
    import traceback
    traceback.print_exc()

# Create placeholder application - will be replaced in run_telegram_bot
if bot_token:
    application = ApplicationBuilder().token(bot_token).build()
else:
    # Use a dummy token for module loading - will be replaced at runtime
    application = ApplicationBuilder().token("0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX").build()


def create_main_menu_keyboard():
    """Create the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Settings", callback_data=CallbackData.SETTINGS_MENU),
            InlineKeyboardButton("📊 Reports", callback_data=CallbackData.REPORTS_MENU),
        ],
        [
            InlineKeyboardButton("🎯 Limits", callback_data=CallbackData.LIMITS_MENU),
            InlineKeyboardButton("👥 Users", callback_data=CallbackData.USERS_MENU),
        ],
        [
            InlineKeyboardButton("📡 Monitoring", callback_data=CallbackData.MONITORING_MENU),
            InlineKeyboardButton("👑 Admins", callback_data=CallbackData.ADMIN_MENU),
        ],
        [
            InlineKeyboardButton("💾 Backup", callback_data=CallbackData.BACKUP),
            InlineKeyboardButton("📥 Restore", callback_data=CallbackData.RESTORE),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_settings_menu_keyboard():
    """Create the settings menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔑 IPInfo Token", callback_data=CallbackData.SET_IPINFO),
            InlineKeyboardButton("🚫 Disable Method", callback_data=CallbackData.DISABLE_METHOD_MENU),
        ],
        [
            InlineKeyboardButton("📋 Enhanced Details", callback_data="enhanced_menu"),
            InlineKeyboardButton("1️⃣ Single IP Users", callback_data="single_ip_menu"),
        ],
        [
            InlineKeyboardButton("⚖️ Punishment", callback_data=CallbackData.PUNISHMENT_MENU),
            InlineKeyboardButton("🔍 Group Filter", callback_data=CallbackData.GROUP_FILTER_MENU),
        ],
        [
            InlineKeyboardButton("👤 Admin Filter", callback_data=CallbackData.ADMIN_FILTER_MENU),
        ],
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_limits_menu_keyboard():
    """Create the limits menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("🎯 Set Special Limit", callback_data=CallbackData.SET_SPECIAL_LIMIT)],
        [InlineKeyboardButton("📋 Show Special Limits", callback_data=CallbackData.SHOW_SPECIAL_LIMIT)],
        [InlineKeyboardButton("🔢 Set General Limit", callback_data="general_limit_menu")],
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_special_limit_options_keyboard():
    """Create special limit options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("1️⃣ 1 Device", callback_data=CallbackData.SPECIAL_LIMIT_1),
            InlineKeyboardButton("2️⃣ 2 Devices", callback_data=CallbackData.SPECIAL_LIMIT_2),
        ],
        [InlineKeyboardButton("✏️ Custom", callback_data=CallbackData.SPECIAL_LIMIT_CUSTOM)],
        [InlineKeyboardButton("« Back to Limits", callback_data=CallbackData.LIMITS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_general_limit_keyboard():
    """Create general limit options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("2️⃣", callback_data=CallbackData.GENERAL_LIMIT_2),
            InlineKeyboardButton("3️⃣", callback_data=CallbackData.GENERAL_LIMIT_3),
            InlineKeyboardButton("4️⃣", callback_data=CallbackData.GENERAL_LIMIT_4),
        ],
        [InlineKeyboardButton("✏️ Custom", callback_data=CallbackData.GENERAL_LIMIT_CUSTOM)],
        [InlineKeyboardButton("« Back to Limits", callback_data=CallbackData.LIMITS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_country_keyboard():
    """Create country code options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 Iran", callback_data=CallbackData.COUNTRY_IR),
            InlineKeyboardButton("🇷🇺 Russia", callback_data=CallbackData.COUNTRY_RU),
        ],
        [
            InlineKeyboardButton("🇨🇳 China", callback_data=CallbackData.COUNTRY_CN),
            InlineKeyboardButton("🌐 None", callback_data=CallbackData.COUNTRY_NONE),
        ],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_interval_keyboard():
    """Create check interval options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("2 min", callback_data=CallbackData.INTERVAL_120),
            InlineKeyboardButton("3 min", callback_data=CallbackData.INTERVAL_180),
            InlineKeyboardButton("4 min", callback_data=CallbackData.INTERVAL_240),
        ],
        [InlineKeyboardButton("✏️ Custom", callback_data=CallbackData.INTERVAL_CUSTOM)],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_time_to_active_keyboard():
    """Create time to active options keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("5 min", callback_data=CallbackData.TIME_300),
            InlineKeyboardButton("10 min", callback_data=CallbackData.TIME_600),
            InlineKeyboardButton("15 min", callback_data=CallbackData.TIME_900),
        ],
        [InlineKeyboardButton("✏️ Custom", callback_data=CallbackData.TIME_CUSTOM)],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_enhanced_details_keyboard():
    """Create enhanced details toggle keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ ON", callback_data=CallbackData.ENHANCED_ON),
            InlineKeyboardButton("❌ OFF", callback_data=CallbackData.ENHANCED_OFF),
        ],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_single_ip_keyboard():
    """Create single IP users toggle keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ ON", callback_data=CallbackData.SINGLE_IP_ON),
            InlineKeyboardButton("❌ OFF", callback_data=CallbackData.SINGLE_IP_OFF),
        ],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_punishment_menu_keyboard(enabled: bool = True, window_hours: int = 72):
    """Create punishment system menu keyboard."""
    toggle_text = "❌ Disable" if enabled else "✅ Enable"
    status_emoji = "🟢" if enabled else "🔴"
    
    keyboard = [
        [InlineKeyboardButton(f"{status_emoji} Status: {'Enabled' if enabled else 'Disabled'}", callback_data="punishment_info")],
        [InlineKeyboardButton(toggle_text, callback_data=CallbackData.PUNISHMENT_TOGGLE)],
        [
            InlineKeyboardButton("⏱️ Time Window", callback_data="punishment_window_menu"),
        ],
        [
            InlineKeyboardButton("24h", callback_data=CallbackData.PUNISHMENT_WINDOW_24),
            InlineKeyboardButton("48h", callback_data=CallbackData.PUNISHMENT_WINDOW_48),
            InlineKeyboardButton("72h", callback_data=CallbackData.PUNISHMENT_WINDOW_72),
        ],
        [InlineKeyboardButton("📋 View Punishment Steps", callback_data="punishment_view_steps")],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_group_filter_menu_keyboard(enabled: bool = False, mode: str = "include", group_ids: list = None):
    """Create group filter menu keyboard."""
    if group_ids is None:
        group_ids = []
    
    toggle_text = "❌ Disable" if enabled else "✅ Enable"
    status_emoji = "🟢" if enabled else "🔴"
    mode_emoji = "📥" if mode == "include" else "📤"
    
    keyboard = [
        [InlineKeyboardButton(f"{status_emoji} Status: {'Enabled' if enabled else 'Disabled'}", callback_data="group_filter_info")],
        [InlineKeyboardButton(toggle_text, callback_data=CallbackData.GROUP_FILTER_TOGGLE)],
        [
            InlineKeyboardButton(f"{mode_emoji} Mode: {mode.title()}", callback_data="group_filter_mode_menu"),
        ],
        [
            InlineKeyboardButton("📥 Include", callback_data=CallbackData.GROUP_FILTER_MODE_INCLUDE),
            InlineKeyboardButton("📤 Exclude", callback_data=CallbackData.GROUP_FILTER_MODE_EXCLUDE),
        ],
        [InlineKeyboardButton(f"📋 Groups: {len(group_ids)} configured", callback_data="group_filter_view_groups")],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_admin_filter_menu_keyboard(enabled: bool = False, mode: str = "include", admin_usernames: list = None):
    """Create admin filter menu keyboard."""
    if admin_usernames is None:
        admin_usernames = []
    
    toggle_text = "❌ Disable" if enabled else "✅ Enable"
    status_emoji = "🟢" if enabled else "🔴"
    mode_emoji = "📥" if mode == "include" else "📤"
    
    keyboard = [
        [InlineKeyboardButton(f"{status_emoji} Status: {'Enabled' if enabled else 'Disabled'}", callback_data="admin_filter_info")],
        [InlineKeyboardButton(toggle_text, callback_data=CallbackData.ADMIN_FILTER_TOGGLE)],
        [
            InlineKeyboardButton(f"{mode_emoji} Mode: {mode.title()}", callback_data="admin_filter_mode_menu"),
        ],
        [
            InlineKeyboardButton("📥 Include", callback_data=CallbackData.ADMIN_FILTER_MODE_INCLUDE),
            InlineKeyboardButton("📤 Exclude", callback_data=CallbackData.ADMIN_FILTER_MODE_EXCLUDE),
        ],
        [InlineKeyboardButton(f"👤 Admins: {len(admin_usernames)} configured", callback_data="admin_filter_view_admins")],
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_users_menu_keyboard():
    """Create users menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("🚫 Disabled Users", callback_data=CallbackData.SHOW_DISABLED_USERS)],
        [InlineKeyboardButton("📋 Show Except Users", callback_data=CallbackData.SHOW_EXCEPT_USERS)],
        [InlineKeyboardButton("➕ Add Except User", callback_data=CallbackData.SET_EXCEPT_USER)],
        [InlineKeyboardButton("➖ Remove Except User", callback_data=CallbackData.REMOVE_EXCEPT_USER)],
        [InlineKeyboardButton("🧹 Cleanup Deleted Users", callback_data=CallbackData.CLEANUP_DELETED_USERS)],
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_monitoring_menu_keyboard():
    """Create monitoring menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data=CallbackData.MONITORING_STATUS)],
        [InlineKeyboardButton("📈 Details", callback_data=CallbackData.MONITORING_DETAILS)],
        [InlineKeyboardButton("🗑️ Clear All", callback_data=CallbackData.MONITORING_CLEAR)],
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_reports_menu_keyboard():
    """Create reports menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("📊 Connection Report", callback_data=CallbackData.REPORT_CONNECTION)],
        [InlineKeyboardButton("🖥️ Node Usage", callback_data=CallbackData.REPORT_NODE_USAGE)],
        [InlineKeyboardButton("📱 Multi-Device Users", callback_data=CallbackData.REPORT_MULTI_DEVICE)],
        [
            InlineKeyboardButton("📈 IP History 12h", callback_data=CallbackData.REPORT_IP_12H),
            InlineKeyboardButton("📈 IP History 48h", callback_data=CallbackData.REPORT_IP_48H),
        ],
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_admin_menu_keyboard():
    """Create admin menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("📋 List Admins", callback_data=CallbackData.LIST_ADMINS)],
        [InlineKeyboardButton("➕ Add Admin", callback_data=CallbackData.ADD_ADMIN)],
        [InlineKeyboardButton("➖ Remove Admin", callback_data=CallbackData.REMOVE_ADMIN)],
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_back_to_main_keyboard():
    """Create a simple back to main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_back_to_users_keyboard():
    """Create a simple back to users menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("« Back to Users", callback_data=CallbackData.USERS_MENU)],
        [InlineKeyboardButton("« Back to Main Menu", callback_data=CallbackData.BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_disabled_users_keyboard(disabled_users: dict, page: int = 0, per_page: int = 5):
    """
    Create a keyboard with disabled users as glass-style buttons.
    Each user gets an enable button.
    
    Args:
        disabled_users: Dict of username -> disabled_timestamp
        page: Current page number (0-indexed)
        per_page: Number of users per page
    """
    import time
    
    keyboard = []
    users_list = list(disabled_users.items())
    total_users = len(users_list)
    total_pages = max(1, (total_users + per_page - 1) // per_page)
    
    # Get current page users
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_users)
    page_users = users_list[start_idx:end_idx]
    
    current_time = time.time()
    
    # Add user buttons with glass-style appearance
    for username, disabled_time in page_users:
        elapsed = int(current_time - disabled_time)
        minutes = elapsed // 60
        if minutes >= 60:
            hours = minutes // 60
            time_str = f"{hours}h ago"
        else:
            time_str = f"{minutes}m ago"
        
        # Glass-style button with user info and enable action
        keyboard.append([
            InlineKeyboardButton(
                f"🔴 {username} ({time_str})",
                callback_data=f"user_info:{username}"
            ),
            InlineKeyboardButton(
                "✅ Enable",
                callback_data=f"enable_user:{username}"
            )
        ])
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"disabled_page:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"disabled_page:{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Enable all button (only show if there are disabled users)
    if total_users > 0:
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Enable All ({total_users} users)",
                callback_data=CallbackData.ENABLE_ALL_DISABLED
            )
        ])
    
    # Refresh and back buttons
    keyboard.append([
        InlineKeyboardButton("🔄 Refresh", callback_data=CallbackData.SHOW_DISABLED_USERS),
    ])
    keyboard.append([
        InlineKeyboardButton("« Back to Users", callback_data=CallbackData.USERS_MENU),
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def show_disabled_users_menu(query, page: int = 0):
    """Display the disabled users menu with enable buttons."""
    from utils.handel_dis_users import DisabledUsers
    from utils.read_config import read_config
    
    try:
        # Load disabled users
        dis_users = DisabledUsers()
        disabled_dict = dis_users.disabled_users
        
        if not disabled_dict:
            text = (
                "🚫 <b>Disabled Users</b>\n\n"
                "✅ No users are currently disabled by the limiter.\n\n"
                "Users get disabled when they exceed their IP limit."
            )
            keyboard = create_back_to_users_keyboard()
        else:
            # Get time to active for info
            try:
                config = await read_config()
                time_to_active = config.get("timing", {}).get("time_to_active_users", 300)
            except:
                time_to_active = 300
            
            total_users = len(disabled_dict)
            text = (
                f"🚫 <b>Disabled Users</b>\n\n"
                f"📊 Total: <b>{total_users}</b> users disabled by limiter\n"
                f"⏱️ Auto-enable after: <b>{time_to_active // 60}</b> minutes\n\n"
                f"<i>Click the ✅ button to manually enable a user:</i>"
            )
            keyboard = create_disabled_users_keyboard(disabled_dict, page=page)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        await query.edit_message_text(
            text=f"❌ Error loading disabled users: {e}",
            reply_markup=create_back_to_users_keyboard(),
            parse_mode="HTML"
        )


async def enable_single_user(query, username: str):
    """Enable a single disabled user."""
    from utils.handel_dis_users import DisabledUsers
    from utils.panel_api import enable_selected_users
    from utils.read_config import read_config
    from utils.types import PanelType
    
    try:
        # Load config for panel data
        config = await read_config()
        panel_config = config.get("panel", {})
        panel_data = PanelType(
            panel_username=panel_config.get("username", ""),
            panel_password=panel_config.get("password", ""),
            panel_domain=panel_config.get("domain", "")
        )
        
        # Enable user on panel
        await enable_selected_users(panel_data, {username})
        
        # Remove from disabled users list
        dis_users = DisabledUsers()
        await dis_users.remove_user(username)
        
        # Show updated list
        await query.answer(f"✅ User {username} enabled!")
        await show_disabled_users_menu(query)
        
    except Exception as e:
        await query.edit_message_text(
            text=f"❌ Error enabling user {username}: {e}",
            reply_markup=create_back_to_users_keyboard(),
            parse_mode="HTML"
        )


async def enable_all_disabled_users(query):
    """Enable all disabled users."""
    from utils.handel_dis_users import DisabledUsers
    from utils.panel_api import enable_selected_users
    from utils.read_config import read_config
    from utils.types import PanelType
    
    try:
        # Load disabled users
        dis_users = DisabledUsers()
        disabled_dict = dis_users.disabled_users.copy()
        
        if not disabled_dict:
            await query.answer("No disabled users to enable!")
            return
        
        usernames = set(disabled_dict.keys())
        count = len(usernames)
        
        await query.edit_message_text(
            text=f"⏳ Enabling {count} users...",
            parse_mode="HTML"
        )
        
        # Load config for panel data
        config = await read_config()
        panel_config = config.get("panel", {})
        panel_data = PanelType(
            panel_username=panel_config.get("username", ""),
            panel_password=panel_config.get("password", ""),
            panel_domain=panel_config.get("domain", "")
        )
        
        # Enable all users on panel
        await enable_selected_users(panel_data, usernames)
        
        # Clear disabled users list
        await dis_users.read_and_clear_users()
        
        await query.edit_message_text(
            text=f"✅ <b>Successfully enabled {count} users!</b>\n\n"
                 f"All disabled users have been re-enabled on the panel.",
            reply_markup=create_back_to_users_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await query.edit_message_text(
            text=f"❌ Error enabling users: {e}",
            reply_markup=create_back_to_users_keyboard(),
            parse_mode="HTML"
        )


async def cleanup_deleted_users_handler(query):
    """Clean up users from limiter config that no longer exist in the panel."""
    from utils.panel_api import cleanup_deleted_users
    from utils.read_config import read_config
    from utils.types import PanelType
    
    try:
        await query.edit_message_text(
            text="⏳ <b>Cleaning up deleted users...</b>\n\n"
                 "Fetching all users from panel and checking limiter config...",
            parse_mode="HTML"
        )
        
        # Load config for panel data
        config = await read_config()
        panel_config = config.get("panel", {})
        panel_data = PanelType(
            panel_username=panel_config.get("username", ""),
            panel_password=panel_config.get("password", ""),
            panel_domain=panel_config.get("domain", "")
        )
        
        # Perform cleanup
        result = await cleanup_deleted_users(panel_data)
        
        # Build result message
        total_removed = (
            len(result["special_limits_removed"]) +
            len(result["except_users_removed"]) +
            len(result["disabled_users_removed"]) +
            len(result["user_groups_backup_removed"])
        )
        
        if total_removed == 0:
            await query.edit_message_text(
                text="✅ <b>Cleanup Complete!</b>\n\n"
                     "No deleted users found in limiter config.\n"
                     "Everything is clean! 🎉",
                reply_markup=create_back_to_users_keyboard(),
                parse_mode="HTML"
            )
        else:
            message_parts = ["🧹 <b>Cleanup Complete!</b>\n"]
            
            if result["special_limits_removed"]:
                message_parts.append(
                    f"\n📊 <b>Special Limits:</b> Removed {len(result['special_limits_removed'])} users\n"
                    f"<code>{', '.join(result['special_limits_removed'][:10])}</code>"
                )
                if len(result["special_limits_removed"]) > 10:
                    message_parts.append(f" and {len(result['special_limits_removed']) - 10} more...")
            
            if result["except_users_removed"]:
                message_parts.append(
                    f"\n📋 <b>Except Users:</b> Removed {len(result['except_users_removed'])} users\n"
                    f"<code>{', '.join(result['except_users_removed'][:10])}</code>"
                )
                if len(result["except_users_removed"]) > 10:
                    message_parts.append(f" and {len(result['except_users_removed']) - 10} more...")
            
            if result["disabled_users_removed"]:
                message_parts.append(
                    f"\n🚫 <b>Disabled Users:</b> Removed {len(result['disabled_users_removed'])} users\n"
                    f"<code>{', '.join(result['disabled_users_removed'][:10])}</code>"
                )
                if len(result["disabled_users_removed"]) > 10:
                    message_parts.append(f" and {len(result['disabled_users_removed']) - 10} more...")
            
            if result["user_groups_backup_removed"]:
                message_parts.append(
                    f"\n📁 <b>Groups Backup:</b> Removed {len(result['user_groups_backup_removed'])} users\n"
                    f"<code>{', '.join(result['user_groups_backup_removed'][:10])}</code>"
                )
                if len(result["user_groups_backup_removed"]) > 10:
                    message_parts.append(f" and {len(result['user_groups_backup_removed']) - 10} more...")
            
            message_parts.append(f"\n\n<b>Total removed:</b> {total_removed} user entries")
            
            await query.edit_message_text(
                text="".join(message_parts),
                reply_markup=create_back_to_users_keyboard(),
                parse_mode="HTML"
            )
        
    except Exception as e:
        await query.edit_message_text(
            text=f"❌ <b>Error during cleanup:</b>\n\n{e}",
            reply_markup=create_back_to_users_keyboard(),
            parse_mode="HTML"
        )


def create_back_to_settings_keyboard():
    """Create a keyboard with only a back to settings button."""
    keyboard = [
        [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_disable_method_menu(query):
    """Display the disable method selection menu."""
    try:
        from utils.read_config import read_config
        config = await read_config()
        
        current_method = config.get("disable_method", "status")
        disabled_group_id = config.get("disabled_group_id", None)
        
        if current_method == "group" and disabled_group_id:
            status = f"Group-based (Group ID: {disabled_group_id})"
        else:
            status = "Status-based (default)"
        
        if current_method == "group" and disabled_group_id:
            status = f"Group-based (Group ID: {disabled_group_id})"
        else:
            status = "Status-based (default)"
        
        text = (
            "🚫 <b>Disable Method</b>\n\n"
            f"📌 <b>Current:</b> {status}\n\n"
            "<b>Options:</b>\n"
            "• <b>Status</b>: Change user status to 'disabled'\n"
            "• <b>Group</b>: Move user to a specific 'disabled' group\n\n"
            "<i>Group method allows users to stay 'active' but with limited access.</i>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔴 Use Status (default)", callback_data=CallbackData.DISABLE_BY_STATUS)],
            [InlineKeyboardButton("📁 Use Group", callback_data=CallbackData.SELECT_DISABLED_GROUP)],
            [InlineKeyboardButton("« Back to Settings", callback_data=CallbackData.SETTINGS_MENU)],
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        await query.edit_message_text(
            text=f"❌ Error loading disable method: {e}",
            reply_markup=create_back_to_settings_keyboard(),
            parse_mode="HTML"
        )


async def show_groups_for_disabled_selection(query):
    """Fetch and display all groups for selection as disabled group."""
    from utils.panel_api import get_groups
    from utils.read_config import read_config
    from utils.types import PanelType
    
    try:
        await query.edit_message_text(
            text="⏳ Loading groups from panel...",
            parse_mode="HTML"
        )
        
        # Load config for panel data
        config = await read_config()
        panel_config = config.get("panel", {})
        panel_data = PanelType(
            panel_username=panel_config.get("username", ""),
            panel_password=panel_config.get("password", ""),
            panel_domain=panel_config.get("domain", "")
        )
        
        # Fetch groups from panel
        groups = await get_groups(panel_data)
        
        if not groups:
            await query.edit_message_text(
                text=(
                    "📁 <b>No Groups Found</b>\n\n"
                    "Please create groups in your panel first.\n"
                    "Then come back here to select the disabled group."
                ),
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
            return
        
        # Get current disabled group ID
        current_group_id = config.get("disabled_group_id", None)
        
        text = (
            "📁 <b>Select Disabled Group</b>\n\n"
            "Choose a group where disabled users will be moved:\n\n"
            "<i>Users will be moved to this group when disabled,\n"
            "and their original groups will be restored when re-enabled.</i>"
        )
        
        # Create buttons for each group
        keyboard = []
        for group in groups:
            group_id = group.get("id")
            group_name = group.get("name", f"Group {group_id}")
            is_disabled = group.get("is_disabled", False)
            total_users = group.get("total_users", 0)
            
            # Mark current selection
            if group_id == current_group_id:
                label = f"✅ {group_name} ({total_users} users)"
            else:
                label = f"📁 {group_name} ({total_users} users)"
            
            if is_disabled:
                label += " [disabled]"
            
            keyboard.append([InlineKeyboardButton(
                label, 
                callback_data=f"set_disabled_group:{group_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("« Back", callback_data=CallbackData.DISABLE_METHOD_MENU)])
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await query.edit_message_text(
            text=f"❌ Error loading groups: {e}\n\nMake sure your panel is running and credentials are correct.",
            reply_markup=create_back_to_settings_keyboard(),
            parse_mode="HTML"
        )


async def set_disabled_group(query, group_id: int):
    """Set the selected group as the disabled group."""
    try:
        from utils.read_config import save_config_value
        
        await save_config_value("disable_method", "group")
        await save_config_value("disabled_group_id", group_id)
        
        await query.edit_message_text(
            text=(
                f"✅ <b>Disabled Group Set!</b>\n\n"
                f"📁 <b>Group ID:</b> {group_id}\n"
                f"🔧 <b>Method:</b> Group-based\n\n"
                f"From now on, when users are disabled:\n"
                f"• Their current groups will be saved\n"
                f"• They will be moved to group <b>{group_id}</b>\n"
                f"• When re-enabled, their original groups will be restored"
            ),
            reply_markup=create_back_to_settings_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        await query.edit_message_text(
            text=f"❌ Error setting disabled group: {e}",
            reply_markup=create_back_to_settings_keyboard(),
            parse_mode="HTML"
        )


START_MESSAGE = """
✨ <b>Welcome to Limiter Bot!</b>

Use the buttons below to navigate through options, or use these commands:

<b>/start</b> - Show this menu
<b>/help</b> - Show all available commands

📌 <b>Quick Tips:</b>
• Use inline buttons for easy navigation
• All settings are saved automatically
• Reports show real-time data"""


async def send_logs(msg):
    """Send logs to all admins."""
    admins = await check_admin()
    for admin in admins:
        try:
            await application.bot.sendMessage(
                chat_id=admin, text=msg, parse_mode="HTML"
            )
        except Exception as error:  # pylint: disable=broad-except
            print(f"Failed to send message to admin {admin}: {error}")


async def add_admin(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Adds an admin to the bot.
    At first checks if the user has admin privileges.
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    if len(await check_admin()) > 5:
        await update.message.reply_html(
            text="You set more than '5' admins you need to delete one of them to add a new admin\n"
            + "check your active admins with /admins_list\n"
            + "you can delete with /remove_admin command"
        )
        return ConversationHandler.END
    await update.message.reply_html(text="Send chat id: ")
    return GET_CHAT_ID


async def get_chat_id(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Adds a new admin if the provided chat ID is valid and not already an admin.
    """
    new_admin_id = update.message.text.strip()
    try:
        if await add_admin_to_config(new_admin_id):
            await update.message.reply_html(
                text=f"Admin <code>{new_admin_id}</code> added successfully!"
            )
        else:
            await update.message.reply_html(
                text=f"Admin <code>{new_admin_id}</code> already exists!"
            )
    except ValueError:
        await update.message.reply_html(
            text=f"Wrong input: <code>{update.message.text.strip()}"
            + "</code>\ntry again <b>/add_admin</b>"
        )
    return ConversationHandler.END


async def admins_list(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a list of current admins.
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    admins = await check_admin()
    if admins:
        admins_str = "\n- ".join(map(str, admins))
        await update.message.reply_html(text=f"Admins: \n- {admins_str}")
    else:
        await update.message.reply_html(text="No admins found!")
    return ConversationHandler.END


async def check_admin_privilege(update: Update):
    """
    Checks if the user has admin privileges.
    """
    admins = await check_admin()
    if not admins:
        await add_admin_to_config(update.effective_chat.id)
    admins = await check_admin()
    if update.effective_chat.id not in admins:
        await update.message.reply_html(
            text="Sorry, you do not have permission to execute this command."
        )
        return ConversationHandler.END


async def set_special_limit(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    set a special limit for a user.
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_html(
        text="Please send the username. For example: <code>Test_User</code>"
    )
    return GET_SPECIAL_LIMIT


async def get_special_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    get the number of limit for a user.
    """
    context.user_data["selected_user"] = update.message.text.strip()
    await update.message.reply_html(
        text="Please send the Number of limit. For example: <code>4</code> or <code>2</code>"
    )
    return GET_LIMIT_NUMBER


async def get_limit_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sets the special limit for a user if the provided input is a valid number.
    """
    try:
        context.user_data["limit_number"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_html(
            text=f"Wrong input: <code>{update.message.text.strip()}"
            + "</code>\ntry again <b>/set_special_limit</b>"
        )
        return ConversationHandler.END
    out_put = await handel_special_limit(
        context.user_data["selected_user"], context.user_data["limit_number"]
    )
    if out_put[0]:
        await update.message.reply_html(
            text=f"<code>{context.user_data['selected_user']}</code> already has a"
            + " special limit. Change it with new value"
        )
    await update.message.reply_html(
        text=f"Special limit for <code>{context.user_data['selected_user']}</code>"
        + f" set to <code>{out_put[1]}</code> successfully!"
    )
    return ConversationHandler.END


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Start function for the bot."""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_html(
        text=START_MESSAGE,
        reply_markup=create_main_menu_keyboard()
    )


async def help_command(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Show help with all commands."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    help_text = """
✨<b>All Commands:</b>

<b>🔧 Configuration:</b>
/start - Show main menu
/create_config - Setup panel info
/set_ipinfo_token - Set IPInfo API token

<b>🎯 Limits:</b>
/set_special_limit - Set user-specific limit
/show_special_limit - Show special limits
/set_general_limit_number - Set default limit

<b>👥 Users:</b>
/set_except_user - Add to except list
/remove_except_user - Remove from except list
/show_except_users - Show except users

<b>⚙️ Settings:</b>
/country_code - Set country filter
/set_check_interval - Set check interval
/set_time_to_active_users - Set active time
/show_enhanced_details - Toggle enhanced info

<b>📡 Monitoring:</b>
/monitoring_status - Current monitoring status
/monitoring_details - Detailed analytics
/clear_monitoring - Clear all warnings

<b>⚖️ Punishment:</b>
/punishment_status - Show punishment config
/punishment_toggle - Enable/disable system
/punishment_set_window - Set time window
/punishment_set_steps - Configure steps
/user_violations - Check user violations
/clear_user_violations - Clear user history

<b>� Group Filter:</b>
/group_filter_status - Show filter config
/group_filter_toggle - Enable/disable filter
/group_filter_mode - Set include/exclude
/group_filter_set - Set group IDs
/group_filter_add - Add group
/group_filter_remove - Remove group

<b>�📊 Reports:</b>
/connection_report - Connection analysis
/node_usage - Node usage stats
/multi_device_users - Multi-device detection
/ip_history_12h - 12h IP history
/ip_history_48h - 48h IP history

<b>👑 Admin:</b>
/add_admin - Add new admin
/admins_list - List admins
/remove_admin - Remove admin

<b>💾 Backup:</b>
/backup - Download config
/restore - Restore config
"""
    await update.message.reply_html(
        text=help_text,
        reply_markup=create_back_to_main_keyboard()
    )


async def create_config(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Add panel domain, username, and password to add into the config file.
    Note: Panel credentials are now stored in .env file, not config.json.
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    
    # Check if environment variables are already set
    from utils.read_config import load_env_config
    env_config = load_env_config()
    panel_config = env_config.get("panel", {})
    domain = panel_config.get("domain")
    username = panel_config.get("username")
    password = panel_config.get("password")
    
    if domain and password:
        await update.message.reply_html(text="You set configuration before!")
        await update.message.reply_html(
            text="⚠️ <b>Note:</b> Panel credentials are stored in <code>.env</code> file.\n"
            + "To change them, edit the .env file or use:\n"
            + "<code>pg-limiter config</code>\n\n"
            + "<b>Current configuration:</b>\n"
            + f"Domain: <code>{domain}</code>\n"
            + f"Username: <code>{username}</code>\n"
            + f"Password: <code>{'*' * len(password) if password else 'Not set'}</code>"
        )
        return ConversationHandler.END
    
    await update.message.reply_html(
        text="⚠️ Panel credentials should be configured in the <code>.env</code> file.\n\n"
        + "To change settings, edit <code>/etc/opt/pg-limiter/.env</code>\n"
        + "or use <code>pg-limiter config</code> command.\n\n"
        + "Then restart the service with <code>pg-limiter restart</code>"
    )
    return ConversationHandler.END


async def get_confirmation(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Get confirmation for change panel information.
    """
    if update.message.text.lower() in ["yes", "y"]:
        await update.message.reply_html(
            text="So now give me your <b>panel address!</b>\n"
            + "Send The Domain or Ip with Port\n"
            + "like: <code>sub.domain.com:8333</code> Or <code>95.12.153.87:443</code> \n"
            + "<b>without</b> <code>https://</code> or <code>http://</code> or anything else",
        )
        return GET_DOMAIN
    await update.message.reply_html(
        text=f"<code>{update.message.text}</code> received.\n"
        "Use <b>/create_config</b> when you change your mind."
    )
    return ConversationHandler.END


async def get_domain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get panel domain form user"""
    context.user_data["domain"] = update.message.text.strip()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Send Your Username: (For example: 'admin')",
    )
    return GET_USERNAME


async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get panel username form user"""
    context.user_data["username"] = update.message.text.strip()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Send Your Password: (For example: 'admin1234')",
    )
    return GET_PASSWORD


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get panel password form user"""
    context.user_data["password"] = update.message.text.strip()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please wait to check panel address, username and password...",
    )
    try:
        await add_base_information(
            context.user_data["domain"],
            context.user_data["password"],
            context.user_data["username"],
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Config saved successfully 🎊"
        )
    except ValueError:
        await update.message.reply_html(
            text="<b>There is a problem with your information check them again!</b>"
            + " (also make sure the panel is running)"
            + "\n"
            + f"Panel Address: <code>{context.user_data['domain']}</code>\n"
            + f"Username: <code>{context.user_data['username']}</code>\n"
            + f"Password: <code>{context.user_data['password']}</code>\n"
            + "--------\n"
            + "Try again /create_config",
        )

    return ConversationHandler.END


async def remove_admin(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Removes a admin form admin list"""
    check = await check_admin_privilege(update)
    if check:
        return check
    admins_count = len(await check_admin())
    if admins_count == 1:
        await update.message.reply_html(
            text="there is just <b>1</b> active admin remain."
            + " <b>if you delete this chat id, then first person start bot "
            + "is new admin</b> or <b>add admin chat id</b> in <code>ADMIN_IDS</code> environment variable"
        )
    await update.message.reply_html(text="Send chat id of the admin to remove: ")
    return GET_CHAT_ID_TO_REMOVE


async def get_chat_id_to_remove(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Get admin chat id to delete it form admin list"""
    try:
        admin_id_to_remove = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_html(
            text=f"Wrong input: <code>{update.message.text.strip()}"
            + "</code>\ntry again <b>/remove_admin</b>"
        )
        return ConversationHandler.END
    if await remove_admin_from_config(admin_id_to_remove):
        await update.message.reply_html(
            text=f"Admin <code>{admin_id_to_remove}</code> removed successfully!"
        )
    else:
        await update.message.reply_html(
            text=f"Admin <code>{admin_id_to_remove}</code> does not exist!"
        )
    return ConversationHandler.END


async def show_special_limit_function(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
):
    """Show special limit list for all users."""
    check = await check_admin_privilege(update)
    if check:
        return check
    out_put = await get_special_limit_list()
    if out_put:
        for user in out_put:
            await update.message.reply_html(text=user)
    else:
        await update.message.reply_html(text="No special limit found!")


async def set_country_code(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Set the country code for the bot."""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_html(
        "1. <code>IR</code> (Iran)\n"
        + "2. <code>RU</code> (Russia)\n"
        + "3. <code>CN</code> (China)\n"
        + "4. <code>None</code>, don't check the location\n"
        + "<b>just send the number of the country code like: <code>2</code> or <code>1</code></b>"
    )
    return SET_COUNTRY_CODE


async def write_country_code(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Write the country code to the config file."""
    country_code = update.message.text.strip()
    country_codes = {"1": "IR", "2": "RU", "3": "CN", "4": "None"}
    selected_country = country_codes.get(country_code, "None")
    await update.message.reply_html(
        f"Country code <code>{selected_country}</code> set successfully!"
    )
    await write_country_code_json(selected_country)
    return ConversationHandler.END


async def send_backup(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Send a comprehensive backup zip file to the user."""
    import zipfile
    import tempfile
    import shutil
    from datetime import datetime
    
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        await update.message.reply_text("📦 Creating backup... Please wait.")
        
        # Create temp directory for backup
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"pg-limiter-backup-{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add config files from /etc/opt/pg-limiter/ (or local .env)
            config_files = [
                (".env", "config/.env"),
            ]
            for src, dst in config_files:
                if os.path.exists(src):
                    zipf.write(src, dst)
            
            # Also check standard Docker paths
            docker_config_dir = "/etc/opt/pg-limiter"
            if os.path.exists(docker_config_dir):
                for filename in os.listdir(docker_config_dir):
                    filepath = os.path.join(docker_config_dir, filename)
                    if os.path.isfile(filepath):
                        zipf.write(filepath, f"config/{filename}")
            
            # Add data files from /var/lib/pg-limiter/ (or local data/)
            data_dirs = [
                "data",
                "/var/lib/pg-limiter/data",
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
            backup_info = f"""PG-Limiter Backup
Created: {datetime.now().isoformat()}
Hostname: {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}

Contents:
- config/: Configuration files (.env, docker-compose.yml)
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
            f"❌ <b>Error creating backup:</b>\n"
            f"<code>{str(e)}</code>"
        )


async def restore_config(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Start the restore process by asking for the backup file."""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_html(
        "📥 <b>Restore from Backup</b>\n\n"
        "Please send your backup file (zip or json format).\n\n"
        "<b>⚠️ Warning:</b> This will replace your current data!\n"
        "A backup of your current config will be created automatically."
    )
    return RESTORE_CONFIG


async def restore_config_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Handle the uploaded backup file and restore it."""
    import zipfile
    import tempfile
    import shutil
    from datetime import datetime
    
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
        
        # Create backup of current data first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if file_name.endswith('.zip'):
            # Handle zip backup (new format)
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "backup.zip")
            
            with open(zip_path, 'wb') as f:
                f.write(file_content)
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restore .env file if present (warn user about manual steps)
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
                data_dst = "data"
                if os.path.exists("/var/lib/pg-limiter/data"):
                    data_dst = "/var/lib/pg-limiter/data"
                
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
                "📁 <b>Restored:</b>\n"
                f"• Environment file: {'✓' if env_restored else '✗'}\n"
                "• Database: ✓\n\n"
                "⚠️ <b>Important:</b> Please restart the service for changes to take effect."
            )
            
        elif file_name.endswith('.json'):
            # Handle legacy JSON config (old format) - migrate to database
            try:
                config_data = json.loads(file_content.decode('utf-8'))
                
                # Migrate to database using db module
                from db import get_db, ConfigCRUD, UserLimitCRUD, ExceptUserCRUD
                
                async with get_db() as db:
                    # Import settings to database
                    if "disable_method" in config_data:
                        await ConfigCRUD.set(db, "disable_method", str(config_data["disable_method"]))
                    if "disabled_group_id" in config_data and config_data["disabled_group_id"]:
                        await ConfigCRUD.set(db, "disabled_group_id", str(config_data["disabled_group_id"]))
                    if config_data.get("enhanced_details") is not None:
                        await ConfigCRUD.set(db, "enhanced_details", str(config_data["enhanced_details"]).lower())
                    if config_data.get("show_single_ip_users") is not None:
                        await ConfigCRUD.set(db, "show_single_ip_users", str(config_data["show_single_ip_users"]).lower())
                    if config_data.get("ipinfo_token"):
                        await ConfigCRUD.set(db, "ipinfo_token", config_data["ipinfo_token"])
                    
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
                    "📝 <b>Note:</b> Panel credentials and bot token are now stored in .env file.\n"
                    "You may need to update your .env file manually.\n\n"
                    "⚠️ <b>Important:</b> Please restart the service for changes to take effect."
                )
                
            except json.JSONDecodeError as e:
                await update.message.reply_html(
                    f"❌ Invalid JSON format: {str(e)}\n"
                    "Use /restore to try again."
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
            f"❌ <b>Error during restore:</b>\n"
            f"<code>{str(e)}</code>\n\n"
            f"Use /restore to try again."
        )
    
    return ConversationHandler.END


async def set_except_users(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Set the except users for the bot."""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_html(
        "Send the except (<code>users in this list have no limitation</code>) user:"
    )
    return SET_EXCEPT_USERS


async def set_except_users_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Write the except users to the config file."""
    except_user = update.message.text.strip()
    await add_except_user(except_user)
    await update.message.reply_html(
        f"Except user <code>{except_user}</code> added successfully!"
    )
    return ConversationHandler.END


async def remove_except_user(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """remove the except users for the bot."""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_html("Send the except user to remove:")
    return REMOVE_EXCEPT_USER


async def remove_except_user_handler(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
):
    """remove the except users from the config file."""
    except_user = await remove_except_user_from_config(update.message.text.strip())
    if except_user:
        await update.message.reply_html(
            f"Except user <code>{except_user}</code> removed successfully!"
        )

    else:
        await update.message.reply_html(
            f"Except user <code>{except_user}</code> not found!"
        )
    return ConversationHandler.END


async def show_except_users(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Show the except users for the bot."""
    check = await check_admin_privilege(update)
    if check:
        return check
    messages = await show_except_users_handler()
    if messages:
        for message in messages:
            await update.message.reply_html(text=message)
    else:
        await update.message.reply_html(text="No except user found!")
    return ConversationHandler.END


async def get_general_limit_number(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Get the general limit number for the bot."""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_text("Please send the general limit number:")
    return GET_GENERAL_LIMIT_NUMBER


async def get_general_limit_number_handler(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
):
    """Write the general limit number to the config file."""
    try:
        limit_number = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_html(
            text=f"Wrong input: <code>{update.message.text.strip()}"
            + "</code>\ntry again <b>/set_general_limit_number</b>"
        )
        return ConversationHandler.END
    await save_general_limit(limit_number)
    await update.message.reply_text(f"General limit set to {limit_number}")
    return ConversationHandler.END


async def get_check_interval(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """get the 'check_interval' variable that handel how often the bot check the users"""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_text(
        "Please send the check interval time like 210 (its recommended to set it to 240 seconds)"
    )
    return GET_CHECK_INTERVAL


async def get_check_interval_handler(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
):
    """save the 'check_interval' variable"""
    try:
        check_interval = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_html(
            text=f"Wrong input: <code>{update.message.text.strip()}"
            + "</code>\ntry again <b>/set_check_interval</b>"
        )
        return ConversationHandler.END
    await save_check_interval(check_interval)
    await update.message.reply_text(f"CHECK_INTERVAL set to {check_interval}")
    return ConversationHandler.END


async def get_time_to_active_users(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """get the 'time_to_active' variable that handel how long user be not be active"""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_text(
        "Please send the time to active users: like 600 (its in seconds)"
    )
    return GET_TIME_TO_ACTIVE_USERS


async def get_time_to_active_users_handler(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
):
    """save the 'time_to_active' variable"""
    try:
        time_to_active_users = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_html(
            text=f"Wrong input: <code>{update.message.text.strip()}"
            + "</code>\ntry again <b>/set_time_to_active_users</b>"
        )
        return ConversationHandler.END
    await save_time_to_active_users(time_to_active_users)
    await update.message.reply_text(
        f"TIME_TO_ACTIVE_USERS set to {time_to_active_users}"
    )
    return ConversationHandler.END


async def monitoring_status(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Shows the current monitoring status of users who are being watched after warnings.
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        # Import here to avoid circular imports
        from utils.warning_system import warning_system
        
        if not warning_system.warnings:
            await update.message.reply_html(text="🟢 No users are currently being monitored.")
            return ConversationHandler.END
        
        active_warnings = []
        expired_warnings = []
        
        for username, warning in warning_system.warnings.items():
            if warning.is_monitoring_active():
                remaining = warning.time_remaining()
                minutes = remaining // 60
                seconds = remaining % 60
                active_warnings.append(
                    f"• <code>{username}</code> - {warning.ip_count} IPs - {minutes}m {seconds}s remaining"
                )
            else:
                expired_warnings.append(username)
        
        message_parts = []
        
        if active_warnings:
            message_parts.append("🔍 <b>Currently Monitoring:</b>\n" + "\n".join(active_warnings))
        
        if expired_warnings:
            message_parts.append(f"⏰ <b>Expired Warnings:</b> {len(expired_warnings)} users")
        
        if not message_parts:
            message_parts.append("🟢 No active monitoring.")
        
        await update.message.reply_html(text="\n\n".join(message_parts))
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error getting monitoring status: {str(e)}")
    
    return ConversationHandler.END


async def clear_monitoring(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Clears all monitoring warnings (admin only).
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        from utils.warning_system import warning_system
        
        count = len(warning_system.warnings)
        warning_system.warnings.clear()
        await warning_system.save_warnings()
        
        await update.message.reply_html(text=f"✅ Cleared {count} monitoring warnings.")
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error clearing monitoring: {str(e)}")
    
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════
# PUNISHMENT SYSTEM COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

async def punishment_status(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Shows the current punishment system configuration and status.
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        from utils.punishment_system import get_punishment_system
        
        config_data = await read_config()
        system = get_punishment_system()
        system.load_config(config_data)
        
        enabled_text = "✅ Enabled" if system.enabled else "❌ Disabled"
        
        steps_text = []
        for i, step in enumerate(system.steps, 1):
            steps_text.append(f"  {i}. {step.get_display_text()}")
        
        message = (
            f"⚖️ <b>Smart Punishment System</b>\n\n"
            f"Status: {enabled_text}\n"
            f"Time Window: <code>{system.window_hours} hours</code>\n\n"
            f"<b>Punishment Steps:</b>\n"
            f"{chr(10).join(steps_text)}\n\n"
            f"<b>Commands:</b>\n"
            f"/punishment_toggle - Enable/disable\n"
            f"/punishment_set_window - Set time window\n"
            f"/punishment_set_steps - Configure steps\n"
            f"/user_violations &lt;username&gt; - Check user\n"
            f"/clear_user_violations &lt;username&gt; - Clear history"
        )
        
        await update.message.reply_html(text=message)
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def punishment_toggle(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Toggle the punishment system on/off."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        config_data = await read_config()
        
        if "punishment" not in config_data:
            config_data["punishment"] = {"enabled": True, "window_hours": 72, "steps": []}
        
        current_state = config_data["punishment"].get("enabled", True)
        config_data["punishment"]["enabled"] = not current_state
        
        await write_json_file(config_data)
        
        new_state = "✅ Enabled" if not current_state else "❌ Disabled"
        await update.message.reply_html(
            text=f"⚖️ Punishment system is now: {new_state}"
        )
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def punishment_set_window(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the punishment time window."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    # Check if hours provided as argument
    if context.args:
        try:
            hours = int(context.args[0])
            if hours < 1 or hours > 720:  # Max 30 days
                await update.message.reply_html(
                    text="❌ Invalid value. Hours must be between 1 and 720."
                )
                return ConversationHandler.END
            
            config_data = await read_config()
            if "punishment" not in config_data:
                config_data["punishment"] = {"enabled": True, "window_hours": hours, "steps": []}
            else:
                config_data["punishment"]["window_hours"] = hours
            
            await write_json_file(config_data)
            await update.message.reply_html(
                text=f"✅ Punishment time window set to <code>{hours} hours</code>\n"
                     f"Violations older than this will be forgotten."
            )
            return ConversationHandler.END
        except ValueError:
            pass
    
    await update.message.reply_html(
        text="⚖️ <b>Set Punishment Time Window</b>\n\n"
             "Enter the number of hours for the violation window.\n"
             "Violations older than this will not count.\n\n"
             "Example: <code>/punishment_set_window 72</code> (3 days)"
    )
    return ConversationHandler.END


async def punishment_set_steps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Configure punishment steps."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    # Check if JSON provided as argument
    if context.args:
        try:
            steps_json = " ".join(context.args)
            steps_data = json.loads(steps_json)
            
            if not isinstance(steps_data, list) or len(steps_data) == 0:
                raise ValueError("Steps must be a non-empty array")
            
            # Validate each step
            validated_steps = []
            for step in steps_data:
                step_type = step.get("type", "disable")
                duration = step.get("duration", 0)
                if step_type not in ["warning", "disable"]:
                    raise ValueError(f"Invalid step type: {step_type}")
                if not isinstance(duration, int) or duration < 0:
                    raise ValueError(f"Invalid duration: {duration}")
                validated_steps.append({"type": step_type, "duration": duration})
            
            config_data = await read_config()
            if "punishment" not in config_data:
                config_data["punishment"] = {"enabled": True, "window_hours": 72, "steps": validated_steps}
            else:
                config_data["punishment"]["steps"] = validated_steps
            
            await write_json_file(config_data)
            
            steps_display = []
            for i, s in enumerate(validated_steps, 1):
                if s["type"] == "warning":
                    steps_display.append(f"  {i}. ⚠️ Warning")
                elif s["duration"] == 0:
                    steps_display.append(f"  {i}. 🚫 Unlimited disable")
                else:
                    steps_display.append(f"  {i}. 🔒 {s['duration']} min disable")
            
            await update.message.reply_html(
                text=f"✅ Punishment steps updated:\n\n{chr(10).join(steps_display)}"
            )
            return ConversationHandler.END
        except (json.JSONDecodeError, ValueError) as e:
            await update.message.reply_html(text=f"❌ Invalid format: {str(e)}")
            return ConversationHandler.END
    
    await update.message.reply_html(
        text="⚖️ <b>Configure Punishment Steps</b>\n\n"
             "Send steps as JSON array:\n"
             '<code>/punishment_set_steps [{"type":"warning","duration":0},{"type":"disable","duration":15},{"type":"disable","duration":60},{"type":"disable","duration":0}]</code>\n\n'
             "<b>Step types:</b>\n"
             "• <code>warning</code> - Just warn, don't disable\n"
             "• <code>disable</code> - Disable user\n\n"
             "<b>Duration (minutes):</b>\n"
             "• <code>0</code> = Unlimited (for warning: ignored, for disable: permanent)\n"
             "• <code>15</code> = 15 minutes\n"
             "• <code>60</code> = 1 hour\n"
             "• <code>240</code> = 4 hours"
    )
    return ConversationHandler.END


async def user_violations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check violation history for a specific user."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_html(
            text="❌ Please provide a username.\n"
                 "Example: <code>/user_violations username</code>"
        )
        return ConversationHandler.END
    
    username = context.args[0]
    
    try:
        from utils.punishment_system import get_punishment_system
        
        config_data = await read_config()
        system = get_punishment_system()
        system.load_config(config_data)
        
        status = system.get_user_status(username)
        
        if status["violation_count"] == 0:
            await update.message.reply_html(
                text=f"✅ User <code>{username}</code> has no violations in the last {status['window_hours']} hours."
            )
            return ConversationHandler.END
        
        violations_text = []
        for v in status["recent_violations"]:
            step_type = "⚠️ Warning" if v["duration"] == 0 and v["step"] == 0 else f"🔒 {v['duration']}m" if v["duration"] > 0 else "🚫 Unlimited"
            violations_text.append(f"  • {v['time_ago']} - Step {v['step'] + 1} ({step_type})")
        
        message = (
            f"⚖️ <b>Violation History: {username}</b>\n\n"
            f"Total violations: <code>{status['violation_count']}</code>\n"
            f"Window: <code>{status['window_hours']} hours</code>\n\n"
            f"<b>Recent Violations:</b>\n"
            f"{chr(10).join(violations_text)}\n\n"
            f"<b>Next Punishment:</b>\n"
            f"  {status['next_punishment']}"
        )
        
        await update.message.reply_html(text=message)
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def clear_user_violations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear violation history for a specific user."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_html(
            text="❌ Please provide a username.\n"
                 "Example: <code>/clear_user_violations username</code>\n\n"
                 "Use <code>/clear_user_violations ALL</code> to clear all history."
        )
        return ConversationHandler.END
    
    username = context.args[0]
    
    try:
        from utils.punishment_system import get_punishment_system
        
        system = get_punishment_system()
        
        if username.upper() == "ALL":
            await system.clear_all_history()
            await update.message.reply_html(
                text="✅ Cleared all violation history."
            )
        else:
            await system.clear_user_history(username)
            await update.message.reply_html(
                text=f"✅ Cleared violation history for <code>{username}</code>"
            )
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════
# GROUP FILTER COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

async def group_filter_status(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Show the current group filter configuration."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        from utils.user_group_filter import get_filter_status_text, get_all_groups
        from utils.types import PanelType
        
        config_data = await read_config()
        
        # Get panel data for group lookup
        panel_config = config_data.get("panel", {})
        panel_data = PanelType(
            panel_config.get("username", ""),
            panel_config.get("password", ""),
            panel_config.get("domain", "")
        )
        
        # Get all groups for name lookup
        groups = await get_all_groups(panel_data)
        
        # Get filter status
        status_text = get_filter_status_text(config_data, groups)
        
        # Build groups list
        groups_list = []
        for group in groups:
            gid = group.get("id", "?")
            name = group.get("name", "Unknown")
            groups_list.append(f"  • <code>{gid}</code> - {name}")
        
        groups_display = "\n".join(groups_list) if groups_list else "  No groups found"
        
        message = (
            f"🔍 <b>Group Filter Status</b>\n\n"
            f"{status_text}\n\n"
            f"<b>Available Groups:</b>\n{groups_display}\n\n"
            f"<b>Commands:</b>\n"
            f"/group_filter_toggle - Enable/disable\n"
            f"/group_filter_mode - Set include/exclude\n"
            f"/group_filter_set - Set groups\n"
            f"/group_filter_add - Add group\n"
            f"/group_filter_remove - Remove group"
        )
        
        await update.message.reply_html(text=message)
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def group_filter_toggle(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Toggle group filter on/off."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        config_data = await read_config()
        
        if "group_filter" not in config_data:
            config_data["group_filter"] = {"enabled": True, "mode": "include", "group_ids": []}
        
        current_state = config_data["group_filter"].get("enabled", False)
        config_data["group_filter"]["enabled"] = not current_state
        
        await write_json_file(config_data)
        
        new_state = "✅ Enabled" if not current_state else "❌ Disabled"
        await update.message.reply_html(
            text=f"🔍 Group filter is now: {new_state}"
        )
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def group_filter_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set group filter mode (include/exclude)."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if context.args:
        mode = context.args[0].lower()
        if mode not in ["include", "exclude"]:
            await update.message.reply_html(
                text="❌ Invalid mode. Use <code>include</code> or <code>exclude</code>"
            )
            return ConversationHandler.END
        
        try:
            config_data = await read_config()
            
            if "group_filter" not in config_data:
                config_data["group_filter"] = {"enabled": False, "mode": mode, "group_ids": []}
            else:
                config_data["group_filter"]["mode"] = mode
            
            await write_json_file(config_data)
            
            if mode == "include":
                desc = "Only users in specified groups will be monitored"
            else:
                desc = "Users in specified groups will be whitelisted"
            
            await update.message.reply_html(
                text=f"✅ Group filter mode set to: <code>{mode}</code>\n{desc}"
            )
            
        except Exception as e:
            await update.message.reply_html(text=f"❌ Error: {str(e)}")
        
        return ConversationHandler.END
    
    await update.message.reply_html(
        text="🔍 <b>Set Group Filter Mode</b>\n\n"
             "<code>/group_filter_mode include</code>\n"
             "  → Only users in specified groups are monitored\n\n"
             "<code>/group_filter_mode exclude</code>\n"
             "  → Users in specified groups are whitelisted (not limited)"
    )
    return ConversationHandler.END


async def group_filter_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the list of group IDs for filtering."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if context.args:
        try:
            # Parse group IDs from arguments
            group_ids = []
            for arg in context.args:
                # Support comma-separated and space-separated
                for gid in arg.split(","):
                    gid = gid.strip()
                    if gid:
                        group_ids.append(int(gid))
            
            config_data = await read_config()
            
            if "group_filter" not in config_data:
                config_data["group_filter"] = {"enabled": False, "mode": "include", "group_ids": group_ids}
            else:
                config_data["group_filter"]["group_ids"] = group_ids
            
            await write_json_file(config_data)
            
            await update.message.reply_html(
                text=f"✅ Group filter set to IDs: <code>{group_ids}</code>"
            )
            
        except ValueError:
            await update.message.reply_html(
                text="❌ Invalid group ID. Please provide numeric IDs."
            )
        except Exception as e:
            await update.message.reply_html(text=f"❌ Error: {str(e)}")
        
        return ConversationHandler.END
    
    await update.message.reply_html(
        text="🔍 <b>Set Group Filter Groups</b>\n\n"
             "Usage: <code>/group_filter_set 1 2 3</code>\n"
             "Or: <code>/group_filter_set 1,2,3</code>\n\n"
             "Use /group_filter_status to see available groups."
    )
    return ConversationHandler.END


async def group_filter_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a group ID to the filter."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_html(
            text="❌ Please provide a group ID.\n"
                 "Example: <code>/group_filter_add 5</code>"
        )
        return ConversationHandler.END
    
    try:
        group_id = int(context.args[0])
        
        config_data = await read_config()
        
        if "group_filter" not in config_data:
            config_data["group_filter"] = {"enabled": False, "mode": "include", "group_ids": [group_id]}
        else:
            current_ids = config_data["group_filter"].get("group_ids", [])
            if group_id not in current_ids:
                current_ids.append(group_id)
                config_data["group_filter"]["group_ids"] = current_ids
            else:
                await update.message.reply_html(
                    text=f"ℹ️ Group ID <code>{group_id}</code> is already in the filter."
                )
                return ConversationHandler.END
        
        await write_json_file(config_data)
        
        await update.message.reply_html(
            text=f"✅ Added group ID <code>{group_id}</code> to filter.\n"
                 f"Current groups: <code>{config_data['group_filter']['group_ids']}</code>"
        )
        
    except ValueError:
        await update.message.reply_html(text="❌ Invalid group ID. Please provide a number.")
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def group_filter_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a group ID from the filter."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_html(
            text="❌ Please provide a group ID.\n"
                 "Example: <code>/group_filter_remove 5</code>"
        )
        return ConversationHandler.END
    
    try:
        group_id = int(context.args[0])
        
        config_data = await read_config()
        
        if "group_filter" not in config_data:
            await update.message.reply_html(
                text="❌ No group filter configured."
            )
            return ConversationHandler.END
        
        current_ids = config_data["group_filter"].get("group_ids", [])
        if group_id in current_ids:
            current_ids.remove(group_id)
            config_data["group_filter"]["group_ids"] = current_ids
            await write_json_file(config_data)
            
            await update.message.reply_html(
                text=f"✅ Removed group ID <code>{group_id}</code> from filter.\n"
                     f"Remaining groups: <code>{current_ids}</code>"
            )
        else:
            await update.message.reply_html(
                text=f"ℹ️ Group ID <code>{group_id}</code> is not in the filter."
            )
        
    except ValueError:
        await update.message.reply_html(text="❌ Invalid group ID. Please provide a number.")
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN FILTER COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

async def admin_filter_status(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Show the current admin filter configuration."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        from utils.admin_filter import get_admin_filter_status_text, get_all_admins
        from utils.types import PanelType
        
        config_data = await read_config()
        
        # Get panel data for admin lookup
        panel_config = config_data.get("panel", {})
        panel_data = PanelType(
            panel_config.get("username", ""),
            panel_config.get("password", ""),
            panel_config.get("domain", "")
        )
        
        # Get all admins for display
        admins = await get_all_admins(panel_data)
        
        # Get filter status
        status_text = get_admin_filter_status_text(config_data, admins)
        
        # Build admins list
        admins_list = []
        for admin in admins:
            username = admin.get("username", "?")
            is_sudo = "👑" if admin.get("is_sudo", False) else ""
            is_disabled = "🔒" if admin.get("is_disabled", False) else ""
            admins_list.append(f"  • <code>{username}</code> {is_sudo}{is_disabled}")
        
        admins_display = "\n".join(admins_list) if admins_list else "  No admins found"
        
        message = (
            f"👤 <b>Admin Filter Status</b>\n\n"
            f"{status_text}\n\n"
            f"<b>Available Admins:</b>\n{admins_display}\n\n"
            f"<b>Commands:</b>\n"
            f"/admin_filter_toggle - Enable/disable\n"
            f"/admin_filter_mode - Set include/exclude\n"
            f"/admin_filter_set - Set admin usernames\n"
            f"/admin_filter_add - Add admin\n"
            f"/admin_filter_remove - Remove admin"
        )
        
        await update.message.reply_html(text=message)
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def admin_filter_toggle(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Toggle admin filter on/off."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        from utils.read_config import save_config_value, invalidate_config_cache
        
        config_data = await read_config()
        filter_config = config_data.get("admin_filter", {})
        current_state = filter_config.get("enabled", False)
        new_state = not current_state
        
        await save_config_value("admin_filter_enabled", "true" if new_state else "false")
        invalidate_config_cache()
        
        status = "✅ Enabled" if new_state else "❌ Disabled"
        await update.message.reply_html(
            text=f"👤 Admin filter is now: {status}"
        )
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def admin_filter_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set admin filter mode (include/exclude)."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if context.args:
        mode = context.args[0].lower()
        if mode not in ["include", "exclude"]:
            await update.message.reply_html(
                text="❌ Invalid mode. Use <code>include</code> or <code>exclude</code>"
            )
            return ConversationHandler.END
        
        try:
            from utils.read_config import save_config_value, invalidate_config_cache
            
            await save_config_value("admin_filter_mode", mode)
            invalidate_config_cache()
            
            if mode == "include":
                desc = "Only users of specified admins will be monitored"
            else:
                desc = "Users of specified admins will be whitelisted"
            
            await update.message.reply_html(
                text=f"✅ Admin filter mode set to: <code>{mode}</code>\n{desc}"
            )
            
        except Exception as e:
            await update.message.reply_html(text=f"❌ Error: {str(e)}")
        
        return ConversationHandler.END
    
    await update.message.reply_html(
        text="👤 <b>Set Admin Filter Mode</b>\n\n"
             "<code>/admin_filter_mode include</code>\n"
             "  → Only users of specified admins are monitored\n\n"
             "<code>/admin_filter_mode exclude</code>\n"
             "  → Users of specified admins are whitelisted (not limited)"
    )
    return ConversationHandler.END


async def admin_filter_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the list of admin usernames for filtering."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if context.args:
        try:
            from utils.read_config import save_config_value, invalidate_config_cache
            
            # Parse admin usernames from arguments
            admin_usernames = []
            for arg in context.args:
                # Support comma-separated and space-separated
                for username in arg.split(","):
                    username = username.strip()
                    if username:
                        admin_usernames.append(username)
            
            # Save as comma-separated string
            await save_config_value("admin_filter_usernames", ",".join(admin_usernames))
            invalidate_config_cache()
            
            await update.message.reply_html(
                text=f"✅ Admin filter set to: <code>{admin_usernames}</code>"
            )
            
        except Exception as e:
            await update.message.reply_html(text=f"❌ Error: {str(e)}")
        
        return ConversationHandler.END
    
    await update.message.reply_html(
        text="👤 <b>Set Admin Filter Admins</b>\n\n"
             "Usage: <code>/admin_filter_set admin1 admin2</code>\n"
             "Or: <code>/admin_filter_set admin1,admin2</code>\n\n"
             "Use /admin_filter_status to see available admins."
    )
    return ConversationHandler.END


async def admin_filter_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add an admin username to the filter."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_html(
            text="❌ Please provide an admin username.\n"
                 "Example: <code>/admin_filter_add admin1</code>"
        )
        return ConversationHandler.END
    
    try:
        from utils.read_config import save_config_value, invalidate_config_cache
        
        admin_username = context.args[0].strip()
        
        config_data = await read_config()
        filter_config = config_data.get("admin_filter", {})
        current_admins = filter_config.get("admin_usernames", [])
        
        if admin_username in current_admins:
            await update.message.reply_html(
                text=f"ℹ️ Admin <code>{admin_username}</code> is already in the filter."
            )
            return ConversationHandler.END
        
        current_admins.append(admin_username)
        await save_config_value("admin_filter_usernames", ",".join(current_admins))
        invalidate_config_cache()
        
        await update.message.reply_html(
            text=f"✅ Added admin <code>{admin_username}</code> to filter.\n"
                 f"Current admins: <code>{current_admins}</code>"
        )
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def admin_filter_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove an admin username from the filter."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_html(
            text="❌ Please provide an admin username.\n"
                 "Example: <code>/admin_filter_remove admin1</code>"
        )
        return ConversationHandler.END
    
    try:
        from utils.read_config import save_config_value, invalidate_config_cache
        
        admin_username = context.args[0].strip()
        
        config_data = await read_config()
        filter_config = config_data.get("admin_filter", {})
        current_admins = filter_config.get("admin_usernames", [])
        
        if admin_username not in current_admins:
            await update.message.reply_html(
                text=f"ℹ️ Admin <code>{admin_username}</code> is not in the filter."
            )
            return ConversationHandler.END
        
        current_admins.remove(admin_username)
        await save_config_value("admin_filter_usernames", ",".join(current_admins))
        invalidate_config_cache()
        
        await update.message.reply_html(
            text=f"✅ Removed admin <code>{admin_username}</code> from filter.\n"
                 f"Remaining admins: <code>{current_admins}</code>"
        )
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def connection_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send connection analysis report."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        report = await generate_connection_report()
        # Split long messages to avoid Telegram's message length limit
        max_length = 4000
        if len(report) <= max_length:
            await update.message.reply_text(f"<code>{report}</code>", parse_mode="HTML")
        else:
            # Split the report into smaller chunks
            chunks = [report[i:i+max_length] for i in range(0, len(report), max_length)]
            for i, chunk in enumerate(chunks):
                await update.message.reply_text(
                    f"<code>Part {i+1}/{len(chunks)}:\n{chunk}</code>", 
                    parse_mode="HTML"
                )
    except Exception as e:
        await update.message.reply_text(f"Error generating report: {str(e)}")


async def node_usage_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send node usage report."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        report = await generate_node_usage_report()
        await update.message.reply_text(f"<code>{report}</code>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Error generating report: {str(e)}")


async def multi_device_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users identified as using multiple devices."""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        multi_device_users = await get_multi_device_users()
        if not multi_device_users:
            await update.message.reply_text("No multi-device users detected.")
            return
        
        report_lines = ["<b>Multi-Device Users:</b>\n"]
        for username, ip_count, node_count, protocols in multi_device_users:
            report_lines.append(f"<code>{username}</code>")
            report_lines.append(f"  • {ip_count} unique IPs")
            report_lines.append(f"  • {node_count} different nodes")
            report_lines.append(f"  • Protocols: {', '.join(protocols)}")
            report_lines.append("")
        
        report = "\n".join(report_lines)
        await update.message.reply_text(report, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Error generating report: {str(e)}")


async def users_by_node_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users by node. Usage: /users_by_node <node_id>"""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_text("Usage: /users_by_node <node_id>")
        return
    
    try:
        node_id = int(context.args[0])
        users_on_node = await get_users_by_node(node_id)
        
        if not users_on_node:
            await update.message.reply_text(f"No users found on node {node_id}.")
            return
        
        report_lines = [f"<b>Users on Node {node_id}:</b>\n"]
        for username, ip, protocol in users_on_node:
            report_lines.append(f"<code>{username}</code>")
            report_lines.append(f"  • IP: {ip}")
            report_lines.append(f"  • Protocol: {protocol}")
            report_lines.append("")
        
        report = "\n".join(report_lines)
        await update.message.reply_text(report, parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("Invalid node ID. Please provide a valid number.")
    except Exception as e:
        await update.message.reply_text(f"Error generating report: {str(e)}")


async def users_by_protocol_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users by inbound protocol. Usage: /users_by_protocol <protocol>"""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    if not context.args:
        await update.message.reply_text("Usage: /users_by_protocol <protocol>\nExample: /users_by_protocol \"Vless Direct\"")
        return
    
    try:
        protocol = " ".join(context.args)
        users_with_protocol = await get_users_by_inbound_protocol(protocol)
        
        if not users_with_protocol:
            await update.message.reply_text(f"No users found using protocol '{protocol}'.")
            return
        
        report_lines = [f"<b>Users using protocol '{protocol}':</b>\n"]
        for username, ip, node_name in users_with_protocol:
            report_lines.append(f"<code>{username}</code>")
            report_lines.append(f"  • IP: {ip}")
            report_lines.append(f"  • Node: {node_name}")
            report_lines.append("")
        
        report = "\n".join(report_lines)
        await update.message.reply_text(report, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Error generating report: {str(e)}")


async def ip_history_12h_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users exceeding limits in last 12 hours"""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        await update.message.reply_text("⏳ Generating 12-hour IP history report...")
        
        from utils.ip_history_tracker import ip_history_tracker
        from utils.isp_detector import ISPDetector
        
        config_data = await read_config()
        
        # Get ISP detector with token if available
        isp_detector = None
        ipinfo_token = config_data.get("IPINFO_TOKEN", "")
        use_fallback_api = config_data.get("USE_FALLBACK_ISP_API", False)
        if ipinfo_token or use_fallback_api:
            isp_detector = ISPDetector(token=ipinfo_token, use_fallback_only=use_fallback_api)
        
        # Generate report
        report = await ip_history_tracker.generate_report(12, config_data, isp_detector)
        
        # Split if too long (Telegram limit)
        if len(report) > 4000:
            # Split into chunks
            chunks = []
            lines = report.split("\n")
            current_chunk = []
            current_length = 0
            
            for line in lines:
                if current_length + len(line) + 1 > 3500:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_length = len(line)
                else:
                    current_chunk.append(line)
                    current_length += len(line) + 1
            
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                if i > 0:
                    chunk = f"<b>Part {i+1}/{len(chunks)}</b>\n\n" + chunk
                await update.message.reply_text(chunk, parse_mode="HTML")
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)
        else:
            await update.message.reply_text(report, parse_mode="HTML")
            
    except Exception as e:
        await update.message.reply_text(f"Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()


async def ip_history_48h_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users exceeding limits in last 48 hours"""
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        await update.message.reply_text("⏳ Generating 48-hour IP history report...")
        
        from utils.ip_history_tracker import ip_history_tracker
        from utils.isp_detector import ISPDetector
        
        config_data = await read_config()
        
        # Get ISP detector with token if available
        isp_detector = None
        ipinfo_token = config_data.get("IPINFO_TOKEN", "")
        use_fallback_api = config_data.get("USE_FALLBACK_ISP_API", False)
        if ipinfo_token or use_fallback_api:
            isp_detector = ISPDetector(token=ipinfo_token, use_fallback_only=use_fallback_api)
        
        # Generate report
        report = await ip_history_tracker.generate_report(48, config_data, isp_detector)
        
        # Split if too long (Telegram limit)
        if len(report) > 4000:
            # Split into chunks
            chunks = []
            lines = report.split("\n")
            current_chunk = []
            current_length = 0
            
            for line in lines:
                if current_length + len(line) + 1 > 3500:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_length = len(line)
                else:
                    current_chunk.append(line)
                    current_length += len(line) + 1
            
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                if i > 0:
                    chunk = f"<b>Part {i+1}/{len(chunks)}</b>\n\n" + chunk
                await update.message.reply_text(chunk, parse_mode="HTML")
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)
        else:
            await update.message.reply_text(report, parse_mode="HTML")
            
    except Exception as e:
        await update.message.reply_text(f"Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()


async def monitoring_details(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Shows detailed monitoring analytics for users being watched after warnings.
    """
    check = await check_admin_privilege(update)
    if check:
        return check
    
    try:
        # Import here to avoid circular imports
        from utils.warning_system import warning_system
        
        if not warning_system.warnings:
            await update.message.reply_html(text="🟢 No users are currently being monitored.")
            return ConversationHandler.END
        
        message_parts = []
        
        for username, warning in warning_system.warnings.items():
            if warning.is_monitoring_active():
                remaining = warning.time_remaining()
                minutes = remaining // 60
                seconds = remaining % 60
                
                # Get analysis data
                analysis = await warning_system.analyze_user_activity_patterns(username)
                consistently_active_ips = analysis.get('consistently_active_ips', set())
                
                user_details = [
                    f"👤 <b>{username}</b>",
                    f"⏰ Time remaining: {minutes}m {seconds}s",
                    f"📊 Current IPs: {warning.ip_count}",
                    f"🔥 Consistently active IPs (4+ min): {len(consistently_active_ips)}",
                    f"📈 Monitoring snapshots: {analysis.get('total_snapshots', 0)}",
                    f"🔄 IP change frequency: {analysis.get('ip_change_frequency', 0):.2f}",
                    f"📊 Peak IP count: {analysis.get('peak_ip_count', 0)}",
                    f"📊 Average IP count: {analysis.get('average_ip_count', 0):.1f}"
                ]
                
                if consistently_active_ips:
                    user_details.append(f"🌐 Consistently active IPs: {', '.join(list(consistently_active_ips)[:5])}")
                    if len(consistently_active_ips) > 5:
                        user_details.append(f"... and {len(consistently_active_ips) - 5} more")
                
                message_parts.append("\n".join(user_details))
        
        if not message_parts:
            message_parts.append("🟢 No active monitoring.")
        
        final_message = "🔍 <b>Detailed Monitoring Analytics:</b>\n\n" + "\n\n".join(message_parts)
        
        # Check message length and split if necessary
        if len(final_message) > 4000:
            parts = []
            current_part = "🔍 <b>Detailed Monitoring Analytics:</b>\n\n"
            
            for part in message_parts:
                if len(current_part + part + "\n\n") > 4000:
                    parts.append(current_part.strip())
                    current_part = part + "\n\n"
                else:
                    current_part += part + "\n\n"
            
            if current_part.strip():
                parts.append(current_part.strip())
            
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_html(text=part)
                else:
                    await update.message.reply_html(text=f"<b>Part {i+1}:</b>\n\n{part}")
        else:
            await update.message.reply_html(text=final_message)
        
    except Exception as e:
        await update.message.reply_html(text=f"❌ Error getting monitoring details: {str(e)}")
    
    return ConversationHandler.END


async def set_ipinfo_token(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Set the ipinfo.io API token for ISP detection."""
    check = await check_admin_privilege(update)
    if check:
        return check
    await update.message.reply_html(
        "Please send your ipinfo.io API token:\n\n"
        + "ℹ️ <b>How to get a token:</b>\n"
        + "1. Go to https://ipinfo.io\n"
        + "2. Sign up for a free account\n"
        + "3. Copy your API token from the dashboard\n"
        + "4. Send it here\n\n"
        + "📊 <b>Benefits:</b>\n"
        + "• Shows ISP name for each IP\n"
        + "• Shows country information\n"
        + "• 50,000 free requests per month\n\n"
        + "💡 <b>Example:</b> <code>acf060906ef428</code>\n"
        + "Or send <code>remove</code> to remove the token"
    )
    return SET_IPINFO_TOKEN


async def set_ipinfo_token_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Write the ipinfo.io token to the config file."""
    token = update.message.text.strip()
    
    if token.lower() == "remove":
        # Remove the token
        await save_ipinfo_token("")
        await update.message.reply_html(
            "✅ IPINFO_TOKEN removed successfully!\n\n"
            + "IP addresses will be shown without ISP information."
        )
        return ConversationHandler.END
    
    # Validate token format (basic check)
    if len(token) < 10:
        await update.message.reply_html(
            "❌ Invalid token format!\n\n"
            + "Token should be longer than 10 characters.\n"
            + "Try again with <b>/set_ipinfo_token</b>"
        )
        return ConversationHandler.END
    
    # Test the token
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://ipinfo.io/8.8.8.8/json?token={token}", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if "org" in data:
                        # Token is valid
                        await save_ipinfo_token(token)
                        await update.message.reply_html(
                            f"✅ IPINFO_TOKEN set successfully!\n\n"
                            + f"🧪 <b>Test result:</b>\n"
                            + f"IP: 8.8.8.8\n"
                            + f"ISP: {data.get('org', 'Unknown')}\n"
                            + f"Country: {data.get('country', 'Unknown')}\n\n"
                            + "ISP detection is now enabled!"
                        )
                    else:
                        await update.message.reply_html(
                            "❌ Invalid token response!\n\n"
                            + "Please check your token and try again."
                        )
                elif response.status == 401:
                    await update.message.reply_html(
                        "❌ Invalid token!\n\n"
                        + "Please check your token and try again."
                    )
                else:
                    await update.message.reply_html(
                        f"❌ API error (HTTP {response.status})!\n\n"
                        + "Please try again later."
                    )
    except Exception as e:
        await update.message.reply_html(
            f"❌ Error testing token: {str(e)}\n\n"
            + "Please try again."
        )
    
    return ConversationHandler.END


async def save_ipinfo_token(token: str):
    """Save the ipinfo.io token to the config file."""
    try:
        config = await read_json_file()
        if "api" not in config:
            config["api"] = {}
        config["api"]["ipinfo_token"] = token
        await write_json_file(config)
        return True
    except Exception as e:
        print(f"Error saving ipinfo token: {e}")
        return False


async def show_enhanced_details_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show/hide detailed node and protocol information."""
    check = await check_admin_privilege(update)
    if check:
        return check

    if not context.args:
        # Show current status
        try:
            config = await read_json_file()
            value = config.get("display", {}).get("show_enhanced_details", True)
            await update.message.reply_html(
                f"SHOW_ENHANCED_DETAILS is currently <b>{'on' if value else 'off'}</b>.\n\n"
                + "ℹ️ <b>What this controls:</b>\n"
                + "• <b>ON</b>: Shows node names, IDs, and protocols\n"
                + "  Example: <code>IP → UK-NEW(5) | Vless Direct</code>\n"
                + "• <b>OFF</b>: Shows only IP addresses (shorter messages)\n"
                + "  Example: <code>IP</code>\n\n"
                + "💡 <b>Usage:</b> <code>/show_enhanced_details on</code> or <code>/show_enhanced_details off</code>"
            )
        except Exception as e:
            await update.message.reply_html(f"Failed to read config: <code>{e}</code>")
        return

    if context.args[0].lower() not in ("on", "off"):
        await update.message.reply_html(
            "Usage: <code>/show_enhanced_details on</code> or <code>/show_enhanced_details off</code>"
        )
        return

    value = context.args[0].lower() == "on"
    
    # Update config in database
    try:
        from utils.read_config import save_config_value
        await save_config_value("enhanced_details", str(value).lower())
        
        status = "enabled" if value else "disabled"
        detail_info = (
            "IP → UK-NEW(5) | Vless Direct" if value 
            else "IP only"
        )
        
        await update.message.reply_html(
            f"✅ SHOW_ENHANCED_DETAILS <b>{status}</b>!\n\n"
            + f"📋 <b>Format:</b> {detail_info}\n\n"
            + "Changes will take effect in the next user report."
        )
    except Exception as e:
        await update.message.reply_html(f"Failed to update config: <code>{e}</code>")


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    # Check admin privilege
    admins = await check_admin()
    if not admins:
        await add_admin_to_config(update.effective_chat.id)
    admins = await check_admin()
    if update.effective_chat.id not in admins:
        await query.edit_message_text(
            text="Sorry, you do not have permission to execute this command."
        )
        return
    
    data = query.data
    
    # Main menu
    if data == CallbackData.MAIN_MENU or data == CallbackData.BACK_MAIN:
        await query.edit_message_text(
            text=START_MESSAGE,
            reply_markup=create_main_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Settings menu
    if data == CallbackData.SETTINGS_MENU or data == CallbackData.BACK_SETTINGS:
        await query.edit_message_text(
            text="⚙️ <b>Settings Menu</b>\n\nConfigure your bot settings:",
            reply_markup=create_settings_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Limits menu
    if data == CallbackData.LIMITS_MENU or data == CallbackData.BACK_LIMITS:
        await query.edit_message_text(
            text="🎯 <b>Limits Menu</b>\n\nManage user connection limits:",
            reply_markup=create_limits_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Users menu
    if data == CallbackData.USERS_MENU:
        await query.edit_message_text(
            text="👥 <b>Users Menu</b>\n\nManage users and view disabled accounts:",
            reply_markup=create_users_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Disabled users menu
    if data == CallbackData.SHOW_DISABLED_USERS:
        await show_disabled_users_menu(query)
        return
    
    # Enable all disabled users
    if data == CallbackData.ENABLE_ALL_DISABLED:
        await enable_all_disabled_users(query)
        return
    
    # Cleanup deleted users
    if data == CallbackData.CLEANUP_DELETED_USERS:
        await cleanup_deleted_users_handler(query)
        return
    
    # Enable single user (dynamic callback)
    if data.startswith("enable_user:"):
        username = data.split(":", 1)[1]
        await enable_single_user(query, username)
        return
    
    # Pagination for disabled users
    if data.startswith("disabled_page:"):
        page = int(data.split(":", 1)[1])
        await show_disabled_users_menu(query, page=page)
        return
    
    # User info (when clicking on user name)
    if data.startswith("user_info:"):
        import time
        from utils.handel_dis_users import DisabledUsers
        username = data.split(":", 1)[1]
        dis_users = DisabledUsers()
        disabled_time = dis_users.disabled_users.get(username)
        
        if disabled_time:
            elapsed = int(time.time() - disabled_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            disabled_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(disabled_time))
            
            info_text = (
                f"ℹ️ <b>User Info: {username}</b>\n\n"
                f"🔴 <b>Status:</b> Disabled\n"
                f"📅 <b>Disabled at:</b> {disabled_at}\n"
                f"⏱️ <b>Elapsed:</b> {minutes}m {seconds}s\n\n"
                f"<i>Click Enable to re-activate this user.</i>"
            )
            
            keyboard = [
                [InlineKeyboardButton(f"✅ Enable {username}", callback_data=f"enable_user:{username}")],
                [InlineKeyboardButton("« Back to Disabled Users", callback_data=CallbackData.SHOW_DISABLED_USERS)],
            ]
            await query.edit_message_text(
                text=info_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            await query.answer(f"User {username} is no longer disabled!")
            await show_disabled_users_menu(query)
        return
    
    # Monitoring menu
    if data == CallbackData.MONITORING_MENU:
        await query.edit_message_text(
            text="📡 <b>Monitoring Menu</b>\n\nView and manage user monitoring:",
            reply_markup=create_monitoring_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Reports menu
    if data == CallbackData.REPORTS_MENU:
        await query.edit_message_text(
            text="📊 <b>Reports Menu</b>\n\nGenerate various reports:",
            reply_markup=create_reports_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Admin menu
    if data == CallbackData.ADMIN_MENU:
        await query.edit_message_text(
            text="👑 <b>Admin Menu</b>\n\nManage bot administrators:",
            reply_markup=create_admin_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Country code menu
    if data == "country_menu":
        await query.edit_message_text(
            text="🌍 <b>Select Country</b>\n\nOnly IPs from the selected country will be counted:",
            reply_markup=create_country_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Country selections
    if data in [CallbackData.COUNTRY_IR, CallbackData.COUNTRY_RU, CallbackData.COUNTRY_CN, CallbackData.COUNTRY_NONE]:
        country_map = {
            CallbackData.COUNTRY_IR: ("IR", "🇮🇷 Iran"),
            CallbackData.COUNTRY_RU: ("RU", "🇷🇺 Russia"),
            CallbackData.COUNTRY_CN: ("CN", "🇨🇳 China"),
            CallbackData.COUNTRY_NONE: ("None", "🌐 None (all countries)"),
        }
        code, name = country_map[data]
        await write_country_code_json(code)
        await query.edit_message_text(
            text=f"✅ Country set to <b>{name}</b>",
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Check interval menu
    if data == "interval_menu":
        await query.edit_message_text(
            text="⏱️ <b>Check Interval</b>\n\nHow often should the bot check users (in seconds):",
            reply_markup=create_interval_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Interval selections
    if data in [CallbackData.INTERVAL_120, CallbackData.INTERVAL_180, CallbackData.INTERVAL_240]:
        interval_map = {
            CallbackData.INTERVAL_120: 120,
            CallbackData.INTERVAL_180: 180,
            CallbackData.INTERVAL_240: 240,
        }
        interval = interval_map[data]
        await save_check_interval(interval)
        await query.edit_message_text(
            text=f"✅ Check interval set to <b>{interval} seconds</b> ({interval // 60} minutes)",
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    if data == CallbackData.INTERVAL_CUSTOM:
        context.user_data["waiting_for"] = "check_interval"
        await query.edit_message_text(
            text="⏱️ <b>Custom Check Interval</b>\n\nSend the interval in seconds (e.g., <code>300</code>):",
            parse_mode="HTML"
        )
        return
    
    # Time to active menu
    if data == "time_menu":
        await query.edit_message_text(
            text="⏰ <b>Time to Active</b>\n\nHow long should a user be considered active (in seconds):",
            reply_markup=create_time_to_active_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Time selections
    if data in [CallbackData.TIME_300, CallbackData.TIME_600, CallbackData.TIME_900]:
        time_map = {
            CallbackData.TIME_300: 300,
            CallbackData.TIME_600: 600,
            CallbackData.TIME_900: 900,
        }
        time_val = time_map[data]
        await save_time_to_active_users(time_val)
        await query.edit_message_text(
            text=f"✅ Time to active set to <b>{time_val} seconds</b> ({time_val // 60} minutes)",
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    if data == CallbackData.TIME_CUSTOM:
        context.user_data["waiting_for"] = "time_to_active"
        await query.edit_message_text(
            text="⏰ <b>Custom Time to Active</b>\n\nSend the time in seconds (e.g., <code>1200</code>):",
            parse_mode="HTML"
        )
        return
    
    # Enhanced details menu
    if data == "enhanced_menu":
        try:
            from utils.read_config import read_config
            config = await read_config()
            value = config.get("enhanced_details", True)
            status = "ON ✅" if value else "OFF ❌"
        except:
            status = "Unknown"
        await query.edit_message_text(
            text=f"📋 <b>Enhanced Details</b>\n\nCurrently: <b>{status}</b>\n\n"
                 + "• <b>ON</b>: Shows node names, IDs, and protocols\n"
                 + "• <b>OFF</b>: Shows only IP addresses",
            reply_markup=create_enhanced_details_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Enhanced details toggles
    if data in [CallbackData.ENHANCED_ON, CallbackData.ENHANCED_OFF]:
        value = data == CallbackData.ENHANCED_ON
        try:
            from utils.read_config import save_config_value
            await save_config_value("enhanced_details", str(value).lower())
            status = "enabled ✅" if value else "disabled ❌"
            await query.edit_message_text(
                text=f"✅ Enhanced details <b>{status}</b>",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PUNISHMENT SYSTEM CALLBACKS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Punishment menu
    if data == CallbackData.PUNISHMENT_MENU:
        try:
            config_data = await read_config()
            punishment_config = config_data.get("punishment", {})
            enabled = punishment_config.get("enabled", True)
            window_hours = punishment_config.get("window_hours", 72)
            
            await query.edit_message_text(
                text=f"⚖️ <b>Punishment System</b>\n\n"
                     f"Configure automatic punishment escalation for repeat violators.\n\n"
                     f"<b>Current Window:</b> {window_hours} hours\n"
                     f"<i>Violations older than this are forgotten.</i>",
                reply_markup=create_punishment_menu_keyboard(enabled, window_hours),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error loading punishment config: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Punishment toggle
    if data == CallbackData.PUNISHMENT_TOGGLE:
        try:
            config_data = await read_config()
            if "punishment" not in config_data:
                config_data["punishment"] = {"enabled": True, "window_hours": 72, "steps": []}
            
            current_state = config_data["punishment"].get("enabled", True)
            config_data["punishment"]["enabled"] = not current_state
            
            await write_json_file(config_data)
            
            enabled = not current_state
            window_hours = config_data["punishment"].get("window_hours", 72)
            
            status = "✅ Enabled" if enabled else "❌ Disabled"
            await query.edit_message_text(
                text=f"⚖️ <b>Punishment System</b>\n\n"
                     f"Status changed to: <b>{status}</b>\n\n"
                     f"<b>Current Window:</b> {window_hours} hours",
                reply_markup=create_punishment_menu_keyboard(enabled, window_hours),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Punishment window selections
    if data in [CallbackData.PUNISHMENT_WINDOW_24, CallbackData.PUNISHMENT_WINDOW_48, CallbackData.PUNISHMENT_WINDOW_72]:
        window_map = {
            CallbackData.PUNISHMENT_WINDOW_24: 24,
            CallbackData.PUNISHMENT_WINDOW_48: 48,
            CallbackData.PUNISHMENT_WINDOW_72: 72,
        }
        hours = window_map[data]
        try:
            config_data = await read_config()
            if "punishment" not in config_data:
                config_data["punishment"] = {"enabled": True, "window_hours": hours, "steps": []}
            else:
                config_data["punishment"]["window_hours"] = hours
            
            await write_json_file(config_data)
            
            enabled = config_data["punishment"].get("enabled", True)
            
            await query.edit_message_text(
                text=f"⚖️ <b>Punishment System</b>\n\n"
                     f"✅ Time window set to <b>{hours} hours</b>\n\n"
                     f"Violations older than this will be forgotten.",
                reply_markup=create_punishment_menu_keyboard(enabled, hours),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Punishment view steps
    if data == "punishment_view_steps":
        try:
            from utils.punishment_system import get_punishment_system
            
            config_data = await read_config()
            system = get_punishment_system()
            system.load_config(config_data)
            
            steps_text = []
            for i, step in enumerate(system.steps, 1):
                steps_text.append(f"  {i}. {step.get_display_text()}")
            
            if not steps_text:
                steps_text = ["  No steps configured (using defaults)"]
            
            await query.edit_message_text(
                text=f"⚖️ <b>Punishment Steps</b>\n\n"
                     f"{chr(10).join(steps_text)}\n\n"
                     f"<i>Use /punishment_set_steps to configure custom steps.</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Back to Punishment", callback_data=CallbackData.PUNISHMENT_MENU)],
                ]),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    if data == "punishment_info":
        await query.answer("Toggle the system with the button below", show_alert=False)
        return
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GROUP FILTER CALLBACKS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Group filter menu
    if data == CallbackData.GROUP_FILTER_MENU:
        try:
            config_data = await read_config()
            filter_config = config_data.get("group_filter", {})
            enabled = filter_config.get("enabled", False)
            mode = filter_config.get("mode", "include")
            group_ids = filter_config.get("group_ids", [])
            
            mode_desc = "Only users in specified groups are monitored" if mode == "include" else "Users in specified groups are whitelisted"
            
            await query.edit_message_text(
                text=f"🔍 <b>Group Filter</b>\n\n"
                     f"Filter users based on their panel groups.\n\n"
                     f"<b>Mode:</b> {mode.title()}\n"
                     f"<i>{mode_desc}</i>",
                reply_markup=create_group_filter_menu_keyboard(enabled, mode, group_ids),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error loading group filter config: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Group filter toggle
    if data == CallbackData.GROUP_FILTER_TOGGLE:
        try:
            config_data = await read_config()
            if "group_filter" not in config_data:
                config_data["group_filter"] = {"enabled": True, "mode": "include", "group_ids": []}
            
            current_state = config_data["group_filter"].get("enabled", False)
            config_data["group_filter"]["enabled"] = not current_state
            
            await write_json_file(config_data)
            
            enabled = not current_state
            mode = config_data["group_filter"].get("mode", "include")
            group_ids = config_data["group_filter"].get("group_ids", [])
            
            status = "✅ Enabled" if enabled else "❌ Disabled"
            await query.edit_message_text(
                text=f"🔍 <b>Group Filter</b>\n\n"
                     f"Status changed to: <b>{status}</b>",
                reply_markup=create_group_filter_menu_keyboard(enabled, mode, group_ids),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Group filter mode selections
    if data in [CallbackData.GROUP_FILTER_MODE_INCLUDE, CallbackData.GROUP_FILTER_MODE_EXCLUDE]:
        mode = "include" if data == CallbackData.GROUP_FILTER_MODE_INCLUDE else "exclude"
        try:
            config_data = await read_config()
            if "group_filter" not in config_data:
                config_data["group_filter"] = {"enabled": False, "mode": mode, "group_ids": []}
            else:
                config_data["group_filter"]["mode"] = mode
            
            await write_json_file(config_data)
            
            enabled = config_data["group_filter"].get("enabled", False)
            group_ids = config_data["group_filter"].get("group_ids", [])
            
            mode_desc = "Only users in specified groups are monitored" if mode == "include" else "Users in specified groups are whitelisted"
            
            await query.edit_message_text(
                text=f"🔍 <b>Group Filter</b>\n\n"
                     f"✅ Mode set to: <b>{mode.title()}</b>\n\n"
                     f"<i>{mode_desc}</i>",
                reply_markup=create_group_filter_menu_keyboard(enabled, mode, group_ids),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Group filter view groups
    if data == "group_filter_view_groups":
        try:
            from utils.user_group_filter import get_all_groups
            from utils.types import PanelType
            
            config_data = await read_config()
            filter_config = config_data.get("group_filter", {})
            configured_ids = filter_config.get("group_ids", [])
            
            # Get panel data for group lookup
            panel_config = config_data.get("panel", {})
            panel_data = PanelType(
                panel_config.get("username", ""),
                panel_config.get("password", ""),
                panel_config.get("domain", "")
            )
            
            # Get all groups
            groups = await get_all_groups(panel_data)
            
            groups_text = []
            for group in groups:
                gid = group.get("id", "?")
                name = group.get("name", "Unknown")
                is_configured = "✅" if gid in configured_ids else "⬜"
                groups_text.append(f"  {is_configured} <code>{gid}</code> - {name}")
            
            if not groups_text:
                groups_text = ["  No groups found in panel"]
            
            await query.edit_message_text(
                text=f"🔍 <b>Available Groups</b>\n\n"
                     f"<b>Configured IDs:</b> <code>{configured_ids}</code>\n\n"
                     f"<b>Panel Groups:</b>\n"
                     f"{chr(10).join(groups_text)}\n\n"
                     f"<i>Use /group_filter_add &lt;id&gt; or /group_filter_remove &lt;id&gt;</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Back to Group Filter", callback_data=CallbackData.GROUP_FILTER_MENU)],
                ]),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error fetching groups: {e}\n\n<i>Make sure panel is configured.</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Back to Group Filter", callback_data=CallbackData.GROUP_FILTER_MENU)],
                ]),
                parse_mode="HTML"
            )
        return
    
    if data == "group_filter_info":
        await query.answer("Toggle the filter with the button below", show_alert=False)
        return
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ADMIN FILTER CALLBACKS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Admin filter menu
    if data == CallbackData.ADMIN_FILTER_MENU:
        try:
            config_data = await read_config()
            filter_config = config_data.get("admin_filter", {})
            enabled = filter_config.get("enabled", False)
            mode = filter_config.get("mode", "include")
            admin_usernames = filter_config.get("admin_usernames", [])
            
            mode_desc = "Only users of specified admins are monitored" if mode == "include" else "Users of specified admins are whitelisted"
            
            await query.edit_message_text(
                text=f"👤 <b>Admin Filter</b>\n\n"
                     f"Filter users based on their owner admin.\n\n"
                     f"<b>Mode:</b> {mode.title()}\n"
                     f"<i>{mode_desc}</i>",
                reply_markup=create_admin_filter_menu_keyboard(enabled, mode, admin_usernames),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error loading admin filter config: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Admin filter toggle
    if data == CallbackData.ADMIN_FILTER_TOGGLE:
        try:
            from utils.read_config import save_config_value
            config_data = await read_config()
            filter_config = config_data.get("admin_filter", {})
            current_state = filter_config.get("enabled", False)
            new_state = not current_state
            
            await save_config_value("admin_filter_enabled", "true" if new_state else "false")
            
            # Invalidate cache
            from utils.read_config import invalidate_config_cache
            invalidate_config_cache()
            
            config_data = await read_config()
            filter_config = config_data.get("admin_filter", {})
            enabled = filter_config.get("enabled", False)
            mode = filter_config.get("mode", "include")
            admin_usernames = filter_config.get("admin_usernames", [])
            
            status = "✅ Enabled" if enabled else "❌ Disabled"
            await query.edit_message_text(
                text=f"👤 <b>Admin Filter</b>\n\n"
                     f"Status changed to: <b>{status}</b>",
                reply_markup=create_admin_filter_menu_keyboard(enabled, mode, admin_usernames),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Admin filter mode selections
    if data in [CallbackData.ADMIN_FILTER_MODE_INCLUDE, CallbackData.ADMIN_FILTER_MODE_EXCLUDE]:
        mode = "include" if data == CallbackData.ADMIN_FILTER_MODE_INCLUDE else "exclude"
        try:
            from utils.read_config import save_config_value, invalidate_config_cache
            await save_config_value("admin_filter_mode", mode)
            invalidate_config_cache()
            
            config_data = await read_config()
            filter_config = config_data.get("admin_filter", {})
            enabled = filter_config.get("enabled", False)
            admin_usernames = filter_config.get("admin_usernames", [])
            
            mode_desc = "Only users of specified admins are monitored" if mode == "include" else "Users of specified admins are whitelisted"
            
            await query.edit_message_text(
                text=f"👤 <b>Admin Filter</b>\n\n"
                     f"✅ Mode set to: <b>{mode.title()}</b>\n\n"
                     f"<i>{mode_desc}</i>",
                reply_markup=create_admin_filter_menu_keyboard(enabled, mode, admin_usernames),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Admin filter view admins
    if data == "admin_filter_view_admins":
        try:
            from utils.admin_filter import get_all_admins
            from utils.types import PanelType
            
            config_data = await read_config()
            filter_config = config_data.get("admin_filter", {})
            configured_usernames = filter_config.get("admin_usernames", [])
            
            # Get panel data for admin lookup
            panel_config = config_data.get("panel", {})
            panel_data = PanelType(
                panel_config.get("username", ""),
                panel_config.get("password", ""),
                panel_config.get("domain", "")
            )
            
            # Get all admins
            admins = await get_all_admins(panel_data)
            
            admins_text = []
            for admin in admins:
                username = admin.get("username", "?")
                is_sudo = admin.get("is_sudo", False)
                is_disabled = admin.get("is_disabled", False)
                is_configured = "✅" if username in configured_usernames else "⬜"
                status = ""
                if is_sudo:
                    status += "👑"
                if is_disabled:
                    status += "🔒"
                admins_text.append(f"  {is_configured} <code>{username}</code> {status}")
            
            if not admins_text:
                admins_text = ["  No admins found in panel"]
            
            await query.edit_message_text(
                text=f"👤 <b>Available Admins</b>\n\n"
                     f"<b>Configured:</b> <code>{configured_usernames}</code>\n\n"
                     f"<b>Panel Admins:</b>\n"
                     f"{chr(10).join(admins_text)}\n\n"
                     f"<i>Use /admin_filter_add &lt;username&gt; or /admin_filter_remove &lt;username&gt;</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Back to Admin Filter", callback_data=CallbackData.ADMIN_FILTER_MENU)],
                ]),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error fetching admins: {e}\n\n<i>Make sure panel is configured and you have sudo access.</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Back to Admin Filter", callback_data=CallbackData.ADMIN_FILTER_MENU)],
                ]),
                parse_mode="HTML"
            )
        return
    
    if data == "admin_filter_info":
        await query.answer("Toggle the filter with the button below", show_alert=False)
        return
    
    # Disable method menu
    if data == CallbackData.DISABLE_METHOD_MENU:
        await show_disable_method_menu(query)
        return
    
    # Disable by status
    if data == CallbackData.DISABLE_BY_STATUS:
        try:
            from utils.read_config import save_config_value
            await save_config_value("disable_method", "status")
            await save_config_value("disabled_group_id", "")
            await query.edit_message_text(
                text="✅ <b>Disable Method</b> set to <b>Status</b>\n\n"
                     "Users will be disabled by changing their status to 'disabled'.",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_settings_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Select disabled group (show group list)
    if data == CallbackData.SELECT_DISABLED_GROUP:
        await show_groups_for_disabled_selection(query)
        return
    
    # Handle group selection for disabled users
    if data.startswith("set_disabled_group:"):
        group_id = int(data.split(":", 1)[1])
        await set_disabled_group(query, group_id)
        return
    
    # Set special limit
    if data == CallbackData.SET_SPECIAL_LIMIT:
        context.user_data["waiting_for"] = "special_limit_username"
        await query.edit_message_text(
            text="🎯 <b>Set Special Limit</b>\n\nSend the username (e.g., <code>Test_User</code>):",
            parse_mode="HTML"
        )
        return
    
    # Special limit options (1, 2, custom)
    if data == CallbackData.SPECIAL_LIMIT_1:
        if "selected_user" in context.user_data:
            username = context.user_data["selected_user"]
            out_put = await handel_special_limit(username, 1)
            msg = f"✅ Special limit for <b>{username}</b> set to <b>1 device</b>"
            if out_put[0]:
                msg = f"✅ Updated <b>{username}</b> limit to <b>1 device</b>"
            await query.edit_message_text(
                text=msg,
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
            context.user_data.pop("selected_user", None)
        return
    
    if data == CallbackData.SPECIAL_LIMIT_2:
        if "selected_user" in context.user_data:
            username = context.user_data["selected_user"]
            out_put = await handel_special_limit(username, 2)
            msg = f"✅ Special limit for <b>{username}</b> set to <b>2 devices</b>"
            if out_put[0]:
                msg = f"✅ Updated <b>{username}</b> limit to <b>2 devices</b>"
            await query.edit_message_text(
                text=msg,
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
            context.user_data.pop("selected_user", None)
        return
    
    if data == CallbackData.SPECIAL_LIMIT_CUSTOM:
        context.user_data["waiting_for"] = "special_limit_number"
        await query.edit_message_text(
            text=f"🎯 <b>Custom Limit for {context.user_data.get('selected_user', 'user')}</b>\n\n"
                 + "Send the limit number (e.g., <code>5</code>):",
            parse_mode="HTML"
        )
        return
    
    # Show special limit
    if data == CallbackData.SHOW_SPECIAL_LIMIT:
        out_put = await get_special_limit_list()
        if out_put:
            text = "📋 <b>Special Limits:</b>\n\n" + "\n".join(out_put)
        else:
            text = "📋 No special limits found!"
        await query.edit_message_text(
            text=text,
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # General limit menu
    if data == "general_limit_menu":
        try:
            from utils.read_config import read_config
            config = await read_config()
            current = config.get("limits", {}).get("general", 2)
        except:
            current = 2
        await query.edit_message_text(
            text=f"🔢 <b>General Limit</b>\n\nCurrent: <b>{current}</b>\n\nSelect new limit:",
            reply_markup=create_general_limit_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # General limit selections
    if data in [CallbackData.GENERAL_LIMIT_2, CallbackData.GENERAL_LIMIT_3, CallbackData.GENERAL_LIMIT_4]:
        limit_map = {
            CallbackData.GENERAL_LIMIT_2: 2,
            CallbackData.GENERAL_LIMIT_3: 3,
            CallbackData.GENERAL_LIMIT_4: 4,
        }
        limit = limit_map[data]
        await save_general_limit(limit)
        await query.edit_message_text(
            text=f"✅ General limit set to <b>{limit}</b>",
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    if data == CallbackData.GENERAL_LIMIT_CUSTOM:
        context.user_data["waiting_for"] = "general_limit"
        await query.edit_message_text(
            text="🔢 <b>Custom General Limit</b>\n\nSend the limit number (e.g., <code>5</code>):",
            parse_mode="HTML"
        )
        return
    
    # Show except users
    if data == CallbackData.SHOW_EXCEPT_USERS:
        messages = await show_except_users_handler()
        if messages:
            text = "👥 <b>Except Users:</b>\n\n" + "\n".join(messages)
        else:
            text = "👥 No except users found!"
        await query.edit_message_text(
            text=text,
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Set except user
    if data == CallbackData.SET_EXCEPT_USER:
        context.user_data["waiting_for"] = "except_user"
        await query.edit_message_text(
            text="👥 <b>Add Except User</b>\n\nSend the username to add:",
            parse_mode="HTML"
        )
        return
    
    # Remove except user
    if data == CallbackData.REMOVE_EXCEPT_USER:
        context.user_data["waiting_for"] = "remove_except_user"
        await query.edit_message_text(
            text="👥 <b>Remove Except User</b>\n\nSend the username to remove:",
            parse_mode="HTML"
        )
        return
    
    # Monitoring status
    if data == CallbackData.MONITORING_STATUS:
        try:
            from utils.warning_system import warning_system
            
            if not warning_system.warnings:
                text = "🟢 No users are currently being monitored."
            else:
                active_warnings = []
                for username, warning in warning_system.warnings.items():
                    if warning.is_monitoring_active():
                        remaining = warning.time_remaining()
                        minutes = remaining // 60
                        seconds = remaining % 60
                        active_warnings.append(
                            f"• <code>{username}</code> - {warning.ip_count} IPs - {minutes}m {seconds}s"
                        )
                
                if active_warnings:
                    text = "🔍 <b>Currently Monitoring:</b>\n\n" + "\n".join(active_warnings)
                else:
                    text = "🟢 No active monitoring."
        except Exception as e:
            text = f"❌ Error: {e}"
        
        await query.edit_message_text(
            text=text,
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Monitoring details
    if data == CallbackData.MONITORING_DETAILS:
        try:
            from utils.warning_system import warning_system
            
            if not warning_system.warnings:
                text = "🟢 No users are currently being monitored."
            else:
                message_parts = []
                for username, warning in warning_system.warnings.items():
                    if warning.is_monitoring_active():
                        remaining = warning.time_remaining()
                        minutes = remaining // 60
                        seconds = remaining % 60
                        analysis = await warning_system.analyze_user_activity_patterns(username)
                        
                        user_details = [
                            f"👤 <b>{username}</b>",
                            f"⏰ Time: {minutes}m {seconds}s",
                            f"📊 IPs: {warning.ip_count}",
                            f"📈 Peak: {analysis.get('peak_ip_count', 0)}",
                        ]
                        message_parts.append("\n".join(user_details))
                
                if message_parts:
                    text = "🔍 <b>Monitoring Details:</b>\n\n" + "\n\n".join(message_parts)
                else:
                    text = "🟢 No active monitoring."
        except Exception as e:
            text = f"❌ Error: {e}"
        
        await query.edit_message_text(
            text=text,
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Clear monitoring
    if data == CallbackData.MONITORING_CLEAR:
        try:
            from utils.warning_system import warning_system
            count = len(warning_system.warnings)
            warning_system.warnings.clear()
            await warning_system.save_warnings()
            text = f"✅ Cleared {count} monitoring warnings."
        except Exception as e:
            text = f"❌ Error: {e}"
        
        await query.edit_message_text(
            text=text,
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Reports
    if data == CallbackData.REPORT_CONNECTION:
        await query.edit_message_text(text="⏳ Generating connection report...")
        try:
            report = await generate_connection_report()
            if len(report) > 4000:
                report = report[:3997] + "..."
            await query.edit_message_text(
                text=f"<code>{report}</code>",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        return
    
    if data == CallbackData.REPORT_NODE_USAGE:
        await query.edit_message_text(text="⏳ Generating node usage report...")
        try:
            report = await generate_node_usage_report()
            await query.edit_message_text(
                text=f"<code>{report}</code>",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        return
    
    if data == CallbackData.REPORT_MULTI_DEVICE:
        await query.edit_message_text(text="⏳ Generating multi-device users report...")
        try:
            multi_device_users = await get_multi_device_users()
            if not multi_device_users:
                text = "No multi-device users detected."
            else:
                lines = ["<b>Multi-Device Users:</b>\n"]
                for username, ip_count, node_count, protocols in multi_device_users[:10]:
                    lines.append(f"<code>{username}</code>: {ip_count} IPs, {node_count} nodes")
                text = "\n".join(lines)
            await query.edit_message_text(
                text=text,
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        return
    
    if data == CallbackData.REPORT_IP_12H:
        await query.edit_message_text(text="⏳ Generating 12-hour IP history report...")
        try:
            from utils.ip_history_tracker import ip_history_tracker
            from utils.isp_detector import ISPDetector
            config_data = await read_config()
            api_config = config_data.get("api", {})
            isp_detector = None
            ipinfo_token = api_config.get("ipinfo_token", "")
            use_fallback_api = api_config.get("use_fallback_isp_api", False)
            if ipinfo_token or use_fallback_api:
                isp_detector = ISPDetector(token=ipinfo_token, use_fallback_only=use_fallback_api)
            report = await ip_history_tracker.generate_report(12, config_data, isp_detector)
            if len(report) > 4000:
                report = report[:3997] + "..."
            await query.edit_message_text(
                text=report,
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        return
    
    if data == CallbackData.REPORT_IP_48H:
        await query.edit_message_text(text="⏳ Generating 48-hour IP history report...")
        try:
            from utils.ip_history_tracker import ip_history_tracker
            from utils.isp_detector import ISPDetector
            config_data = await read_config()
            api_config = config_data.get("api", {})
            isp_detector = None
            ipinfo_token = api_config.get("ipinfo_token", "")
            use_fallback_api = api_config.get("use_fallback_isp_api", False)
            if ipinfo_token or use_fallback_api:
                isp_detector = ISPDetector(token=ipinfo_token, use_fallback_only=use_fallback_api)
            report = await ip_history_tracker.generate_report(48, config_data, isp_detector)
            if len(report) > 4000:
                report = report[:3997] + "..."
            await query.edit_message_text(
                text=report,
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error: {e}",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        return
    
    # Admin list
    if data == CallbackData.LIST_ADMINS:
        admins = await check_admin()
        if admins:
            admins_str = "\n• ".join(map(str, admins))
            text = f"👑 <b>Admins:</b>\n\n• {admins_str}"
        else:
            text = "No admins found!"
        await query.edit_message_text(
            text=text,
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Add admin
    if data == CallbackData.ADD_ADMIN:
        if len(await check_admin()) > 5:
            await query.edit_message_text(
                text="❌ You have more than 5 admins. Remove one first.",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
            return
        context.user_data["waiting_for"] = "add_admin"
        await query.edit_message_text(
            text="👑 <b>Add Admin</b>\n\nSend the chat ID of the new admin:",
            parse_mode="HTML"
        )
        return
    
    # Remove admin
    if data == CallbackData.REMOVE_ADMIN:
        context.user_data["waiting_for"] = "remove_admin"
        await query.edit_message_text(
            text="👑 <b>Remove Admin</b>\n\nSend the chat ID of the admin to remove:",
            parse_mode="HTML"
        )
        return
    
    # Backup - redirect to /backup command
    if data == CallbackData.BACKUP:
        await query.edit_message_text(
            text="💾 <b>Backup</b>\n\n"
                 + "Use the /backup command to create a full backup (ZIP format).\n"
                 + "It includes configuration and database files.",
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Restore
    if data == CallbackData.RESTORE:
        context.user_data["waiting_for"] = "restore_file"
        await query.edit_message_text(
            text="📥 <b>Restore Config</b>\n\n"
                 + "⚠️ This will replace your current configuration!\n\n"
                 + "Send the backup file (ZIP or legacy JSON):",
            parse_mode="HTML"
        )
        return
    
    # Create config
    if data == CallbackData.CREATE_CONFIG:
        context.user_data["waiting_for"] = "config_domain"
        await query.edit_message_text(
            text="🔧 <b>Panel Configuration</b>\n\n"
                 + "Send your panel address:\n"
                 + "Example: <code>sub.domain.com:8333</code>\n\n"
                 + "<b>Without</b> https:// or http://",
            parse_mode="HTML"
        )
        return
    
    # Set IPInfo token
    if data == CallbackData.SET_IPINFO:
        context.user_data["waiting_for"] = "ipinfo_token"
        await query.edit_message_text(
            text="🔑 <b>IPInfo Token</b>\n\n"
                 + "Send your ipinfo.io API token:\n\n"
                 + "Get one at: https://ipinfo.io\n\n"
                 + "Or send <code>remove</code> to remove the token",
            parse_mode="HTML"
        )
        return
    
    # User action buttons from check_ip_used messages
    if data.startswith("set_limit:"):
        parts = data.split(":")
        username = parts[1]
        # If device_count is included, we can offer quick set option
        suggested_limit = int(parts[2]) if len(parts) > 2 else None
        
        context.user_data["selected_user"] = username
        context.user_data["waiting_for"] = None
        
        # Create keyboard with suggested limit if available
        if suggested_limit:
            keyboard = [
                [InlineKeyboardButton(f"📱 Set {suggested_limit} devices", callback_data=f"quick_limit:{username}:{suggested_limit}")],
                [
                    InlineKeyboardButton("1️⃣", callback_data=CallbackData.SPECIAL_LIMIT_1),
                    InlineKeyboardButton("2️⃣", callback_data=CallbackData.SPECIAL_LIMIT_2),
                    InlineKeyboardButton("🔢 Custom", callback_data=CallbackData.SPECIAL_LIMIT_CUSTOM),
                ],
                [InlineKeyboardButton("🔙 Cancel", callback_data=CallbackData.BACK_MAIN)],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply_markup = create_special_limit_options_keyboard()
        
        await query.edit_message_text(
            text=f"🎯 <b>Set limit for: {username}</b>\n\nChoose the device limit:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return
    
    # Quick limit setting (from suggested limit button)
    if data.startswith("quick_limit:"):
        parts = data.split(":")
        username = parts[1]
        limit = int(parts[2])
        out_put = await handel_special_limit(username, limit)
        msg = f"✅ Special limit for <b>{username}</b> set to <b>{limit}</b> devices"
        if out_put[0]:
            msg = f"✅ Updated <b>{username}</b> limit to <b>{limit}</b> devices"
        await query.edit_message_text(
            text=msg,
            reply_markup=create_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    if data.startswith("add_except:"):
        username = data.split(":", 1)[1]
        try:
            await add_except_user(username)
            await query.edit_message_text(
                text=f"✅ User <b>{username}</b> added to except list (unlimited devices)",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Error adding {username} to except list: {e}",
                reply_markup=create_back_to_main_keyboard(),
                parse_mode="HTML"
            )
        return
    
    if data.startswith("skip:"):
        username = data.split(":", 1)[1]
        await query.edit_message_text(
            text=f"⏭️ Skipped user <b>{username}</b>",
            parse_mode="HTML"
        )
        return


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for inline keyboard flows."""
    # Check admin privilege
    admins = await check_admin()
    if update.effective_chat.id not in admins:
        return
    
    waiting_for = context.user_data.get("waiting_for")
    if not waiting_for:
        return
    
    text = update.message.text.strip()
    
    # Handle special limit username input
    if waiting_for == "special_limit_username":
        context.user_data["selected_user"] = text
        context.user_data["waiting_for"] = None
        await update.message.reply_html(
            text=f"🎯 <b>Set limit for: {text}</b>\n\nChoose the device limit:",
            reply_markup=create_special_limit_options_keyboard()
        )
        return
    
    # Handle special limit custom number
    if waiting_for == "special_limit_number":
        try:
            limit = int(text)
            username = context.user_data.get("selected_user", "user")
            out_put = await handel_special_limit(username, limit)
            msg = f"✅ Special limit for <b>{username}</b> set to <b>{limit}</b>"
            if out_put[0]:
                msg = f"✅ Updated <b>{username}</b> limit to <b>{limit}</b>"
            await update.message.reply_html(
                text=msg,
                reply_markup=create_back_to_main_keyboard()
            )
            context.user_data.pop("selected_user", None)
            context.user_data["waiting_for"] = None
        except ValueError:
            await update.message.reply_html(
                text="❌ Invalid number. Please send a valid number.",
                reply_markup=create_back_to_main_keyboard()
            )
            context.user_data["waiting_for"] = None
        return
    
    # Handle general limit custom
    if waiting_for == "general_limit":
        try:
            limit = int(text)
            await save_general_limit(limit)
            await update.message.reply_html(
                text=f"✅ General limit set to <b>{limit}</b>",
                reply_markup=create_back_to_main_keyboard()
            )
        except ValueError:
            await update.message.reply_html(
                text="❌ Invalid number.",
                reply_markup=create_back_to_main_keyboard()
            )
        context.user_data["waiting_for"] = None
        return
    
    # Handle check interval custom
    if waiting_for == "check_interval":
        try:
            interval = int(text)
            await save_check_interval(interval)
            await update.message.reply_html(
                text=f"✅ Check interval set to <b>{interval} seconds</b>",
                reply_markup=create_back_to_main_keyboard()
            )
        except ValueError:
            await update.message.reply_html(
                text="❌ Invalid number.",
                reply_markup=create_back_to_main_keyboard()
            )
        context.user_data["waiting_for"] = None
        return
    
    # Handle time to active custom
    if waiting_for == "time_to_active":
        try:
            time_val = int(text)
            await save_time_to_active_users(time_val)
            await update.message.reply_html(
                text=f"✅ Time to active set to <b>{time_val} seconds</b>",
                reply_markup=create_back_to_main_keyboard()
            )
        except ValueError:
            await update.message.reply_html(
                text="❌ Invalid number.",
                reply_markup=create_back_to_main_keyboard()
            )
        context.user_data["waiting_for"] = None
        return
    
    # Handle except user
    if waiting_for == "except_user":
        await add_except_user(text)
        await update.message.reply_html(
            text=f"✅ Except user <b>{text}</b> added!",
            reply_markup=create_back_to_main_keyboard()
        )
        context.user_data["waiting_for"] = None
        return
    
    # Handle remove except user
    if waiting_for == "remove_except_user":
        result = await remove_except_user_from_config(text)
        if result:
            await update.message.reply_html(
                text=f"✅ Except user <b>{text}</b> removed!",
                reply_markup=create_back_to_main_keyboard()
            )
        else:
            await update.message.reply_html(
                text=f"❌ User <b>{text}</b> not found!",
                reply_markup=create_back_to_main_keyboard()
            )
        context.user_data["waiting_for"] = None
        return
    
    # Handle add admin
    if waiting_for == "add_admin":
        try:
            if await add_admin_to_config(text):
                await update.message.reply_html(
                    text=f"✅ Admin <b>{text}</b> added!",
                    reply_markup=create_back_to_main_keyboard()
                )
            else:
                await update.message.reply_html(
                    text=f"❌ Admin <b>{text}</b> already exists!",
                    reply_markup=create_back_to_main_keyboard()
                )
        except:
            await update.message.reply_html(
                text="❌ Invalid chat ID!",
                reply_markup=create_back_to_main_keyboard()
            )
        context.user_data["waiting_for"] = None
        return
    
    # Handle remove admin
    if waiting_for == "remove_admin":
        try:
            admin_id = int(text)
            if await remove_admin_from_config(admin_id):
                await update.message.reply_html(
                    text=f"✅ Admin <b>{admin_id}</b> removed!",
                    reply_markup=create_back_to_main_keyboard()
                )
            else:
                await update.message.reply_html(
                    text=f"❌ Admin <b>{admin_id}</b> not found!",
                    reply_markup=create_back_to_main_keyboard()
                )
        except:
            await update.message.reply_html(
                text="❌ Invalid chat ID!",
                reply_markup=create_back_to_main_keyboard()
            )
        context.user_data["waiting_for"] = None
        return
    
    # Handle config domain
    if waiting_for == "config_domain":
        context.user_data["config_domain"] = text
        context.user_data["waiting_for"] = "config_username"
        await update.message.reply_html(
            text="Send your panel <b>username</b>:",
        )
        return
    
    # Handle config username
    if waiting_for == "config_username":
        context.user_data["config_username"] = text
        context.user_data["waiting_for"] = "config_password"
        await update.message.reply_html(
            text="Send your panel <b>password</b>:",
        )
        return
    
    # Handle config password
    if waiting_for == "config_password":
        context.user_data["config_password"] = text
        context.user_data["waiting_for"] = None
        
        await update.message.reply_html(text="⏳ Checking credentials...")
        
        try:
            await add_base_information(
                context.user_data["config_domain"],
                context.user_data["config_password"],
                context.user_data["config_username"],
            )
            await update.message.reply_html(
                text="✅ Config saved successfully! 🎊",
                reply_markup=create_back_to_main_keyboard()
            )
        except:
            await update.message.reply_html(
                text="❌ There is a problem with your information!\n\n"
                     + f"Domain: <code>{context.user_data['config_domain']}</code>\n"
                     + f"Username: <code>{context.user_data['config_username']}</code>\n\n"
                     + "Please check and try again.",
                reply_markup=create_back_to_main_keyboard()
            )
        return
    
    # Handle IPInfo token
    if waiting_for == "ipinfo_token":
        if text.lower() == "remove":
            await save_ipinfo_token("")
            await update.message.reply_html(
                text="✅ IPInfo token removed!",
                reply_markup=create_back_to_main_keyboard()
            )
        elif len(text) < 10:
            await update.message.reply_html(
                text="❌ Invalid token format!",
                reply_markup=create_back_to_main_keyboard()
            )
        else:
            await save_ipinfo_token(text)
            await update.message.reply_html(
                text="✅ IPInfo token set successfully!",
                reply_markup=create_back_to_main_keyboard()
            )
        context.user_data["waiting_for"] = None
        return


async def document_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads for restore functionality."""
    waiting_for = context.user_data.get("waiting_for")
    if waiting_for != "restore_file":
        return
    
    # Check admin privilege
    admins = await check_admin()
    if update.effective_chat.id not in admins:
        return
    
    try:
        if not update.message.document:
            await update.message.reply_html(
                text="❌ Please send a valid backup file (ZIP or JSON).",
                reply_markup=create_back_to_main_keyboard()
            )
            context.user_data["waiting_for"] = None
            return
        
        file_name = update.message.document.file_name
        
        if file_name.endswith('.zip'):
            # Handle ZIP backup
            file = await update.message.document.get_file()
            file_content = await file.download_as_bytearray()
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "backup.zip")
            
            with open(zip_path, 'wb') as f:
                f.write(file_content)
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Restore data files
            data_src = os.path.join(temp_dir, "data")
            if os.path.exists(data_src):
                data_dst = "data"
                if os.path.exists("/var/lib/pg-limiter/data"):
                    data_dst = "/var/lib/pg-limiter/data"
                
                for item in os.listdir(data_src):
                    src = os.path.join(data_src, item)
                    dst = os.path.join(data_dst, item)
                    if os.path.isfile(src):
                        os.makedirs(data_dst, exist_ok=True)
                        shutil.copy2(src, dst)
            
            shutil.rmtree(temp_dir)
            
            await update.message.reply_html(
                text="✅ <b>Backup restored!</b>\n\n"
                     "⚠️ Please restart the service for changes to take effect.",
                reply_markup=create_back_to_main_keyboard()
            )
            
        elif file_name.endswith('.json'):
            # Handle legacy JSON config - migrate to database
            file = await update.message.document.get_file()
            file_content = await file.download_as_bytearray()
            
            try:
                config_data = json.loads(file_content.decode('utf-8'))
            except json.JSONDecodeError as e:
                await update.message.reply_html(
                    text=f"❌ Invalid JSON format: {e}",
                    reply_markup=create_back_to_main_keyboard()
                )
                context.user_data["waiting_for"] = None
                return
            
            # Migrate to database
            from utils.read_config import save_config_value
            from db import get_db, UserLimitCRUD, ExceptUserCRUD
            
            async with get_db() as db:
                # Import settings
                if "disable_method" in config_data:
                    await save_config_value("disable_method", config_data["disable_method"])
                if "disabled_group_id" in config_data and config_data["disabled_group_id"]:
                    await save_config_value("disabled_group_id", str(config_data["disabled_group_id"]))
                if config_data.get("enhanced_details") is not None:
                    await save_config_value("enhanced_details", str(config_data["enhanced_details"]).lower())
                
                # Import special limits
                special_limits = config_data.get("limits", {}).get("special", {})
                for username, limit in special_limits.items():
                    await UserLimitCRUD.set(db, username, limit)
                
                # Import except users
                except_users = config_data.get("except_users", [])
                for username in except_users:
                    await ExceptUserCRUD.add(db, username, "Restored from backup")
            
            await update.message.reply_html(
                text="✅ <b>Legacy config imported to database!</b>\n\n"
                     "📝 <b>Note:</b> Panel credentials should be set in .env file.\n"
                     "⚠️ Restart the service for changes to take effect.",
                reply_markup=create_back_to_main_keyboard()
            )
        else:
            await update.message.reply_html(
                text="❌ Please send a ZIP or JSON file.",
                reply_markup=create_back_to_main_keyboard()
            )
            context.user_data["waiting_for"] = None
            return
        
    except Exception as e:
        await update.message.reply_html(
            text=f"❌ Error: {e}",
            reply_markup=create_back_to_main_keyboard()
        )
    
    context.user_data["waiting_for"] = None


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CallbackQueryHandler(callback_query_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
application.add_handler(MessageHandler(filters.Document.ALL, document_message_handler))

# Keep command handlers for backward compatibility
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("create_config", create_config)],
        states={
            GET_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_confirmation)],
            GET_DOMAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_domain)],
            GET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            GET_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("set_special_limit", set_special_limit)],
        states={
            GET_SPECIAL_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_special_limit)],
            GET_LIMIT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_limit_number)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("set_time_to_active_users", get_time_to_active_users)],
        states={
            GET_TIME_TO_ACTIVE_USERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time_to_active_users_handler)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("set_check_interval", get_check_interval)],
        states={
            GET_CHECK_INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_check_interval_handler)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("set_general_limit_number", get_general_limit_number)],
        states={
            GET_GENERAL_LIMIT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_general_limit_number_handler)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("remove_except_user", remove_except_user)],
        states={
            REMOVE_EXCEPT_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_except_user_handler)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("country_code", set_country_code)],
        states={
            SET_COUNTRY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, write_country_code)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("set_except_user", set_except_users)],
        states={
            SET_EXCEPT_USERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_except_users_handler)],
        },
        fallbacks=[],
    )
)
application.add_handler(CommandHandler("show_special_limit", show_special_limit_function))
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("add_admin", add_admin)],
        states={
            GET_CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id)],
        },
        fallbacks=[],
    )
)
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("remove_admin", remove_admin)],
        states={
            GET_CHAT_ID_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id_to_remove)],
        },
        fallbacks=[],
    )
)
application.add_handler(CommandHandler("backup", send_backup))
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("restore", restore_config)],
        states={
            RESTORE_CONFIG: [MessageHandler(filters.Document.ALL, restore_config_handler)],
        },
        fallbacks=[],
    )
)
application.add_handler(CommandHandler("admins_list", admins_list))
application.add_handler(CommandHandler("show_except_users", show_except_users))
application.add_handler(CommandHandler("monitoring_status", monitoring_status))
application.add_handler(CommandHandler("monitoring_details", monitoring_details))
application.add_handler(CommandHandler("clear_monitoring", clear_monitoring))

# Punishment system commands
application.add_handler(CommandHandler("punishment_status", punishment_status))
application.add_handler(CommandHandler("punishment_toggle", punishment_toggle))
application.add_handler(CommandHandler("punishment_set_window", punishment_set_window))
application.add_handler(CommandHandler("punishment_set_steps", punishment_set_steps))
application.add_handler(CommandHandler("user_violations", user_violations))
application.add_handler(CommandHandler("clear_user_violations", clear_user_violations))

# Group filter commands
application.add_handler(CommandHandler("group_filter_status", group_filter_status))
application.add_handler(CommandHandler("group_filter_toggle", group_filter_toggle))
application.add_handler(CommandHandler("group_filter_mode", group_filter_mode))
application.add_handler(CommandHandler("group_filter_set", group_filter_set))
application.add_handler(CommandHandler("group_filter_add", group_filter_add))
application.add_handler(CommandHandler("group_filter_remove", group_filter_remove))

# Admin filter commands
application.add_handler(CommandHandler("admin_filter_status", admin_filter_status))
application.add_handler(CommandHandler("admin_filter_toggle", admin_filter_toggle))
application.add_handler(CommandHandler("admin_filter_mode", admin_filter_mode))
application.add_handler(CommandHandler("admin_filter_set", admin_filter_set))
application.add_handler(CommandHandler("admin_filter_add", admin_filter_add))
application.add_handler(CommandHandler("admin_filter_remove", admin_filter_remove))

application.add_handler(CommandHandler("connection_report", connection_report_command))
application.add_handler(CommandHandler("node_usage", node_usage_report_command))
application.add_handler(CommandHandler("multi_device_users", multi_device_users_command))
application.add_handler(CommandHandler("users_by_node", users_by_node_command))
application.add_handler(CommandHandler("users_by_protocol", users_by_protocol_command))
application.add_handler(CommandHandler("ip_history_12h", ip_history_12h_command))
application.add_handler(CommandHandler("ip_history_48h", ip_history_48h_command))
application.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("set_ipinfo_token", set_ipinfo_token)],
        states={
            SET_IPINFO_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_ipinfo_token_handler)],
        },
        fallbacks=[],
    )
)
application.add_handler(CommandHandler("show_enhanced_details", show_enhanced_details_command))

# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
import sys
import time
from datetime import datetime, timezone
from typing import Optional
from aiogram import Bot

from config import Settings
from utils.logging import get_logger

logger = get_logger("event_logger")

class EventLoggerService:
    def __init__(self, settings: Settings, bot: Optional[Bot] = None):
        self.settings = settings
        self.bot = bot
        self._last_ram_alert: float = 0.0

    def set_bot(self, bot: Bot) -> None:
        self.bot = bot

    async def log_event(self, text: str, parse_mode: str = "HTML") -> None:
        if not self.bot or not self.settings.LOGGER_GROUP_ID:
            return
        try:
            await self.bot.send_message(
                chat_id=self.settings.LOGGER_GROUP_ID,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
        except Exception as exc:
            logger.warning("Failed to send notification to logger group: %s", exc)

    async def notify_bot_started(self, bot_username: str, version: int, total_files: int) -> None:
        text = (
            f"🚀 <b>Bot System Started!</b>\n\n"
            f"• <b>Master Bot:</b> @{bot_username}\n"
            f"• <b>Skin (BOT_TYPE):</b> <code>{self.settings.BOT_TYPE}</code>\n"
            f"• <b>Platform OS:</b> <code>{sys.platform}</code>\n"
            f"• <b>Manifest Version:</b> v{version}\n"
            f"• <b>Indexed Files:</b> {total_files}\n"
            f"• <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        await self.log_event(text)

    async def notify_serious_error(
        self, error_type: str, details: str, user_id: Optional[int] = None
    ) -> None:
        user_line = f"\n• <b>User ID:</b> <code>{user_id}</code>" if user_id else ""
        clean_details = details.replace("<", "&lt;").replace(">", "&gt;")[:1500]
        text = (
            f"🚨 <b>CRITICAL / SERIOUS ERROR DETECTED!</b>\n\n"
            f"• <b>Error Type:</b> <code>{error_type}</code>{user_line}\n"
            f"• <b>Details:</b>\n<pre>{clean_details}</pre>\n"
            f"• <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        await self.log_event(text)

    async def notify_new_user(
        self, user_id: int, full_name: str, username: Optional[str] = None
    ) -> None:
        uname_line = f"@{username}" if username else "<i>None</i>"
        clean_name = full_name.replace("<", "&lt;").replace(">", "&gt;")
        text = (
            f"👤 <b>New User Started The Bot!</b>\n\n"
            f"• <b>User ID:</b> <code>{user_id}</code>\n"
            f"• <b>Name:</b> {clean_name}\n"
            f"• <b>Username:</b> {uname_line}\n"
            f"• <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        await self.log_event(text)

    async def notify_high_ram(self, ram_mb: float, threshold_mb: float = 4096.0) -> None:
        now = time.monotonic()
        if now - self._last_ram_alert < 1800.0:
            return
        self._last_ram_alert = now
        text = (
            f"⚠️ <b>HIGH RAM USAGE ALERT!</b>\n\n"
            f"• <b>Current RAM:</b> <code>{ram_mb:.1f} MB</code> ({ram_mb / 1024.0:.2f} GB)\n"
            f"• <b>Threshold:</b> <code>{threshold_mb:.0f} MB</code> (4.0 GB)\n"
            f"• <b>Status:</b> Bot process is operating under high memory load\n"
            f"• <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        await self.log_event(text)

    async def notify_spammer_blocked(
        self, user_id: int, full_name: str, username: Optional[str], msg_count: int
    ) -> None:
        uname_line = f"@{username}" if username else "<i>None</i>"
        clean_name = full_name.replace("<", "&lt;").replace(">", "&gt;")
        text = (
            f"🚨 <b>User Auto-Blocked For Spamming!</b>\n\n"
            f"• <b>User ID:</b> <code>{user_id}</code>\n"
            f"• <b>Name:</b> {clean_name}\n"
            f"• <b>Username:</b> {uname_line}\n"
            f"• <b>Violation:</b> Sent {msg_count} messages in 10 seconds\n"
            f"• <b>Action:</b> Permanently blocked from bot\n"
            f"• <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        await self.log_event(text)

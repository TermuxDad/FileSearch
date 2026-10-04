# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
import time
import asyncio
from typing import Callable, Dict, Any, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Settings
from database.users import UserRepository
from database.blocked_users import BlockedUserRepository
from database.settings import SystemSettingsRepository
from keyboards.inline import get_maintenance_keyboard
from lang.manager import tr
from services.event_logger import EventLoggerService
from utils.logging import get_logger

logger = get_logger("middlewares.user_access")

class UserAccessMiddleware(BaseMiddleware):
    def __init__(
        self,
        settings: Settings,
        user_repo: UserRepository,
        blocked_repo: BlockedUserRepository,
        system_settings_repo: Optional[SystemSettingsRepository] = None,
        event_logger: Optional[EventLoggerService] = None,
    ):
        super().__init__()
        self.settings = settings
        self.user_repo = user_repo
        self.blocked_repo = blocked_repo
        self.system_settings_repo = system_settings_repo
        self.event_logger = event_logger
        self._synced_users: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user or user.is_bot:
            return await handler(event, data)

        lang = "en"
        data["lang"] = lang

        if await self.blocked_repo.is_blocked(user.id):
            if user.id not in self.blocked_repo.warned_blocks:
                self.blocked_repo.warned_blocks.add(user.id)
                if isinstance(event, Message):
                    await event.answer(tr("user_blocked", lang), parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer(tr("user_blocked", lang), show_alert=True)
            return None

        if self.system_settings_repo and self.system_settings_repo.is_maintenance_mode:
            if not self.settings.is_owner(user.id):
                support_url = self.settings.SUPPORT_GROUP_URL or self.settings.BACKUP_CHANNEL_URL or "https://t.me/social_bots"
                kb = get_maintenance_keyboard(support_url=support_url, lang=lang)
                if isinstance(event, Message):
                    await event.answer(
                        tr("maintenance_notice", lang),
                        reply_markup=kb,
                        parse_mode="HTML",
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(tr("maintenance_alert", lang), show_alert=True)
                return None

        if isinstance(event, Message) and event.chat.type in ("group", "supergroup", "channel"):
            if not self.settings.is_owner(user.id) and event.chat.id not in (self.settings.FILES_GROUP_ID, self.settings.LOGGER_GROUP_ID):
                bot_user = self.settings.MASTER_BOT_USERNAME or "bot"
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=tr("btn_open_pm", lang),
                                url=f"https://t.me/{bot_user}?start=group",
                            )
                        ]
                    ]
                )
                await event.reply(
                    tr("group_restricted", lang),
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                return None

        now = time.time()
        if now - self._synced_users.get(user.id, 0.0) > 900.0:
            self._synced_users[user.id] = now
            asyncio.create_task(
                self._safe_upsert_user(user.id, user.first_name, user.username, lang)
            )

        return await handler(event, data)

    async def _safe_upsert_user(
        self, user_id: int, first_name: str, username: Optional[str], lang: str
    ) -> None:
        try:
            is_new = await self.user_repo.upsert_user(
                user_id=user_id,
                first_name=first_name,
                username=username,
                lang=lang,
            )
            if is_new and self.event_logger:
                await self.event_logger.notify_new_user(
                    user_id=user_id,
                    full_name=first_name,
                    username=username,
                )
        except Exception as exc:
            logger.error("Background user upsert failed for %d: %s", user_id, exc)

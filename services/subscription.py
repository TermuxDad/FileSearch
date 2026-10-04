# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
import asyncio
from typing import List, Tuple, Optional, Union, Dict, Any
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Settings
from lang.manager import tr
from services.cache_manager import TTLCache
from utils.logging import get_logger

logger = get_logger("subscription")


class SubscriptionService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._cache: TTLCache[bool] = TTLCache(maxsize=10000, default_ttl=300.0)
        self._semaphore = asyncio.Semaphore(5)
        self._channels: List[Dict[str, Any]] = [
            {"channel": ch, "invite_link": self.settings.SUBSCRIBE_INVITE_LINKS.get(str(ch))}
            for ch in self.settings.SUBSCRIBE
        ]

    def is_cached_subscribed(self, user_id: int) -> bool:
        return bool(self._cache.get(f"sub:{user_id}"))

    def mark_subscribed(self, user_id: int, ttl: float = 300.0) -> None:
        self._cache.set(f"sub:{user_id}", True, ttl=ttl)

    def clear_cache(self, user_id: Optional[int] = None) -> None:
        if user_id is not None:
            self._cache.delete(f"sub:{user_id}")
        else:
            self._cache = TTLCache(maxsize=10000, default_ttl=300.0)

    def get_channels(self) -> List[Dict[str, Any]]:
        return list(self._channels)

    async def get_missing_channels(
        self, bot: Bot, user_id: int, ignore_cache: bool = False
    ) -> List[Tuple[Union[str, int], str]]:
        if not self._channels:
            return []

        if not ignore_cache and self.is_cached_subscribed(user_id):
            return []

        missing: List[Tuple[Union[str, int], str]] = []

        async def check_channel(entry: Dict[str, Any]) -> Optional[Tuple[Union[str, int], str]]:
            channel = entry.get("channel")
            if not channel:
                return None
            async with self._semaphore:
                try:
                    member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
                    status = member.status
                    is_member = False
                    if status in ("creator", "administrator", "member"):
                        is_member = True
                    elif status == "restricted" and getattr(member, "is_member", False):
                        is_member = True

                    if not is_member:
                        invite_link = entry.get("invite_link") or await self._resolve_channel_url(bot, channel)
                        return (channel, invite_link)
                    return None
                except TelegramBadRequest as exc:
                    logger.warning("Could not check channel %s: %s", channel, exc)
                    invite_link = entry.get("invite_link") or await self._resolve_channel_url(bot, channel)
                    return (channel, invite_link)
                except TelegramForbiddenError as exc:
                    logger.error("Bot forbidden from checking channel %s: %s", channel, exc)
                    invite_link = entry.get("invite_link") or await self._resolve_channel_url(bot, channel)
                    return (channel, invite_link)
                except Exception as exc:
                    logger.exception("Error checking membership for channel %s: %s", channel, exc)
                    invite_link = entry.get("invite_link") or await self._resolve_channel_url(bot, channel)
                    return (channel, invite_link)

        tasks = [check_channel(entry) for entry in self._channels]
        results = await asyncio.gather(*tasks)

        for res in results:
            if res is not None:
                missing.append(res)

        if not missing:
            self.mark_subscribed(user_id)
        else:
            self.clear_cache(user_id)

        return missing

    async def _resolve_channel_url(self, bot: Bot, channel: Union[str, int]) -> str:
        if isinstance(channel, str) and channel.startswith("@"):
            return f"https://t.me/{channel[1:]}"

        ch_str = str(channel)
        if ch_str in self.settings.SUBSCRIBE_INVITE_LINKS:
            return self.settings.SUBSCRIBE_INVITE_LINKS[ch_str]

        try:
            chat = await bot.get_chat(channel)
            if chat.invite_link:
                return chat.invite_link
            link = await bot.create_chat_invite_link(chat_id=channel)
            return link.invite_link
        except Exception:
            return f"https://t.me/c/{str(channel).replace('-100', '')}"

    def build_subscription_keyboard(
        self, missing: List[Tuple[Union[str, int], str]], lang: str = "en"
    ) -> InlineKeyboardMarkup:
        buttons: List[List[InlineKeyboardButton]] = []

        for idx, (channel, url) in enumerate(missing, start=1):
            name = channel if isinstance(channel, str) and channel.startswith("@") else f"Channel {idx}"
            btn_text = f"{tr('btn_join_channel', lang)} ({name})"
            buttons.append([InlineKeyboardButton(text=btn_text, url=url)])

        buttons.append([InlineKeyboardButton(text=tr("btn_confirm_sub", lang), callback_data="confirm_sub")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

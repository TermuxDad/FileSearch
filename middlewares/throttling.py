# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import asyncio
import time
from typing import Callable, Dict, Any, Awaitable, Optional, List
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from config import Settings
from database.blocked_users import BlockedUserRepository
from services.cache_manager import TTLCache
from services.event_logger import EventLoggerService
from utils.exceptions import RateLimitExceededError
from utils.logging import get_logger

logger = get_logger("middlewares.throttling")

class TokenBucket:
    __slots__ = ("tokens", "last_update", "rate", "burst")

    def __init__(self, rate: float, burst: int):
        self.tokens: float = float(burst)
        self.last_update: float = time.monotonic()
        self.rate: float = rate
        self.burst: int = burst

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_update
        self.last_update = now

        self.tokens = min(float(self.burst), self.tokens + (elapsed / self.rate))

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

class ThrottlingMiddleware(BaseMiddleware):

    def __init__(
        self,
        settings: Settings,
        blocked_repo: Optional[BlockedUserRepository] = None,
        event_logger: Optional[EventLoggerService] = None,
    ):
        super().__init__()
        self.settings = settings
        self.blocked_repo = blocked_repo
        self.event_logger = event_logger
        self.rate = settings.RATE_LIMIT_RATE
        self.burst = settings.RATE_LIMIT_BURST

        self._buckets: TTLCache[TokenBucket] = TTLCache(maxsize=10000, default_ttl=3600.0)
        self._user_messages: Dict[int, List[float]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user or user.is_bot:
            return await handler(event, data)

        now = time.monotonic()
        recent = [t for t in self._user_messages.get(user.id, []) if now - t <= 10.0]
        recent.append(now)
        self._user_messages[user.id] = recent

        if len(recent) >= 10 and not self.settings.is_owner(user.id):
            logger.warning("Spam detected from user %d (%d msgs in 10s). Blocking.", user.id, len(recent))
            if self.blocked_repo:
                await self.blocked_repo.block_user(
                    user_id=user.id,
                    blocked_by=0,
                    reason=f"Auto-ban: sent {len(recent)} messages in 10s",
                )
                self.blocked_repo.warned_blocks.add(user.id)

            if self.event_logger:
                asyncio.create_task(
                    self.event_logger.notify_spammer_blocked(
                        user_id=user.id,
                        full_name=user.full_name,
                        username=user.username,
                        msg_count=len(recent),
                    )
                )

            if isinstance(event, Message):
                await event.answer(
                    "⛔ <b>Access Denied / You Have Been Blocked!</b>\n\n"
                    "You were automatically blocked for spamming (sending 10+ messages in 10 seconds).\n"
                    "This incident has been logged and reported to the administrators.",
                    parse_mode="HTML",
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Blocked for spamming!", show_alert=True)
            return None

        bucket = self._buckets.get(str(user.id))
        if bucket is None:
            bucket = TokenBucket(rate=self.rate, burst=self.burst)
            self._buckets.set(str(user.id), bucket)

        if not bucket.consume():
            logger.warning("Rate limit exceeded for user %d", user.id)
            if isinstance(event, Message):
                await event.answer("⚠️ You are sending requests too quickly. Please slow down.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Too fast! Please slow down.", show_alert=False)
            return None

        return await handler(event, data)

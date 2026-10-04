# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery

from config import Settings
from services.subscription import SubscriptionService
from utils.logging import get_logger

logger = get_logger("middlewares.subscription")

class ForceSubscriptionMiddleware(BaseMiddleware):

    def __init__(self, settings: Settings, subscription_service: SubscriptionService):
        super().__init__()
        self.settings = settings
        self.subscription_service = subscription_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        bot: Optional[Bot] = data.get("bot")

        if not user or user.is_bot or not bot or not self.settings.SUBSCRIBE:
            return await handler(event, data)

        if self.settings.is_owner(user.id):
            return await handler(event, data)

        if isinstance(event, Message):

            if event.chat.type != "private":
                return await handler(event, data)

            text = event.text or ""
            if text.startswith("/start"):
                return await handler(event, data)

        elif isinstance(event, CallbackQuery):
            if event.data in ("confirm_sub", "noop"):
                return await handler(event, data)

        missing = await self.subscription_service.get_missing_channels(bot, user.id)
        if missing:
            keyboard = self.subscription_service.build_subscription_keyboard(missing)
            prompt = (
                "📢 <b>Subscription Required</b>\n\n"
                "To search and access files, you must join our official channels below.\n"
                "Once joined, click the <b>Confirm Joining</b> button to proceed!"
            )
            if isinstance(event, Message):
                await event.answer(prompt, reply_markup=keyboard, parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Please join the required channels first!", show_alert=True)
                if event.message:
                    await event.message.answer(prompt, reply_markup=keyboard, parse_mode="HTML")
            return None

        return await handler(event, data)

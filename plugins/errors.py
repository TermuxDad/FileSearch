# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import asyncio
import traceback
from typing import Optional
from aiogram import Router
from aiogram.types import ErrorEvent
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramNetworkError,
)
from services.event_logger import EventLoggerService
from utils.exceptions import AppError
from utils.logging import get_logger

logger = get_logger("errors")

async def global_error_handler(
    event: ErrorEvent, event_logger: Optional[EventLoggerService] = None
) -> bool:
    exception = event.exception
    update = event.update

    if isinstance(exception, TelegramRetryAfter):
        logger.warning("Telegram flood limit triggered. Retry after %.1fs", exception.retry_after)
        return True

    if isinstance(exception, TelegramForbiddenError):
        logger.warning("Telegram forbidden (user blocked bot or kick): %s", exception)
        return True

    if isinstance(exception, TelegramBadRequest):

        if "message is not modified" in str(exception).lower():
            return True
        logger.warning("Telegram bad request: %s", exception)
        return True

    if isinstance(exception, TelegramNetworkError):
        logger.warning("Telegram network error encountered: %s", exception)
        return True

    if isinstance(exception, AppError):
        logger.warning("Application error handled: %s", exception.message)
        if update.message:
            try:
                await update.message.answer(f"⚠️ {exception.user_facing}")
            except Exception:
                pass
        elif update.callback_query:
            try:
                await update.callback_query.answer(f"⚠️ {exception.user_facing}", show_alert=True)
            except Exception:
                pass
        return True

    logger.exception("Unhandled exception processing update %s: %s", update.update_id, exception)

    user_id = None
    if update.message and update.message.from_user:
        user_id = update.message.from_user.id
    elif update.callback_query and update.callback_query.from_user:
        user_id = update.callback_query.from_user.id

    if event_logger:
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        asyncio.create_task(
            event_logger.notify_serious_error(
                error_type=type(exception).__name__,
                details=f"{exception}\n\nTraceback:\n{tb}",
                user_id=user_id,
            )
        )

    if update.message:
        try:
            await update.message.answer(
                "❌ An unexpected internal error occurred. Our engineers have been alerted."
            )
        except Exception:
            pass
    elif update.callback_query:
        try:
            await update.callback_query.answer(
                "❌ An unexpected error occurred. Please try again later.",
                show_alert=True,
            )
        except Exception:
            pass

    return True

def create_errors_router(name: str = "errors_router") -> Router:
    r = Router(name=name)
    r.errors.register(global_error_handler)
    return r

router = create_errors_router("default_errors_router")

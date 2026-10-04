# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from typing import Optional
from config import Settings
from database.users import UserRepository
from database.blocked_users import BlockedUserRepository
from database.settings import SystemSettingsRepository
from services.event_logger import EventLoggerService
from middlewares.throttling import ThrottlingMiddleware
from middlewares.user_access import UserAccessMiddleware
from plugins.file_delivery import router as file_delivery_router
from plugins.errors import create_errors_router

def create_delivery_dispatcher(
    settings: Settings,
    user_repo: UserRepository,
    blocked_repo: BlockedUserRepository,
    system_settings_repo: Optional[SystemSettingsRepository] = None,
    event_logger: Optional[EventLoggerService] = None,
) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(ThrottlingMiddleware(settings, blocked_repo=blocked_repo, event_logger=event_logger))
    dp.callback_query.middleware(ThrottlingMiddleware(settings, blocked_repo=blocked_repo, event_logger=event_logger))

    dp.message.middleware(UserAccessMiddleware(settings, user_repo, blocked_repo, system_settings_repo, event_logger))
    dp.callback_query.middleware(UserAccessMiddleware(settings, user_repo, blocked_repo, system_settings_repo, event_logger))

    dp.include_router(create_errors_router("delivery_errors_router"))
    dp.include_router(file_delivery_router)

    return dp

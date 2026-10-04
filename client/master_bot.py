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
from middlewares.subscription import ForceSubscriptionMiddleware
from plugins.start import router as start_router
from plugins.help import router as help_router
from plugins.search import router as search_router
from plugins.request import router as request_router
from plugins.force_sub import router as force_sub_router
from plugins.block import router as block_router
from plugins.stats import router as stats_router
from plugins.scan import router as scan_router
from plugins.admin import router as admin_router
from plugins.callbacks import router as callbacks_router
from plugins.errors import create_errors_router
from services.subscription import SubscriptionService

def create_master_dispatcher(
    settings: Settings,
    user_repo: UserRepository,
    blocked_repo: BlockedUserRepository,
    subscription_service: SubscriptionService,
    system_settings_repo: Optional[SystemSettingsRepository] = None,
    event_logger: Optional[EventLoggerService] = None,
) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(ThrottlingMiddleware(settings, blocked_repo=blocked_repo, event_logger=event_logger))
    dp.callback_query.middleware(ThrottlingMiddleware(settings, blocked_repo=blocked_repo, event_logger=event_logger))

    dp.message.middleware(UserAccessMiddleware(settings, user_repo, blocked_repo, system_settings_repo, event_logger))
    dp.callback_query.middleware(UserAccessMiddleware(settings, user_repo, blocked_repo, system_settings_repo, event_logger))

    dp.message.middleware(ForceSubscriptionMiddleware(settings, subscription_service))
    dp.callback_query.middleware(ForceSubscriptionMiddleware(settings, subscription_service))

    dp.include_router(create_errors_router("master_errors_router"))
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(force_sub_router)
    dp.include_router(callbacks_router)
    dp.include_router(request_router)
    dp.include_router(block_router)
    dp.include_router(stats_router)
    dp.include_router(scan_router)
    dp.include_router(admin_router)
    dp.include_router(search_router)

    return dp

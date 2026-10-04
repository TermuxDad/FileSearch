# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import time
import asyncio
from typing import Optional, Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
import aiohttp
from aiohttp import TCPConnector, ThreadedResolver
from aiogram.client.session.aiohttp import AiohttpSession

from config import Settings
from client.mongodb import MongoDB
from client.master_bot import create_master_dispatcher
from client.delivery_bot import create_delivery_dispatcher
from database import (
    ensure_indexes,
    UserRepository,
    BlockedUserRepository,
    RequestRepository,
    StatisticsRepository,
    ManifestRepository,
    TokenRegistryRepository,
    SystemSettingsRepository,
)
from keyboards.pagination import PaginationManager
from lang.manager import load_skin
from services import (
    SearchEngine,
    FileTokenService,
    ManifestManager,
    SubscriptionService,
    StatisticsManager,
    RequestManager,
    FileDeliveryService,
    EventLoggerService,
)
from services.scanner import ScannerService
from utils.logging import get_logger

logger = get_logger("client.bots")

class ReliableAiohttpSession(AiohttpSession):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._connector_init["resolver"] = ThreadedResolver()

class BotEcosystem:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.start_time: float = time.time()

        self.mongodb = MongoDB(settings)

        self.user_repo: Optional[UserRepository] = None
        self.blocked_repo: Optional[BlockedUserRepository] = None
        self.request_repo: Optional[RequestRepository] = None
        self.stats_repo: Optional[StatisticsRepository] = None
        self.manifest_repo: Optional[ManifestRepository] = None
        self.token_repo: Optional[TokenRegistryRepository] = None
        self.system_settings_repo: Optional[SystemSettingsRepository] = None

        self.search_engine: Optional[SearchEngine] = None
        self.manifest_manager: Optional[ManifestManager] = None
        self.token_service: Optional[FileTokenService] = None
        self.file_delivery_service: Optional[FileDeliveryService] = None
        self.subscription_service: Optional[SubscriptionService] = None
        self.stats_manager: Optional[StatisticsManager] = None
        self.pagination_manager: Optional[PaginationManager] = None
        self.scanner_service: Optional[ScannerService] = None

        self.master_bot: Optional[Bot] = None
        self.delivery_bot: Optional[Bot] = None
        self.master_dp: Optional[Dispatcher] = None
        self.delivery_dp: Optional[Dispatcher] = None
        self.event_logger: Optional[EventLoggerService] = None
        self._monitor_task: Optional[asyncio.Task] = None

        self._initialized: bool = False
        self._polling_tasks: list[asyncio.Task] = []

    async def initialize(self) -> None:
        if self._initialized:
            return

        logger.info("Initializing Bot Ecosystem...")

        await self.mongodb.connect()
        db = self.mongodb.db

        self.user_repo = UserRepository(db)
        self.blocked_repo = BlockedUserRepository(db)
        await self.blocked_repo.load_cache()
        self.request_repo = RequestRepository(db)
        self.stats_repo = StatisticsRepository(db)
        self.manifest_repo = ManifestRepository(db)
        self.token_repo = TokenRegistryRepository(db)
        self.system_settings_repo = SystemSettingsRepository(db)
        await self.system_settings_repo.load()

        await ensure_indexes(db)

        self.search_engine = SearchEngine(
            cache_size=self.settings.SEARCH_CACHE_SIZE,
            strict_and=self.settings.SEARCH_STRICT_AND,
            fuzzy_enabled=self.settings.SEARCH_FUZZY_ENABLED,
            fuzzy_threshold=self.settings.SEARCH_FUZZY_THRESHOLD,
        )
        self.manifest_manager = ManifestManager(
            settings=self.settings,
            manifest_repo=self.manifest_repo,
            search_engine=self.search_engine,
        )
        self.token_service = FileTokenService(
            token_repo=self.token_repo,
            default_ttl=self.settings.TOKEN_EXPIRY_SECONDS,
        )
        self.subscription_service = SubscriptionService(self.settings)

        self.stats_manager = StatisticsManager(self.stats_repo)
        await self.stats_manager.start()

        self.file_delivery_service = FileDeliveryService(
            token_service=self.token_service,
            search_engine=self.search_engine,
            user_repo=self.user_repo,
            blocked_repo=self.blocked_repo,
            stats_manager=self.stats_manager,
            auto_delete_seconds=self.settings.AUTO_DELETE_FILE_SECONDS,
        )
        self.pagination_manager = PaginationManager(
            settings=self.settings,
            token_service=self.token_service,
        )
        self.request_manager = RequestManager(
            settings=self.settings,
            request_repo=self.request_repo,
        )
        self.scanner_service = ScannerService(
            settings=self.settings,
            manifest_manager=self.manifest_manager,
        )

        load_skin(self.settings.BOT_TYPE)

        default_props = DefaultBotProperties(parse_mode=ParseMode.HTML)
        self.master_bot = Bot(
            token=self.settings.MASTER_BOT_TOKEN,
            session=ReliableAiohttpSession(),
            default=default_props,
        )
        self.event_logger = EventLoggerService(self.settings, self.master_bot)

        try:
            master_me = await self.master_bot.get_me()
            self.settings.MASTER_BOT_USERNAME = master_me.username or self.settings.MASTER_BOT_USERNAME
            logger.info("Discovered Master Bot username: @%s", self.settings.MASTER_BOT_USERNAME)
        except Exception as exc:
            logger.warning("Could not auto-fetch Master Bot username: %s", exc)

        if self.settings.is_dual_bot:
            self.delivery_bot = Bot(
                token=self.settings.DELIVERY_BOT_TOKEN,
                session=ReliableAiohttpSession(),
                default=default_props,
            )
            try:
                delivery_me = await self.delivery_bot.get_me()
                self.settings.DELIVERY_BOT_USERNAME = delivery_me.username or self.settings.DELIVERY_BOT_USERNAME
                logger.info("Discovered Delivery Bot username: @%s", self.settings.DELIVERY_BOT_USERNAME)
            except Exception as exc:
                logger.warning("Could not auto-fetch Delivery Bot username: %s", exc)
        else:
            logger.info("Single-bot mode active: Master Bot handles search and file delivery directly.")
            self.delivery_bot = self.master_bot
            self.settings.DELIVERY_BOT_USERNAME = self.settings.MASTER_BOT_USERNAME

        try:
            await self.manifest_manager.initialize_and_load(self.master_bot)
        except Exception as exc:
            logger.warning("Initial manifest recovery non-fatal warning: %s", exc)

        self.master_dp = create_master_dispatcher(
            settings=self.settings,
            user_repo=self.user_repo,
            blocked_repo=self.blocked_repo,
            subscription_service=self.subscription_service,
            system_settings_repo=self.system_settings_repo,
            event_logger=self.event_logger,
        )
        if self.settings.is_dual_bot:
            self.delivery_dp = create_delivery_dispatcher(
                settings=self.settings,
                user_repo=self.user_repo,
                blocked_repo=self.blocked_repo,
                system_settings_repo=self.system_settings_repo,
                event_logger=self.event_logger,
            )
        else:
            self.delivery_dp = None

        shared_workflow_data = {
            "ecosystem": self,
            "settings": self.settings,
            "mongodb": self.mongodb,
            "user_repo": self.user_repo,
            "blocked_repo": self.blocked_repo,
            "system_settings_repo": self.system_settings_repo,
            "event_logger": self.event_logger,
            "request_repo": self.request_repo,
            "stats_repo": self.stats_repo,
            "statistics_repo": self.stats_repo,
            "manifest_repo": self.manifest_repo,
            "token_repo": self.token_repo,
            "search_engine": self.search_engine,
            "manifest_manager": self.manifest_manager,
            "token_service": self.token_service,
            "file_delivery_service": self.file_delivery_service,
            "subscription_service": self.subscription_service,
            "stats_manager": self.stats_manager,
            "statistics_manager": self.stats_manager,
            "pagination_manager": self.pagination_manager,
            "request_manager": self.request_manager,
            "scanner_service": self.scanner_service,
            "master_bot": self.master_bot,
            "delivery_bot": self.delivery_bot,
            "start_time": self.start_time,
        }

        self.master_dp.workflow_data.update(shared_workflow_data)
        if self.settings.is_dual_bot and self.delivery_dp:
            self.delivery_dp.workflow_data.update(shared_workflow_data)

        self._initialized = True
        logger.info("Bot Ecosystem initialization complete")

    async def register_commands(self) -> None:
        if not self.master_bot or not self.delivery_bot:
            return

        user_commands = [
            BotCommand(command="start", description="Restart bot or open welcome screen"),
            BotCommand(command="help", description="Show search and request guide"),
            BotCommand(command="request", description="Request an unlisted file"),
            BotCommand(command="cancel", description="Cancel active operation"),
        ]

        owner_commands = [
            BotCommand(command="start", description="Restart bot or open welcome screen"),
            BotCommand(command="help", description="Show search and full admin guide"),
            BotCommand(command="stats", description="System hardware & telemetry"),
            BotCommand(command="scan", description="Scan messages in group/channel for files"),
            BotCommand(command="maintain", description="Toggle maintenance mode on/off"),
            BotCommand(command="restart", description="Restart bot process"),
            BotCommand(command="blocked", description="List blocked users"),
            BotCommand(command="request", description="Request an unlisted file"),
            BotCommand(command="cancel", description="Cancel active operation"),
        ]

        delivery_commands = [
            BotCommand(command="start", description="Retrieve file via delivery link"),
        ]

        try:
            await self.master_bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
            for owner_id in self.settings.OWNER_IDS:
                try:
                    await self.master_bot.set_my_commands(
                        owner_commands,
                        scope=BotCommandScopeChat(chat_id=owner_id),
                    )
                except Exception as exc:
                    logger.debug("Could not register scoped owner commands for %d: %s", owner_id, exc)

            if self.settings.is_dual_bot and self.delivery_bot:
                await self.delivery_bot.set_my_commands(delivery_commands, scope=BotCommandScopeDefault())

            logger.info("Telegram bot menu commands registered (User + Owner scopes)")
        except Exception as exc:
            logger.warning("Could not register bot menu commands: %s", exc)

    async def start_polling(self) -> None:
        if not self._initialized:
            await self.initialize()

        await self.register_commands()
        await self.master_bot.delete_webhook(drop_pending_updates=False)

        task_master = asyncio.create_task(
            self.master_dp.start_polling(self.master_bot, handle_signals=False),
            name="master_bot_polling",
        )
        self._polling_tasks = [task_master]

        if self.settings.is_dual_bot and self.delivery_bot and self.delivery_dp:
            logger.info("Starting dual-bot polling: Master Bot + Delivery Bot")
            await self.delivery_bot.delete_webhook(drop_pending_updates=False)
            task_delivery = asyncio.create_task(
                self.delivery_dp.start_polling(self.delivery_bot, handle_signals=False),
                name="delivery_bot_polling",
            )
            self._polling_tasks.append(task_delivery)
        else:
            logger.info("Starting single-bot polling: Master Bot handles all operations")

        if self.event_logger:
            asyncio.create_task(
                self.event_logger.notify_bot_started(
                    bot_username=self.settings.MASTER_BOT_USERNAME,
                    version=self.manifest_manager.version,
                    total_files=self.manifest_manager.files_count,
                )
            )

        self._monitor_task = asyncio.create_task(self._monitor_ram_load(), name="ram_monitor_task")

        await asyncio.gather(*self._polling_tasks)

    async def _monitor_ram_load(self) -> None:
        import psutil
        proc = psutil.Process()
        while True:
            try:
                await asyncio.sleep(30.0)
                rss_mb = proc.memory_info().rss / (1024.0 * 1024.0)
                if rss_mb > 4096.0 and self.event_logger:
                    await self.event_logger.notify_high_ram(ram_mb=rss_mb, threshold_mb=4096.0)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("RAM monitor check error: %s", exc)

    async def shutdown(self) -> None:
        logger.info("Shutting down Bot Ecosystem...")

        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()

        for task in self._polling_tasks:
            if not task.done():
                task.cancel()

        if self.master_dp:
            try:
                await self.master_dp.stop_polling()
            except RuntimeError:
                pass
        if self.settings.is_dual_bot and self.delivery_dp:
            try:
                await self.delivery_dp.stop_polling()
            except RuntimeError:
                pass

        if self.manifest_manager and self.manifest_manager.is_dirty:
            logger.info("Flushing uncommitted manifest changes before shutdown...")
            try:
                await self.manifest_manager.flush_manifest(self.master_bot)
            except Exception as exc:
                logger.warning("Could not flush manifest on shutdown: %s", exc)

        if self.stats_manager:
            await self.stats_manager.stop()

        if self.master_bot and self.master_bot.session:
            await self.master_bot.session.close()
        if self.settings.is_dual_bot and self.delivery_bot and self.delivery_bot.session:
            await self.delivery_bot.session.close()
        await asyncio.sleep(0.25)

        await self.mongodb.close()

        self._initialized = False
        logger.info("Bot Ecosystem successfully shut down")

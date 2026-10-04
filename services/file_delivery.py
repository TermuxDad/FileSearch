# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
import asyncio
from typing import Tuple, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest

from database.users import UserRepository
from database.blocked_users import BlockedUserRepository
from lang.manager import tr
from services.file_tokens import FileTokenService
from services.search_engine import SearchEngine, IndexedFile
from services.statistics_manager import StatisticsManager
from utils.exceptions import TokenError, UserBlockedError
from utils.logging import get_logger

logger = get_logger("services.file_delivery")

class FileDeliveryService:
    def __init__(
        self,
        token_service: FileTokenService,
        search_engine: SearchEngine,
        user_repo: UserRepository,
        blocked_repo: BlockedUserRepository,
        stats_manager: StatisticsManager,
        auto_delete_seconds: int = 300,
    ):
        self.token_service = token_service
        self.search_engine = search_engine
        self.user_repo = user_repo
        self.blocked_repo = blocked_repo
        self.stats_manager = stats_manager
        self.auto_delete_seconds = auto_delete_seconds

    async def deliver_file_by_token(
        self,
        bot: Bot,
        user_id: int,
        token: str,
        lang: str = "en",
    ) -> Tuple[bool, str]:
        if await self.blocked_repo.is_blocked(user_id):
            raise UserBlockedError()

        try:
            file_id = await self.token_service.resolve_token(token)
        except TokenError as exc:
            return False, exc.user_facing

        file_record = self.search_engine.get_file(file_id)
        if not file_record:
            return False, tr("delivery_file_missing", lang)

        delivered = await self._send_media(bot, user_id, file_record, lang=lang)

        if delivered:
            self.stats_manager.record_delivery_success()
            await self.user_repo.increment_files_received(user_id)
            return True, "Success"
        else:
            self.stats_manager.record_delivery_failure()
            return False, tr("internal_error", lang)

    async def _send_media(self, bot: Bot, user_id: int, file_record: IndexedFile, lang: str = "en") -> bool:
        tg_file_id = file_record.delivery_file_id or file_record.master_file_id
        base_caption = file_record.caption or ""
        file_type = (file_record.file_type or "document").lower()

        delete_notice = tr("delivery_delete_notice", lang)
        caption = f"{base_caption}{delete_notice}"
        if len(caption) > 1024:
            cutoff = 1020 - len(delete_notice)
            caption = f"{base_caption[:cutoff]}...{delete_notice}"

        for attempt in range(2):
            try:
                sent_msg = None
                if tg_file_id:
                    if file_type == "video":
                        sent_msg = await bot.send_video(chat_id=user_id, video=tg_file_id, caption=caption, parse_mode="HTML")
                    elif file_type == "animation":
                        sent_msg = await bot.send_animation(chat_id=user_id, animation=tg_file_id, caption=caption, parse_mode="HTML")
                    else:
                        sent_msg = await bot.send_document(chat_id=user_id, document=tg_file_id, caption=caption, parse_mode="HTML")

                elif file_record.source_chat_id and file_record.source_message_id:
                    sent_msg = await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=file_record.source_chat_id,
                        message_id=file_record.source_message_id,
                        caption=caption,
                        parse_mode="HTML",
                    )

                if sent_msg:
                    msg_id = getattr(sent_msg, "message_id", None)
                    if msg_id:
                        asyncio.create_task(
                            self._schedule_message_deletion(bot=bot, chat_id=user_id, message_id=msg_id, delay=self.auto_delete_seconds),
                            name=f"del_file_{user_id}_{msg_id}",
                        )
                    return True

                return False

            except TelegramRetryAfter as exc:
                if attempt == 0:
                    await asyncio.sleep(min(exc.retry_after, 5.0))
                    continue
                return False
            except TelegramForbiddenError:
                return False
            except TelegramBadRequest:
                if attempt == 0 and file_record.source_chat_id and file_record.source_message_id:
                    tg_file_id = None
                    continue
                return False
            except Exception as exc:
                logger.exception("Unexpected error delivering file %s to %d: %s", file_record.id, user_id, exc)
                return False

        return False

    async def _schedule_message_deletion(
        self, bot: Bot, chat_id: int, message_id: int, delay: int = 300
    ) -> None:
        try:
            await asyncio.sleep(delay)
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass

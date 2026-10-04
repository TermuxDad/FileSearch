# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Optional, Dict, Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import Settings
from services.manifest_manager import ManifestManager
from utils.logging import get_logger

logger = get_logger("services.scanner")

class ScanSession:

    def __init__(
        self,
        session_id: str,
        chat_id: int,
        start_id: int,
        end_id: int,
        status_message: Message,
    ):
        self.session_id = session_id
        self.chat_id = chat_id
        self.start_id = start_id
        self.end_id = end_id
        self.current_id = start_id
        self.files_found = 0
        self.files_since_last_edit = 0
        self.checked_in_batch = 0
        self.is_paused = False
        self.is_stopped = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.status = "running"
        self.status_message = status_message
        self.started_at = time.time()
        self.last_edit_time = time.monotonic()
        self.task: Optional[asyncio.Task] = None

    def get_keyboard(self, finished: bool = False) -> Optional[InlineKeyboardMarkup]:
        if finished or self.is_stopped or self.status in ("completed", "stopped", "error"):
            return None

        if self.is_paused:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="▶ Resume",
                            callback_data=f"scan:resume:{self.session_id}",
                        ),
                        InlineKeyboardButton(
                            text="⏹ Stop",
                            callback_data=f"scan:stop:{self.session_id}",
                        ),
                    ]
                ]
            )
        elif self.status == "resting":
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⏹ Stop",
                            callback_data=f"scan:stop:{self.session_id}",
                        ),
                    ]
                ]
            )
        else:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⏸ Pause",
                            callback_data=f"scan:pause:{self.session_id}",
                        ),
                        InlineKeyboardButton(
                            text="⏹ Stop",
                            callback_data=f"scan:stop:{self.session_id}",
                        ),
                    ]
                ]
            )

    def get_progress_text(self, note: str = "") -> str:
        total = max(1, self.end_id - self.start_id + 1)
        checked = max(0, min(total, self.current_id - self.start_id + 1))
        pct = (checked / total) * 100

        status_text = {
            "running": "⚡ Scanning",
            "paused": "⏸ Paused",
            "resting": "☕ Resting (2m Cooldown)",
            "stopped": "⏹ Stopped",
            "completed": "✅ Completed",
        }.get(self.status, self.status)

        lines = [
            "🔍 <b>Chat File Scanner</b>",
            "",
            f"📊 <b>Progress:</b> <code>{checked}</code> / <code>{total}</code> msgs ({pct:.1f}%)",
            f"📁 <b>Files Saved:</b> <code>{self.files_found}</code>",
            f"📍 <b>Current Msg ID:</b> <code>{self.current_id}</code>",
            f"⚡ <b>Status:</b> {status_text}",
        ]
        if note:
            lines.append(f"\n<i>{note}</i>")
        return "\n".join(lines)

    async def update_progress_message(
        self, bot: Bot, note: str = "", finished: bool = False
    ) -> None:
        if not self.status_message:
            return

        text = self.get_progress_text(note=note)
        kb = self.get_keyboard(finished=finished)

        try:
            await bot.edit_message_text(
                chat_id=self.status_message.chat.id,
                message_id=self.status_message.message_id,
                text=text,
                reply_markup=kb,
                parse_mode="HTML",
            )
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                await bot.edit_message_text(
                    chat_id=self.status_message.chat.id,
                    message_id=self.status_message.message_id,
                    text=text,
                    reply_markup=kb,
                    parse_mode="HTML",
                )
            except Exception:
                pass
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                logger.debug("Non-fatal: could not edit scan message: %s", exc)
        except Exception as exc:
            logger.debug("Non-fatal: error updating scan progress message: %s", exc)

    def pause(self) -> None:
        self.is_paused = True
        self.pause_event.clear()
        self.status = "paused"

    def resume(self) -> None:
        self.is_paused = False
        self.pause_event.set()
        self.status = "running"

    def stop(self) -> None:
        self.is_stopped = True
        self.pause_event.set()
        self.status = "stopped"

class ScannerService:

    def __init__(self, settings: Settings, manifest_manager: ManifestManager):
        self.settings = settings
        self.manifest_manager = manifest_manager
        self.active_sessions: Dict[int, ScanSession] = {}
        self.sessions_by_id: Dict[str, ScanSession] = {}

    def get_active_session(self, chat_id: int) -> Optional[ScanSession]:
        return self.active_sessions.get(chat_id)

    def get_session_by_id(self, session_id: str) -> Optional[ScanSession]:
        return self.sessions_by_id.get(session_id)

    async def start_scan(
        self,
        master_bot: Bot,
        delivery_bot: Bot,
        chat_id: int,
        start_id: int,
        end_id: int,
        status_message: Message,
        session_id: Optional[str] = None,
    ) -> ScanSession:
        sid = session_id or uuid.uuid4().hex[:8]
        start_clean = max(1, abs(start_id))
        end_clean = max(1, abs(end_id))
        actual_start = min(start_clean, end_clean)
        actual_end = max(start_clean, end_clean)
        session = ScanSession(
            session_id=sid,
            chat_id=chat_id,
            start_id=actual_start,
            end_id=actual_end,
            status_message=status_message,
        )

        self.active_sessions[chat_id] = session
        self.sessions_by_id[sid] = session

        task = asyncio.create_task(
            self._run_scan_loop(master_bot, delivery_bot, session),
            name=f"scan_{chat_id}_{sid}",
        )
        session.task = task
        return session

    async def _run_scan_loop(
        self,
        master_bot: Bot,
        delivery_bot: Bot,
        session: ScanSession,
    ) -> None:
        logger.info(
            "Starting scan for chat %d range %d-%d using Delivery Bot",
            session.chat_id,
            session.start_id,
            session.end_id,
        )

        try:
            for msg_id in range(session.start_id, session.end_id + 1):
                session.current_id = msg_id

                if session.is_stopped:
                    break

                if session.is_paused:
                    await session.pause_event.wait()
                    if session.is_stopped:
                        break

                session.checked_in_batch += 1
                if session.checked_in_batch >= 180:
                    session.status = "resting"
                    await session.update_progress_message(
                        master_bot,
                        note="⏸ Cooldown: Checked 180 messages. Resting for 2 minutes to protect bot...",
                    )
                    for _ in range(120):
                        if session.is_stopped:
                            break
                        while session.is_paused:
                            await session.pause_event.wait()
                            if session.is_stopped:
                                break
                        await asyncio.sleep(1)

                    if session.is_stopped:
                        break

                    session.checked_in_batch = 0
                    session.status = "running"
                    await session.update_progress_message(
                        master_bot,
                        note="▶ Cooldown ended. Resuming message scan...",
                    )

                fwd = None
                try:
                    fwd = await delivery_bot.forward_message(
                        chat_id=self.settings.LOGGER_GROUP_ID,
                        from_chat_id=session.chat_id,
                        message_id=msg_id,
                    )
                except TelegramRetryAfter as exc:
                    logger.warning("Telegram FloodWait on msg %d: waiting %ds", msg_id, exc.retry_after)
                    await session.update_progress_message(
                        master_bot,
                        note=f"⏳ FloodWait: Pausing {exc.retry_after}s for Telegram...",
                    )
                    await asyncio.sleep(exc.retry_after + 1)
                    try:
                        fwd = await delivery_bot.forward_message(
                            chat_id=self.settings.LOGGER_GROUP_ID,
                            from_chat_id=session.chat_id,
                            message_id=msg_id,
                        )
                    except Exception:
                        fwd = None
                except TelegramBadRequest as exc:
                    if "chat not found" in str(exc).lower() or "bot is not a member" in str(exc).lower():
                        try:
                            fwd = await master_bot.forward_message(
                                chat_id=self.settings.LOGGER_GROUP_ID,
                                from_chat_id=session.chat_id,
                                message_id=msg_id,
                            )
                        except Exception:
                            fwd = None
                    else:
                        fwd = None
                except Exception as exc:
                    logger.debug("Exception forwarding message %d: %s", msg_id, exc)
                    fwd = None

                if fwd:
                    media = None
                    file_type = "document"

                    if fwd.document:
                        media = fwd.document
                        file_type = "document"
                    elif fwd.video:
                        media = fwd.video
                        file_type = "video"
                    elif fwd.audio:
                        media = fwd.audio
                        file_type = "audio"
                    elif fwd.animation:
                        media = fwd.animation
                        file_type = "animation"

                    if media:
                        file_name = getattr(media, "file_name", None) or getattr(media, "title", None)
                        caption = fwd.caption or file_name or f"file_{msg_id}"
                        file_size = getattr(media, "file_size", None)
                        mime_type = getattr(media, "mime_type", None)

                        await self.manifest_manager.ingest_file(
                            bot=master_bot,
                            caption=caption,
                            file_type=file_type,
                            file_id=media.file_id,
                            file_name=file_name,
                            file_size=file_size,
                            mime_type=mime_type,
                            source_chat_id=session.chat_id,
                            source_message_id=msg_id,
                            delivery_file_id=media.file_id,
                            debounce=True,
                        )
                        session.files_found += 1
                        session.files_since_last_edit += 1

                    try:
                        active_del_bot = delivery_bot if fwd.from_user and fwd.from_user.id == delivery_bot.id else master_bot
                        await active_del_bot.delete_message(
                            chat_id=self.settings.LOGGER_GROUP_ID,
                            message_id=fwd.message_id,
                        )
                    except Exception:
                        pass

                now = time.monotonic()
                time_since_edit = now - session.last_edit_time
                msgs_from_start = msg_id - session.start_id + 1

                if (msgs_from_start % 10 == 0 or session.files_since_last_edit >= 5 or time_since_edit >= 3.0) and time_since_edit >= 1.5:
                    session.last_edit_time = now
                    session.files_since_last_edit = 0
                    await session.update_progress_message(master_bot)

                await asyncio.sleep(0.05)

        except Exception as exc:
            logger.exception("Unexpected error in scan loop: %s", exc)
            session.status = "error"
            await session.update_progress_message(
                master_bot, note=f"❌ Error occurred: {exc}", finished=True
            )
        finally:
            if session.is_stopped:
                session.status = "stopped"
                finish_note = f"⏹ Stopped by owner. Saved {session.files_found} files."
            elif session.status != "error":
                session.status = "completed"
                finish_note = f"✅ Completed! Saved {session.files_found} files."
            else:
                finish_note = "❌ Terminated with error."

            await session.update_progress_message(
                master_bot, note=finish_note, finished=True
            )

            if session.files_found > 0:
                try:
                    logger.info("Scan completed with %d files. Flushing manifest...", session.files_found)
                    await self.manifest_manager.flush_manifest(master_bot, force=True)
                except Exception as exc:
                    logger.exception("Failed to flush manifest after scan: %s", exc)

            self.active_sessions.pop(session.chat_id, None)
            self.sessions_by_id.pop(session.session_id, None)

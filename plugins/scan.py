# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import re
import uuid
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Settings
from services.scanner import ScannerService
from utils.logging import get_logger

logger = get_logger("plugins.scan")

router = Router(name="scan_router")

SCAN_RANGE_PATTERN = re.compile(r"^/scan(?:@\w+)?\s+(-?\d+)(?:(?:\s*[-:]\s*|\s+to\s+|\s+)(-?\d+))?$", re.IGNORECASE)

@router.message(Command("scan"))
async def on_scan_command(
    message: Message,
    bot: Bot,
    settings: Settings,
    scanner_service: ScannerService,
    delivery_bot: Optional[Bot] = None,
) -> None:
    user = message.from_user
    if not user or not settings.is_owner(user.id):
        return

    if message.chat.type == "private":
        await message.answer(
            "⚠️ <b>Chat Restriction</b>\n\n"
            "The <code>/scan</code> command can only be used in <b>groups</b> and <b>channels</b> where files are stored, not in private chat.",
            parse_mode="HTML",
        )
        return

    text = (message.text or "").strip()
    match = SCAN_RANGE_PATTERN.match(text)
    if not match:
        await message.answer(
            "⚠️ <b>Invalid Command Format</b>\n\n"
            "<b>Usage:</b> <code>/scan &lt;start_id&gt;-&lt;end_id&gt;</code>\n"
            "<i>Example:</i> <code>/scan 1-2000</code>\n\n"
            "<i>All controls (Pause, Resume, Stop) are handled via inline buttons on the live progress message.</i>",
            parse_mode="HTML",
        )
        return

    val1 = max(1, abs(int(match.group(1))))
    val2 = max(1, abs(int(match.group(2)))) if match.group(2) else 1
    start_id, end_id = min(val1, val2), max(val1, val2)

    active_session = scanner_service.get_active_session(message.chat.id)
    if active_session and not active_session.is_stopped:
        await message.answer(
            f"⚠️ A scan is already running in this chat (Range: <code>{active_session.start_id}-{active_session.end_id}</code>).\n"
            f"Use the buttons on the progress message to pause or stop it.",
            parse_mode="HTML",
        )
        return

    fetch_bot = delivery_bot or bot
    session_id = uuid.uuid4().hex[:8]
    total_msgs = end_id - start_id + 1

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏸ Pause",
                    callback_data=f"scan:pause:{session_id}",
                ),
                InlineKeyboardButton(
                    text="⏹ Stop",
                    callback_data=f"scan:stop:{session_id}",
                ),
            ]
        ]
    )

    initial_msg = await message.answer(
        "🔍 <b>Chat File Scanner</b>\n\n"
        f"📊 <b>Progress:</b> <code>0</code> / <code>{total_msgs}</code> msgs (0.0%)\n"
        f"📁 <b>Files Saved:</b> <code>0</code>\n"
        f"📍 <b>Current Msg ID:</b> <code>{start_id}</code>\n"
        "⚡ <b>Status:</b> <i>Starting scan...</i>",
        reply_markup=kb,
        parse_mode="HTML",
    )

    await scanner_service.start_scan(
        master_bot=bot,
        delivery_bot=fetch_bot,
        chat_id=message.chat.id,
        start_id=start_id,
        end_id=end_id,
        status_message=initial_msg,
        session_id=session_id,
    )

@router.callback_query(F.data.startswith("scan:pause:"))
async def on_scan_pause_callback(
    query: CallbackQuery,
    bot: Bot,
    settings: Settings,
    scanner_service: ScannerService,
) -> None:
    user = query.from_user
    if not user or not settings.is_owner(user.id):
        await query.answer("Unauthorized: Owner only.", show_alert=True)
        return

    session_id = query.data.split(":")[2]
    session = scanner_service.get_session_by_id(session_id)
    if not session or session.is_stopped:
        await query.answer("This scan session has ended or does not exist.", show_alert=True)
        return

    session.pause()
    await session.update_progress_message(bot, note="⏸ Paused by owner.")
    await query.answer("Scan paused.")

@router.callback_query(F.data.startswith("scan:resume:"))
async def on_scan_resume_callback(
    query: CallbackQuery,
    bot: Bot,
    settings: Settings,
    scanner_service: ScannerService,
) -> None:
    user = query.from_user
    if not user or not settings.is_owner(user.id):
        await query.answer("Unauthorized: Owner only.", show_alert=True)
        return

    session_id = query.data.split(":")[2]
    session = scanner_service.get_session_by_id(session_id)
    if not session or session.is_stopped:
        await query.answer("This scan session has ended or does not exist.", show_alert=True)
        return

    session.resume()
    await session.update_progress_message(bot, note="▶ Resumed by owner.")
    await query.answer("Scan resumed.")

@router.callback_query(F.data.startswith("scan:stop:"))
async def on_scan_stop_callback(
    query: CallbackQuery,
    bot: Bot,
    settings: Settings,
    scanner_service: ScannerService,
) -> None:
    user = query.from_user
    if not user or not settings.is_owner(user.id):
        await query.answer("Unauthorized: Owner only.", show_alert=True)
        return

    session_id = query.data.split(":")[2]
    session = scanner_service.get_session_by_id(session_id)
    if not session or session.is_stopped:
        await query.answer("This scan session has ended or does not exist.", show_alert=True)
        return

    session.stop()
    await session.update_progress_message(bot, note="⏹ Stopped by owner.", finished=True)
    await query.answer("Scan stopped.")

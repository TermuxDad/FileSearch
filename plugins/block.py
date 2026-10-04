# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import math
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery

from config import Settings
from database.blocked_users import BlockedUserRepository
from database.users import UserRepository
from keyboards.inline import get_blocked_users_keyboard
from utils.formatting import escape_html
from utils.validators import is_valid_telegram_id
from utils.logging import get_logger

logger = get_logger("plugins.block")

router = Router(name="block_router")

@router.message(Command("block"))
async def on_block_command(
    message: Message,
    command: CommandObject,
    settings: Settings,
    blocked_repo: BlockedUserRepository,
) -> None:
    user = message.from_user
    if not user or not settings.is_owner(user.id):
        return

    raw_args = (command.args or "").strip().split(maxsplit=1)
    target_id: Optional[int] = None
    reason: Optional[str] = None

    if raw_args and is_valid_telegram_id(raw_args[0]):
        target_id = int(raw_args[0])
        if len(raw_args) > 1:
            reason = raw_args[1]
    elif message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        if command.args:
            reason = command.args.strip()

    if not target_id:
        await message.answer("⚠️ Usage: <code>/block &lt;user_id&gt; [reason]</code> (or reply to a message)", parse_mode="HTML")
        return

    if settings.is_owner(target_id):
        await message.answer("⛔ Configured bot owners cannot be blocked.")
        return

    is_new = await blocked_repo.block_user(
        user_id=target_id,
        blocked_by=user.id,
        reason=reason,
    )

    if is_new:
        await message.answer(f"✅ User <code>{target_id}</code> has been blocked.", parse_mode="HTML")
    else:
        await message.answer(f"ℹ️ User <code>{target_id}</code> was already blocked (updated record).", parse_mode="HTML")

@router.message(Command("unblock"))
async def on_unblock_command(
    message: Message,
    command: CommandObject,
    settings: Settings,
    blocked_repo: BlockedUserRepository,
) -> None:
    user = message.from_user
    if not user or not settings.is_owner(user.id):
        return

    args = (command.args or "").strip()
    target_id: Optional[int] = None

    if is_valid_telegram_id(args):
        target_id = int(args)
    elif message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id

    if not target_id:
        await message.answer("⚠️ Usage: <code>/unblock &lt;user_id&gt;</code> (or reply to a message)", parse_mode="HTML")
        return

    was_blocked = await blocked_repo.unblock_user(target_id)
    if was_blocked:
        await message.answer(f"✅ User <code>{target_id}</code> has been unblocked.", parse_mode="HTML")
    else:
        await message.answer(f"ℹ️ User <code>{target_id}</code> was not in the blocked list.", parse_mode="HTML")

@router.message(Command("blocked"))
async def on_list_blocked_command(
    message: Message,
    settings: Settings,
    blocked_repo: BlockedUserRepository,
) -> None:
    user = message.from_user
    if not user or not settings.is_owner(user.id):
        return

    items, total = await blocked_repo.get_blocked_page(page=1, page_size=10)
    if not items:
        await message.answer("ℹ️ There are currently no blocked users.")
        return

    total_pages = max(1, math.ceil(total / 10))
    text = _format_blocked_page(items, page=1, total_pages=total_pages, total=total)
    keyboard = get_blocked_users_keyboard(page=1, total_pages=total_pages)

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("blk_pg:"))
async def on_blocked_page_callback(
    callback: CallbackQuery,
    settings: Settings,
    blocked_repo: BlockedUserRepository,
) -> None:
    user = callback.from_user
    if not user or not settings.is_owner(user.id):
        await callback.answer("⛔ Owner command only.", show_alert=True)
        return

    parts = (callback.data or "").split(":")
    if len(parts) != 2:
        return

    try:
        page = int(parts[1])
    except ValueError:
        return

    items, total = await blocked_repo.get_blocked_page(page=page, page_size=10)
    total_pages = max(1, math.ceil(total / 10))

    if page < 1 or page > total_pages:
        await callback.answer()
        return

    text = _format_blocked_page(items, page=page, total_pages=total_pages, total=total)
    keyboard = get_blocked_users_keyboard(page=page, total_pages=total_pages)

    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass
    await callback.answer()

def _format_blocked_page(items: list, page: int, total_pages: int, total: int) -> str:
    lines = [f"🚫 <b>Blocked Users ({total} total - Page {page}/{total_pages}):</b>\n"]
    for doc in items:
        uid = doc.get("_id")
        dt = doc.get("blocked_at")
        dt_str = dt.strftime("%Y-%m-%d %H:%M") if hasattr(dt, "strftime") else "N/A"
        reason = escape_html(doc.get("reason") or "No reason specified")
        lines.append(f"• <code>{uid}</code> (<i>{dt_str}</i>) - {reason}")
    return "\n".join(lines)

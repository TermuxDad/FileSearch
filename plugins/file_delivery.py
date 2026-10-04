# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

from config import Settings
from keyboards.inline import get_redirect_to_master_keyboard
from lang.manager import tr
from services.file_delivery import FileDeliveryService
from utils.exceptions import UserBlockedError
from utils.formatting import escape_html
from utils.logging import get_logger

logger = get_logger("plugins.file_delivery")

router = Router(name="file_delivery_router")

@router.message(CommandStart())
async def on_delivery_start_command(
    message: Message,
    command: CommandObject,
    bot: Bot,
    settings: Settings,
    file_delivery_service: FileDeliveryService,
    lang: str = "en",
) -> None:
    user = message.from_user
    if not user:
        return

    token = command.args
    first_name = escape_html(user.first_name)

    if token:
        token = token.strip()
        try:
            success, msg = await file_delivery_service.deliver_file_by_token(
                bot=bot,
                user_id=user.id,
                token=token,
                lang=lang,
            )
            if not success:
                await message.answer(
                    f"⚠️ {msg}",
                    reply_markup=get_redirect_to_master_keyboard(settings.MASTER_BOT_USERNAME, lang=lang),
                    parse_mode="HTML",
                )
        except UserBlockedError:
            await message.answer(tr("user_blocked", lang), parse_mode="HTML")
        except Exception as exc:
            logger.exception("Unexpected error processing token %s: %s", token[:8], exc)
            await message.answer(
                tr("internal_error", lang),
                reply_markup=get_redirect_to_master_keyboard(settings.MASTER_BOT_USERNAME, lang=lang),
            )
        return

    welcome_text = (
        f"👋 Hello <b>{first_name}</b>!\n\n"
        f"I am the <b>File Delivery Agent</b> for @{settings.MASTER_BOT_USERNAME}.\n\n"
        "⚡ <i>My role is to securely send requested files to your chat when you click a result link.</i>\n\n"
        "To search our extensive file collection, please visit the <b>Master Bot</b> below:"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_redirect_to_master_keyboard(settings.MASTER_BOT_USERNAME, lang=lang),
        parse_mode="HTML",
    )

@router.message(F.chat.type == "private")
async def on_delivery_plain_text(message: Message, settings: Settings, lang: str = "en") -> None:
    await message.answer(
        "ℹ️ <b>File Searching is handled by Master Bot</b>\n\n"
        "This bot only delivers files via secure links. Please use our Master Bot to search the library.",
        reply_markup=get_redirect_to_master_keyboard(settings.MASTER_BOT_USERNAME, lang=lang),
        parse_mode="HTML",
    )

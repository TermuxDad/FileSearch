# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import Settings
from keyboards.inline import get_start_keyboard, get_help_keyboard
from lang.manager import tr
from utils.formatting import escape_html
from utils.logging import get_logger

logger = get_logger("plugins.help")

router = Router(name="help_router")

def get_help_caption(user_id: int, settings: Settings, lang: str = "en") -> str:
    if settings.is_owner(user_id):
        return tr("help_text_owner", lang)
    return tr("help_text", lang)

@router.message(Command("help"))
async def on_help_command(
    message: Message,
    settings: Settings,
    lang: str = "en",
) -> None:
    user = message.from_user
    user_id = user.id if user else 0
    help_caption = get_help_caption(user_id, settings, lang)
    help_kb = get_help_keyboard(lang)

    try:
        await message.answer_photo(
            photo=settings.START_IMAGE_URL,
            caption=help_caption,
            reply_markup=help_kb,
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning("Could not send help photo (fallback to text): %s", exc)
        await message.answer(help_caption, reply_markup=help_kb, parse_mode="HTML")

@router.callback_query(F.data == "help_menu")
async def on_help_callback(
    query: CallbackQuery,
    settings: Settings,
    lang: str = "en",
) -> None:
    user = query.from_user
    user_id = user.id if user else 0
    help_caption = get_help_caption(user_id, settings, lang)
    help_kb = get_help_keyboard(lang)

    if query.message:
        try:
            await query.message.edit_caption(
                caption=help_caption,
                reply_markup=help_kb,
                parse_mode="HTML",
            )
        except Exception:
            try:
                await query.message.edit_text(
                    text=help_caption,
                    reply_markup=help_kb,
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.debug("Non-fatal: could not edit to help menu: %s", exc)

    await query.answer()

@router.callback_query(F.data == "start_menu")
async def on_start_callback(
    query: CallbackQuery,
    settings: Settings,
    lang: str = "en",
) -> None:
    user = query.from_user
    first_name = escape_html(user.first_name if user else "Friend")

    if settings.is_dual_bot:
        welcome_text = tr(
            "welcome_dual_text",
            lang,
            first_name=first_name,
            delivery_username=settings.DELIVERY_BOT_USERNAME,
        )
    else:
        welcome_text = tr("welcome_text", lang, first_name=first_name)

    start_kb = get_start_keyboard(
        support_url=settings.SUPPORT_GROUP_URL,
        backup_url=settings.BACKUP_CHANNEL_URL,
        lang=lang,
    )

    if query.message:
        try:
            await query.message.edit_caption(
                caption=welcome_text,
                reply_markup=start_kb,
                parse_mode="HTML",
            )
        except Exception:
            try:
                await query.message.edit_text(
                    text=welcome_text,
                    reply_markup=start_kb,
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.debug("Non-fatal: could not edit to start menu: %s", exc)

    await query.answer()

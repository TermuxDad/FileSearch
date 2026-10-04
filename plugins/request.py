# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from lang.manager import tr
from services.request_manager import RequestManager
from utils.formatting import escape_html
from utils.logging import get_logger

logger = get_logger("plugins.request")

router = Router(name="request_router")

class FileRequestState(StatesGroup):
    waiting_for_description = State()

@router.message(Command("cancel"))
async def on_cancel_command(message: Message, state: FSMContext, lang: str = "en") -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(tr("request_cancel_no_active", lang))
        return

    await state.clear()
    await message.answer(tr("request_cancelled", lang))

@router.message(Command("request"))
async def on_request_command(message: Message, state: FSMContext, lang: str = "en") -> None:
    if message.chat.type != "private":
        await message.answer(tr("request_pm_only", lang))
        return

    await state.set_state(FileRequestState.waiting_for_description)
    await message.answer(tr("request_prompt", lang), parse_mode="HTML")

@router.message(FileRequestState.waiting_for_description, F.text)
async def on_request_description_received(
    message: Message,
    state: FSMContext,
    bot: Bot,
    request_manager: RequestManager,
    lang: str = "en",
) -> None:
    text = (message.text or "").strip()
    user = message.from_user
    if not user:
        return

    if text.startswith("/"):
        if text.startswith("/cancel"):
            await state.clear()
            await message.answer(tr("request_cancelled", lang))
        else:
            await message.answer(tr("request_text_only", lang))
        return

    if len(text) < 3:
        await message.answer(tr("request_too_short", lang))
        return

    if len(text) > 300:
        await message.answer(tr("request_too_long", lang))
        return

    await state.clear()
    clean_text = escape_html(text)

    try:
        doc = await request_manager.submit_request(
            bot=bot,
            user_id=user.id,
            description=text,
            first_name=user.first_name,
            username=user.username,
        )
        await message.answer(
            tr(
                "request_submitted",
                lang,
                description=clean_text,
                request_id=doc["_id"],
            ),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("Failed to submit request for user %d: %s", user.id, exc)
        await message.answer(tr("internal_error", lang))

@router.message(FileRequestState.waiting_for_description)
async def on_invalid_request_input(message: Message, lang: str = "en") -> None:
    await message.answer(tr("request_text_only", lang))

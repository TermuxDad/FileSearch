# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import Settings
from keyboards.pagination import PaginationManager
from lang.manager import tr
from plugins.request import FileRequestState
from services.request_manager import RequestManager
from services.search_engine import SearchEngine
from utils.formatting import escape_html
from utils.logging import get_logger

logger = get_logger("plugins.callbacks")

router = Router(name="callbacks_router")

@router.callback_query(F.data == "noop")
async def on_noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()

@router.callback_query(F.data == "make_request")
async def on_make_request_callback(callback: CallbackQuery, state: FSMContext, lang: str = "en") -> None:
    await state.set_state(FileRequestState.waiting_for_description)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            tr("request_prompt", lang),
            parse_mode="HTML",
        )

@router.callback_query(F.data.startswith("sp:"))
async def on_search_pagination_callback(
    callback: CallbackQuery,
    pagination_manager: PaginationManager,
    search_engine: SearchEngine,
    lang: str = "en",
) -> None:
    user = callback.from_user
    if not user:
        return

    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer("Malformed request.", show_alert=True)
        return

    _, session_id, page_str = parts

    try:
        page = int(page_str)
    except ValueError:
        await callback.answer("Invalid page.", show_alert=True)
        return

    session = pagination_manager.get_session(session_id)
    if not session:
        await callback.answer(tr("session_expired", lang), show_alert=True)
        return

    if session.user_id != user.id:
        await callback.answer(tr("session_not_yours", lang), show_alert=True)
        return

    if page < 1 or page > session.total_pages:
        await callback.answer()
        return

    keyboard = await pagination_manager.build_search_keyboard(
        session=session,
        page=page,
        search_engine=search_engine,
        lang=lang,
    )

    clean_query = escape_html(session.query)
    total = session.total_items
    pages = session.total_pages

    new_text = tr("search_results_header", lang, query=clean_query, total=total, page=page, pages=pages)

    try:
        if callback.message:
            await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except Exception as exc:
        logger.warning("Failed to edit pagination message: %s", exc)
        await callback.answer()

@router.callback_query(F.data.startswith("req_up:"))
async def on_request_uploaded_callback(
    callback: CallbackQuery,
    bot: Bot,
    settings: Settings,
    request_manager: RequestManager,
) -> None:
    user = callback.from_user
    if not user:
        return

    if not settings.is_owner(user.id):
        await callback.answer("⛔ Only configured bot owners can complete requests!", show_alert=True)
        return

    parts = (callback.data or "").split(":")
    if len(parts) != 2:
        await callback.answer("Malformed request callback.", show_alert=True)
        return

    request_id = parts[1]
    success, msg = await request_manager.mark_request_completed(
        bot=bot,
        request_id=request_id,
        completed_by_id=user.id,
    )

    await callback.answer(msg, show_alert=True)

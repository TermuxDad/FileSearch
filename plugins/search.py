# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
import asyncio
import re
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.types import Message

from config import settings
from keyboards.inline import get_empty_search_keyboard
from keyboards.pagination import PaginationManager
from lang.manager import tr
from services.manifest_manager import ManifestManager
from services.search_engine import SearchEngine
from services.statistics_manager import StatisticsManager
from services.request_manager import RequestManager
from utils.formatting import escape_html
from utils.logging import get_logger

logger = get_logger("plugins.search")

router = Router(name="search_router")

async def _safe_delete_message(message: Message) -> None:
    try:
        await message.delete()
    except Exception as exc:
        logger.debug("Non-fatal: could not delete query message %d: %s", message.message_id, exc)

@router.message(F.chat.id.func(lambda cid: cid == settings.FILES_GROUP_ID))
async def on_storage_file_received(
    message: Message,
    bot: Bot,
    manifest_manager: ManifestManager,
    stats_manager: StatisticsManager,
) -> None:
    file_id = None
    file_type = "document"
    file_name = None
    file_size = None
    mime_type = None

    if message.document:
        file_id = message.document.file_id
        file_type = "document"
        file_name = message.document.file_name
        file_size = message.document.file_size
        mime_type = message.document.mime_type
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
        file_name = message.video.file_name
        file_size = message.video.file_size
        mime_type = message.video.mime_type
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
        file_name = message.audio.file_name or message.audio.title or f"audio_{message.message_id}.mp3"
        file_size = message.audio.file_size
        mime_type = message.audio.mime_type
    elif message.animation:
        file_id = message.animation.file_id
        file_type = "animation"
        file_name = message.animation.file_name
        file_size = message.animation.file_size
        mime_type = message.animation.mime_type
    else:
        return

    caption = message.caption or file_name or ""
    if not caption:
        caption = f"file_{message.message_id}"

    try:
        record = await manifest_manager.ingest_file(
            bot=bot,
            caption=caption,
            file_type=file_type,
            file_id=file_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            source_chat_id=message.chat.id,
            source_message_id=message.message_id,
        )
        logger.info("Indexed file: %s (caption='%s')", record["id"], caption[:30])
    except Exception as exc:
        logger.exception("Failed to ingest file msg %d: %s", message.message_id, exc)

@router.message(F.chat.type == "private", F.text)
async def on_user_search(
    message: Message,
    search_engine: SearchEngine,
    pagination_manager: PaginationManager,
    stats_manager: StatisticsManager,
    bot: Optional[Bot] = None,
    request_manager: Optional[RequestManager] = None,
    lang: str = "en",
) -> None:
    query = (message.text or "").strip()
    user = message.from_user
    if not user:
        return

    if query.startswith("/"):
        return

    asyncio.create_task(_safe_delete_message(message))

    if "#request" in query.lower():
        clean_desc = re.sub(r"#request\b", "", query, flags=re.IGNORECASE).strip()
        if len(clean_desc) < 3:
            await message.answer(tr("request_too_short", lang))
            return
        if len(clean_desc) > 300:
            await message.answer(tr("request_too_long", lang))
            return

        if request_manager and bot:
            try:
                doc = await request_manager.submit_request(
                    bot=bot,
                    user_id=user.id,
                    description=clean_desc,
                    first_name=user.first_name,
                    username=user.username,
                )
                await message.answer(
                    tr(
                        "request_submitted",
                        lang,
                        description=escape_html(clean_desc),
                        request_id=doc["_id"],
                    ),
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.exception("Failed to submit #request for %d: %s", user.id, exc)
                await message.answer(tr("internal_error", lang))
        return

    if len(query) < 2:
        await message.answer(tr("search_too_short", lang))
        return

    if len(query) > 100:
        await message.answer(tr("search_too_long", lang))
        return

    stats_manager.record_search()
    results = search_engine.search(query=query, limit=100)
    clean_query = escape_html(query)

    if not results:
        await message.answer(
            tr("search_no_results", lang, query=clean_query),
            reply_markup=get_empty_search_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    file_ids = [f.id for f in results]
    session = pagination_manager.create_session(user_id=user.id, query=query, file_ids=file_ids)
    keyboard = await pagination_manager.build_search_keyboard(
        session, page=1, search_engine=search_engine, lang=lang
    )

    total = session.total_items
    pages = session.total_pages

    await message.answer(
        tr("search_results_header", lang, query=clean_query, total=total, page=1, pages=pages),
        reply_markup=keyboard,
        parse_mode="HTML",
    )

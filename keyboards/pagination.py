# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
import math
import uuid
from dataclasses import dataclass
from typing import List, Optional, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Settings
from lang.manager import tr
from services.cache_manager import TTLCache
from services.file_tokens import FileTokenService
from utils.formatting import format_result_button_text
from utils.logging import get_logger

logger = get_logger("keyboards.pagination")

@dataclass(slots=True)
class SearchSession:
    session_id: str
    user_id: int
    query: str
    file_ids: List[str]
    page_size: int = 10

    @property
    def total_items(self) -> int:
        return len(self.file_ids)

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.file_ids) / self.page_size))

    def get_page_file_ids(self, page: int) -> List[str]:
        if page < 1 or page > self.total_pages:
            return []
        start = (page - 1) * self.page_size
        end = start + self.page_size
        return self.file_ids[start:end]

class PaginationManager:
    def __init__(self, settings: Settings, token_service: FileTokenService, cache_size: int = 2000):
        self.settings = settings
        self.token_service = token_service
        self._sessions: TTLCache[SearchSession] = TTLCache(maxsize=cache_size, default_ttl=600.0)

    def create_session(self, user_id: int, query: str, file_ids: List[str]) -> SearchSession:
        session_id = uuid.uuid4().hex[:8]
        session = SearchSession(
            session_id=session_id,
            user_id=user_id,
            query=query,
            file_ids=file_ids,
            page_size=self.settings.SEARCH_PAGE_SIZE,
        )
        self._sessions.set(session_id, session)
        return session

    def get_session(self, session_id: str) -> Optional[SearchSession]:
        return self._sessions.get(session_id)

    async def build_search_keyboard(
        self,
        session: SearchSession,
        page: int,
        search_engine: Any,
        lang: str = "en",
    ) -> InlineKeyboardMarkup:
        page_file_ids = session.get_page_file_ids(page)
        buttons: List[List[InlineKeyboardButton]] = []

        for fid in page_file_ids:
            file_record = search_engine.get_file(fid)
            if not file_record:
                continue

            caption = file_record.caption or file_record.file_name or "File"
            size = file_record.file_size
            btn_title = format_result_button_text(caption, size, max_length=42)

            token = await self.token_service.create_token(fid)
            deep_link = f"https://t.me/{self.settings.delivery_username}?start={token}"
            buttons.append([InlineKeyboardButton(text=btn_title, url=deep_link)])

        total_pages = session.total_pages
        if total_pages > 1:
            nav_row: List[InlineKeyboardButton] = []
            if page > 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text=tr("btn_prev", lang),
                        callback_data=f"sp:{session.session_id}:{page - 1}",
                    )
                )
            nav_row.append(
                InlineKeyboardButton(
                    text=f"📄 {page}/{total_pages}",
                    callback_data="noop",
                )
            )
            if page < total_pages:
                nav_row.append(
                    InlineKeyboardButton(
                        text=tr("btn_next", lang),
                        callback_data=f"sp:{session.session_id}:{page + 1}",
                    )
                )
            buttons.append(nav_row)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

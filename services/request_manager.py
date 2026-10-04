# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
import uuid
from typing import Optional, Dict, Any, Tuple
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Settings
from database.requests import RequestRepository
from database.users import UserRepository
from lang.manager import tr
from utils.formatting import escape_html
from utils.logging import get_logger

logger = get_logger("request_manager")

class RequestManager:
    def __init__(self, settings: Settings, request_repo: RequestRepository, user_repo: Optional[UserRepository] = None):
        self.settings = settings
        self.request_repo = request_repo
        self.user_repo = user_repo

    async def submit_request(
        self,
        bot: Bot,
        user_id: int,
        description: str,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        req_id = uuid.uuid4().hex[:12]
        clean_desc = escape_html(description.strip())
        user_display = escape_html(first_name or "User")
        uname_line = f"<b>Username:</b> @{username}\n" if username else ""

        logger_text = (
            "📥 <b>New File Request</b>\n\n"
            f"<b>Requester:</b> {user_display} (<code>{user_id}</code>)\n"
            f"{uname_line}"
            f"<b>Requested Content:</b>\n"
            f"<blockquote>{clean_desc}</blockquote>\n\n"
            f"<b>ID:</b> <code>{req_id}</code>"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Mark Uploaded",
                        callback_data=f"req_up:{req_id}",
                    )
                ]
            ]
        )

        logger_msg = await bot.send_message(
            chat_id=self.settings.LOGGER_GROUP_ID,
            text=logger_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

        doc = await self.request_repo.create_request(
            request_id=req_id,
            user_id=user_id,
            description=description.strip(),
            logger_chat_id=self.settings.LOGGER_GROUP_ID,
            logger_message_id=logger_msg.message_id,
            first_name=first_name,
            username=username,
        )
        return doc

    async def mark_request_completed(
        self,
        bot: Bot,
        request_id: str,
        completed_by_id: int,
    ) -> Tuple[bool, str]:
        doc = await self.request_repo.complete_request(request_id, completed_by=completed_by_id)
        if not doc:
            return False, "This request does not exist or has already been completed."

        user_id = doc["user_id"]
        description = doc.get("description", "")
        clean_desc = escape_html(description)

        try:
            completed_text = (
                "✅ <b>Request Completed</b>\n\n"
                f"<b>Requester:</b> <code>{user_id}</code>\n"
                f"<b>Requested Content:</b>\n"
                f"<blockquote>{clean_desc}</blockquote>\n\n"
                f"<b>Status:</b> Uploaded & Notified\n"
                f"<b>Handled By:</b> <code>{completed_by_id}</code>"
            )
            await bot.edit_message_text(
                chat_id=doc["logger_chat_id"],
                message_id=doc["logger_message_id"],
                text=completed_text,
                parse_mode="HTML",
                reply_markup=None,
            )
        except Exception as exc:
            logger.warning("Could not update logger message for request %s: %s", request_id, exc)

        lang = "en"
        if self.user_repo:
            lang = await self.user_repo.get_language(user_id)

        notify_text = tr("request_completed_notify", lang, description=clean_desc)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=notify_text,
                parse_mode="HTML",
            )
            logger.info("Notified user %d for completed request %s", user_id, request_id)
        except (TelegramForbiddenError, TelegramBadRequest) as exc:
            logger.warning("Could not notify requester %d: %s", user_id, exc)
        except Exception as exc:
            logger.exception("Error notifying requester %d: %s", user_id, exc)

        return True, "Request successfully marked as uploaded and requester notified!"

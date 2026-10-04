# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from lang.manager import tr

def get_start_keyboard(support_url: str, backup_url: str, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr("btn_support_group", lang), url=support_url),
                InlineKeyboardButton(text=tr("btn_backup_channel", lang), url=backup_url),
            ],
            [
                InlineKeyboardButton(text=tr("btn_help", lang), callback_data="help_menu"),
            ],
        ]
    )

def get_help_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr("btn_back", lang), callback_data="start_menu"),
            ]
        ]
    )

def get_empty_search_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr("btn_request_file", lang), callback_data="make_request")]
        ]
    )

def get_redirect_to_master_keyboard(master_username: str, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr("btn_back_to_search", lang),
                    url=f"https://t.me/{master_username}",
                )
            ]
        ]
    )

def get_blocked_users_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons: List[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"blk_pg:{page - 1}"))
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"blk_pg:{page + 1}"))

    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])

def get_maintenance_keyboard(support_url: str, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr("btn_support_channel", lang), url=support_url),
            ]
        ]
    )

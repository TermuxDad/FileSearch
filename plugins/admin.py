# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from typing import Optional, Any

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import Settings
from database.settings import SystemSettingsRepository
from utils.logging import get_logger

logger = get_logger("plugins.admin")

router = Router(name="admin_router")


async def restart_bot_process(ecosystem: Optional[Any] = None) -> None:
    await asyncio.sleep(1.0)
    if ecosystem:
        try:
            await ecosystem.shutdown()
        except Exception as exc:
            logger.warning("Error during ecosystem shutdown before restart: %s", exc)

    if sys.platform == "win32":
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    else:
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception:
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit(0)


@router.message(Command("restart"))
async def on_restart_command(
    message: Message,
    settings: Settings,
    ecosystem: Optional[Any] = None,
) -> None:
    user = message.from_user
    if not user or not settings.is_owner(user.id):
        return

    await message.answer(
        f"🔄 <b>Restarting Bot System...</b>\n\n"
        f"• <b>Operating System:</b> <code>{sys.platform}</code>\n"
        f"• Gracefully shutting down services and rebooting process...",
        parse_mode="HTML",
    )

    logger.info("Executing /restart command from owner %d on %s", user.id, sys.platform)
    asyncio.create_task(restart_bot_process(ecosystem))


@router.message(Command("maintain"))
async def on_maintain_command(
    message: Message,
    command: CommandObject,
    settings: Settings,
    system_settings_repo: Optional[SystemSettingsRepository] = None,
) -> None:
    user = message.from_user
    if not user or not settings.is_owner(user.id):
        return

    if not system_settings_repo:
        await message.answer("⚠️ System settings repository is unavailable.", parse_mode="HTML")
        return

    arg = (command.args or "").strip().lower()
    if arg in ("on", "enable", "1", "true"):
        await system_settings_repo.set_maintenance_mode(True)
        await message.answer(
            "🛠️ <b>Maintenance Mode: ENABLED</b>\n\n"
            "• Public user access is now restricted.\n"
            "• Users will see the maintenance notification with the support channel button.\n"
            "• Bot owner accounts retain full command access.\n\n"
            "<i>To restore public access, run:</i> <code>/maintain off</code>",
            parse_mode="HTML",
        )
    elif arg in ("off", "disable", "0", "false"):
        await system_settings_repo.set_maintenance_mode(False)
        await message.answer(
            "✅ <b>Maintenance Mode: DISABLED</b>\n\n"
            "• Public access has been restored.\n"
            "• All users can now search and retrieve files normally.",
            parse_mode="HTML",
        )
    else:
        current_status = "ENABLED 🔴" if system_settings_repo.is_maintenance_mode else "DISABLED 🟢"
        await message.answer(
            f"🛠️ <b>Maintenance Mode Status:</b> <code>{current_status}</code>\n\n"
            "<b>Usage:</b>\n"
            "• <code>/maintain on</code> - Turn ON maintenance mode (blocks users)\n"
            "• <code>/maintain off</code> - Turn OFF maintenance mode (allows users)",
            parse_mode="HTML",
        )

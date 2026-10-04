# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import platform
import sys
import time
from typing import Optional
import psutil

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import Settings
from utils.formatting import format_file_size, format_duration
from utils.logging import get_logger

logger = get_logger("plugins.stats")

router = Router(name="stats_router")


def get_server_health(start_time: Optional[float] = None) -> dict:
    metrics = {
        "bot_ram": "N/A",
        "sys_ram": "N/A",
        "cpu_percent": "N/A",
        "disk_storage": "N/A",
        "uptime": "N/A",
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": platform.python_version(),
    }
    try:
        proc = psutil.Process()
        try:
            metrics["bot_ram"] = format_file_size(proc.memory_info().rss)
        except Exception:
            pass

        try:
            vmem = psutil.virtual_memory()
            metrics["sys_ram"] = (
                f"{format_file_size(vmem.used)} / {format_file_size(vmem.total)} ({vmem.percent}%)"
            )
        except Exception:
            pass

        try:
            disk_path = "/" if sys.platform != "win32" else "."
            disk = psutil.disk_usage(disk_path)
            metrics["disk_storage"] = (
                f"{format_file_size(disk.used)} / {format_file_size(disk.total)} ({disk.percent}%, {format_file_size(disk.free)} free)"
            )
        except Exception:
            pass

        try:
            cpu = psutil.cpu_percent(interval=None)
            metrics["cpu_percent"] = f"{cpu:.1f}%"
        except Exception:
            pass

        try:
            boot = start_time or proc.create_time()
            metrics["uptime"] = format_duration(time.time() - boot)
        except Exception:
            pass
    except Exception as exc:
        logger.warning("Could not read server metrics: %s", exc)
    return metrics


@router.message(Command("stats"))
async def on_stats_command(
    message: Message,
    settings: Settings,
    start_time: Optional[float] = None,
    **kwargs,
) -> None:
    user = message.from_user
    if not user or not settings.is_owner(user.id):
        return

    try:
        srv = get_server_health(start_time)
        response = (
            "📊 <b>System Telemetry</b>\n\n"
            f"• <b>Bot RAM:</b> <code>{srv['bot_ram']}</code>\n"
            f"• <b>System RAM:</b> <code>{srv['sys_ram']}</code>\n"
            f"• <b>CPU Load:</b> <code>{srv['cpu_percent']}</code>\n"
            f"• <b>Disk Storage:</b> <code>{srv['disk_storage']}</code>\n"
            f"• <b>Uptime:</b> <code>{srv['uptime']}</code>\n"
            f"• <b>OS:</b> <code>{srv['platform']}</code>\n"
            f"• <b>Python:</b> <code>v{srv['python']}</code>"
        )
        await message.answer(response, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Failed to compile system stats: %s", exc)
        await message.answer("⚠️ Failed to retrieve system statistics.")

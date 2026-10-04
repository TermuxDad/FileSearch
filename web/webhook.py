# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations

import hmac
from aiohttp import web
from aiogram.types import Update
from client.bots import BotEcosystem
from utils.logging import get_logger

logger = get_logger("web.webhook")

def _verify_secret_token(request: web.Request, expected_secret: str) -> bool:
    header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not expected_secret or not header:
        return False
    return hmac.compare_digest(header, expected_secret)

async def master_webhook_handler(request: web.Request) -> web.Response:
    ecosystem: BotEcosystem = request.app["ecosystem"]
    secret = ecosystem.settings.WEBHOOK_SECRET

    if not _verify_secret_token(request, secret):
        logger.warning("Unauthorized webhook request rejected for master bot")
        return web.Response(status=401, text="Unauthorized")

    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": ecosystem.master_bot})
        await ecosystem.master_dp.feed_update(bot=ecosystem.master_bot, update=update)
        return web.Response(status=200, text="OK")
    except Exception as exc:
        logger.error("Error processing master webhook update: %s", exc)
        return web.Response(status=500, text="Internal Error")

async def delivery_webhook_handler(request: web.Request) -> web.Response:
    ecosystem: BotEcosystem = request.app["ecosystem"]
    secret = ecosystem.settings.WEBHOOK_SECRET

    if not _verify_secret_token(request, secret):
        logger.warning("Unauthorized webhook request rejected for delivery bot")
        return web.Response(status=401, text="Unauthorized")

    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": ecosystem.delivery_bot})
        await ecosystem.delivery_dp.feed_update(bot=ecosystem.delivery_bot, update=update)
        return web.Response(status=200, text="OK")
    except Exception as exc:
        logger.error("Error processing delivery webhook update: %s", exc)
        return web.Response(status=500, text="Internal Error")

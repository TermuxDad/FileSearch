import asyncio
import logging
import os

from aiohttp import web
from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()

from bot.config import Config
from bot.database.db import Database
from bot.backup import BackupManager
from bot.handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("zombie_survival")

db = Database(Config.MONGO_URI, Config.MONGO_DB)
backup = BackupManager(None, db, Config)

app = Client(
    "zombie_survival_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=32,
)

async def health(request):
    return web.json_response({"status": "ok", "service": "zombie-survival"})

async def start_health_server():
    server = web.Application()
    server.router.add_get("/", health)
    server.router.add_get("/health", health)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("Health server listening on 0.0.0.0:%s", port)
    return runner

async def main():
    Config.validate()
    await db.connect()
    await db.ensure_indexes()
    backup.app = app
    register_handlers(app, db, Config)
    health_runner = await start_health_server()
    try:
        await app.start()
        # Disaster recovery happens before normal gameplay is exposed. It only
        # restores when all live game collections are empty and the backup has
        # a matching SHA-256 checksum.
        await backup.restore_latest_if_empty()
        await backup.start()
        app._zombie_backup_manager = backup
        restore_raids = getattr(app, "_zombie_restore_raids", None)
        if restore_raids:
            await restore_raids()
        me = await app.get_me()
        log.info("Bot started: @%s", me.username)
        await asyncio.Event().wait()
    finally:
        # Best-effort final snapshot before a clean shutdown/redeploy.
        if backup.enabled and app.is_connected:
            try:
                await backup.create_backup(reason="shutdown")
            except Exception:
                log.exception("Final shutdown backup failed")
        await backup.stop()
        await app.stop()
        await db.close()
        await health_runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

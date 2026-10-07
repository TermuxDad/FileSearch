import logging
from aiohttp import web
from pyrogram import Client
import config
from Client.database import Database

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("Veyro")

class Veyro(Client):
    def __init__(self):
        super().__init__(
            "Veyro",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            plugins={"root": "plugins"},
        )
        self.db = Database(config.MONGO_DB, config.MONGODB_DB_NAME)
        self.tag_jobs = {}
        self._http_runner = None
        self._http_site = None

    async def _health(self, request):
        try:
            await self.db.ping()
            return web.json_response({"status": "ok", "bot": "Veyro", "database": "ok"})
        except Exception:
            return web.json_response({"status": "degraded", "bot": "Veyro", "database": "unavailable"}, status=503)

    async def _home(self, request):
        return web.Response(text="Veyro is running.", content_type="text/plain")

    async def _start_http(self):
        app = web.Application()
        app.router.add_get("/", self._home)
        app.router.add_get("/health", self._health)
        self._http_runner = web.AppRunner(app, access_log=None)
        await self._http_runner.setup()
        self._http_site = web.TCPSite(self._http_runner, "0.0.0.0", config.PORT)
        await self._http_site.start()
        log.info("HTTP health server listening on 0.0.0.0:%s", config.PORT)

    async def start(self, *args, **kwargs):
        await self.db.ensure_indexes()
        await super().start(*args, **kwargs)
        await self._start_http()
        me = await self.get_me()
        if not config.BOT_USERNAME and me.username:
            config.BOT_USERNAME = me.username
        log.info("Veyro started as @%s", me.username or me.id)
        if config.LOGGER_GROUP:
            try:
                await self.send_message(config.LOGGER_GROUP, "<b>Vᴇʏʀᴏ Hᴀꜱ Sᴛᴀʀᴛᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</b>")
            except Exception:
                log.exception("Failed to send startup log")

    async def stop(self, *args, **kwargs):
        for state in list(self.tag_jobs.values()):
            state["task"].cancel()
        self.tag_jobs.clear()
        if self._http_runner:
            await self._http_runner.cleanup()
            self._http_runner = None
            self._http_site = None
        await self.db.close()
        await super().stop(*args, **kwargs)

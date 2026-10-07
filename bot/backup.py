from __future__ import annotations

import asyncio
import gzip
import hashlib
import logging
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson import json_util

log = logging.getLogger("zombie_survival.backup")

BACKUP_COLLECTIONS = ("players", "missions", "raids", "combats", "pvp_challenges", "pvp_fights", "clans", "clan_wars", "territories", "event_claims", "rivalries")


class BackupManager:
    """MongoDB -> Telegram disaster-recovery snapshots.

    MongoDB remains the live source of truth. Telegram only stores compressed
    snapshots so an empty/corrupted Mongo database can be reconstructed.
    """

    def __init__(self, app, db, config):
        self.app = app
        self.db = db
        self.config = config
        self.chat_id = config.BACKUP_CHAT_ID
        self.interval = max(300, config.BACKUP_INTERVAL_SECONDS)
        self.keep = max(2, config.BACKUP_KEEP)
        self.auto_restore = config.AUTO_RESTORE
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._stopping = False

    @property
    def enabled(self) -> bool:
        return bool(self.chat_id)

    async def start(self):
        if not self.enabled:
            log.warning("Telegram backup disabled: BACKUP_CHAT_ID is not configured")
            return
        self._stopping = False
        self._task = asyncio.create_task(self._loop(), name="zombie-backup-loop")
        log.info("Telegram backup enabled: every %ss, keep=%s", self.interval, self.keep)

    async def stop(self):
        self._stopping = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self):
        # Give the bot a moment to finish startup before the first snapshot.
        await asyncio.sleep(10)
        while not self._stopping:
            try:
                await self.create_backup(reason="scheduled")
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Scheduled backup failed")
            await asyncio.sleep(self.interval)

    async def create_backup(self, reason: str = "manual") -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("BACKUP_CHAT_ID is not configured")

        async with self._lock:
            started = time.monotonic()
            payload = await self._snapshot()
            raw = json_util.dumps(payload, separators=(",", ":")).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            compressed = gzip.compress(raw, compresslevel=6)

            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"zombie_backup_{stamp}_{digest[:12]}.json.gz"
            temp_path = Path(tempfile.gettempdir()) / filename
            temp_path.write_bytes(compressed)

            try:
                caption = (
                    "🗄 <b>Zombie Survival Backup</b>\n"
                    f"• Reason: <b>{reason}</b>\n"
                    f"• Players: <b>{payload['counts'].get('players', 0):,}</b>\n"
                    f"• Raw: <b>{len(raw):,} bytes</b>\n"
                    f"• Compressed: <b>{len(compressed):,} bytes</b>\n"
                    f"• SHA-256: <code>{digest}</code>\n"
                    f"• UTC: <code>{payload['created_at']}</code>"
                )
                chat_id = self.chat_id
                if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
                    chat_id = int(chat_id)
                msg = await self.app.send_document(
                    chat_id=chat_id,
                    document=str(temp_path),
                    file_name=filename,
                    caption=caption,
                )
                message_id = int(msg.id)
                file_id = getattr(getattr(msg, "document", None), "file_id", None)

                await self.db.db.backups.insert_one({
                    "message_id": message_id,
                    "file_id": file_id,
                    "chat_id": self.chat_id,
                    "filename": filename,
                    "sha256": digest,
                    "raw_bytes": len(raw),
                    "compressed_bytes": len(compressed),
                    "players": payload["counts"].get("players", 0),
                    "reason": reason,
                    "created_at": datetime.now(timezone.utc),
                })
                await self._prune_metadata()

                elapsed = time.monotonic() - started
                log.info(
                    "Backup complete: %s players=%s compressed=%s elapsed=%.2fs",
                    filename,
                    payload["counts"].get("players", 0),
                    len(compressed),
                    elapsed,
                )
                return {
                    "message_id": message_id,
                    "file_id": file_id,
                    "filename": filename,
                    "players": payload["counts"].get("players", 0),
                    "raw_bytes": len(raw),
                    "compressed_bytes": len(compressed),
                    "sha256": digest,
                    "elapsed": elapsed,
                }
            finally:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    async def _snapshot(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "format": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database": self.config.MONGO_DB,
            "collections": {},
            "counts": {},
        }
        for name in BACKUP_COLLECTIONS:
            docs = await self.db.db[name].find({}).to_list(length=None)
            data["collections"][name] = docs
            data["counts"][name] = len(docs)
        return data

    async def _prune_metadata(self):
        old = await self.db.db.backups.find({}, {"_id": 1, "message_id": 1}).sort("created_at", -1).skip(self.keep).to_list(length=1000)
        if old:
            await self.db.db.backups.delete_many({"_id": {"$in": [x["_id"] for x in old]}})
        # Do not delete Telegram backup messages automatically. Keeping them is
        # safer for disaster recovery; metadata is simply bounded in MongoDB.

    async def latest_backup(self) -> dict[str, Any] | None:
        return await self.db.db.backups.find_one({}, sort=[("created_at", -1)])

    async def restore_latest_if_empty(self) -> bool:
        if not self.enabled or not self.auto_restore:
            return False

        counts = {name: await self.db.db[name].count_documents({}) for name in BACKUP_COLLECTIONS}
        if any(counts.values()):
            log.info("Auto-restore skipped: live database is not empty: %s", counts)
            return False

        meta = await self.latest_backup()
        if not meta or not meta.get("file_id"):
            # The backup metadata itself lives in MongoDB, so it disappears if
            # the whole database was deleted. Fall back to Telegram history and
            # discover the newest backup document directly.
            meta = await self._find_latest_telegram_backup()
        if not meta or not meta.get("file_id"):
            log.warning("Auto-restore skipped: no Telegram backup could be discovered")
            return False

        log.warning("Live database is empty; attempting restore from Telegram backup message %s", meta.get("message_id"))
        tg_file = await self.app.download_media(meta["file_id"], in_memory=True)
        raw_gz = self._bytes_from_download(tg_file)
        raw = gzip.decompress(raw_gz)
        digest = hashlib.sha256(raw).hexdigest()
        if meta.get("sha256") and digest != meta["sha256"]:
            raise RuntimeError("Backup SHA-256 verification failed; refusing restore")
        payload = json_util.loads(raw.decode("utf-8"))
        await self._restore_payload(payload)
        log.warning("Automatic restore completed from backup message %s", meta.get("message_id"))
        return True

    async def _find_latest_telegram_backup(self) -> dict[str, Any] | None:
        """Find the newest backup even when MongoDB metadata is gone."""
        try:
            async for message in self.app.get_chat_history(self.chat_id, limit=50):
                document = getattr(message, "document", None)
                filename = getattr(document, "file_name", "") if document else ""
                if not filename.startswith("zombie_backup_") or not filename.endswith(".json.gz"):
                    continue
                caption = getattr(message, "caption", "") or ""
                match = re.search(r"SHA-256:\s*<code>([0-9a-f]{64})</code>", caption, re.I)
                return {
                    "message_id": int(message.id),
                    "file_id": getattr(document, "file_id", None),
                    "sha256": match.group(1) if match else None,
                    "chat_id": self.chat_id,
                    "filename": filename,
                }
        except Exception:
            log.exception("Could not scan Telegram backup history")
        return None

    @staticmethod
    def _bytes_from_download(value: Any) -> bytes:
        if hasattr(value, "getbuffer"):
            return bytes(value.getbuffer())
        if isinstance(value, (str, Path)):
            return Path(value).read_bytes()
        if isinstance(value, bytes):
            return value
        return bytes(value)

    async def _restore_payload(self, payload: dict[str, Any]):
        if payload.get("format") != 1:
            raise RuntimeError("Unsupported backup format")
        collections = payload.get("collections")
        if not isinstance(collections, dict):
            raise RuntimeError("Backup is missing collections")

        # Insert into empty collections only. Startup checks guarantee this,
        # and each collection is checked again to avoid accidental overwrites.
        for name in BACKUP_COLLECTIONS:
            docs = collections.get(name, [])
            if not isinstance(docs, list):
                raise RuntimeError(f"Invalid backup collection: {name}")
            if await self.db.db[name].count_documents({}) != 0:
                raise RuntimeError(f"Refusing restore because collection is not empty: {name}")
            if docs:
                await self.db.db[name].insert_many(docs, ordered=False)

    async def status(self) -> dict[str, Any]:
        meta = await self.latest_backup()
        return {
            "enabled": self.enabled,
            "chat_id": self.chat_id,
            "interval_seconds": self.interval,
            "keep_metadata": self.keep,
            "auto_restore": self.auto_restore,
            "latest": meta,
        }

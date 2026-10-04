# THIS SOURCE CODE IS DEVELOPED BY @MIGHTYAYUSH. FOLLOW @SOCIAL_BOTS FOR MORE DETAILS AND MEET THE DEVELOPER...
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.logging import get_logger

logger = get_logger("database.settings")

class SystemSettingsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.settings
        self._maintenance_mode: bool = False

    @property
    def is_maintenance_mode(self) -> bool:
        return self._maintenance_mode

    async def load(self) -> None:
        try:
            doc = await self.collection.find_one({"_id": "system_config"})
            if doc:
                self._maintenance_mode = bool(doc.get("maintenance_mode", False))
                logger.info("Loaded system settings: maintenance_mode=%s", self._maintenance_mode)
            else:
                await self.collection.update_one(
                    {"_id": "system_config"},
                    {"$setOnInsert": {"maintenance_mode": False, "updated_at": datetime.now(timezone.utc).isoformat()}},
                    upsert=True,
                )
                self._maintenance_mode = False
        except Exception as exc:
            logger.warning("Failed to load system settings from MongoDB: %s", exc)

    async def set_maintenance_mode(self, enabled: bool) -> None:
        self._maintenance_mode = enabled
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            await self.collection.update_one(
                {"_id": "system_config"},
                {"$set": {"maintenance_mode": enabled, "updated_at": now_iso}},
                upsert=True,
            )
            logger.info("Maintenance mode set to: %s", enabled)
        except Exception as exc:
            logger.error("Failed to update maintenance mode in MongoDB: %s", exc)

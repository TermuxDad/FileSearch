from datetime import datetime, timezone, timedelta

class Database:
    def __init__(self, uri, name):
        from motor.motor_asyncio import AsyncIOMotorClient
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
        self.db = self.client[name]

    async def ensure_indexes(self):
        await self.db.users.create_index("user_id", unique=True)
        await self.db.groups.create_index("chat_id", unique=True)
        await self.db.whispers.create_index("expires_at", expireAfterSeconds=0)
        try:
            await self.db.whisper_targets.drop_index("sender_id_1")
        except Exception:
            pass
        await self.db.whisper_targets.create_index(
            [("sender_id", 1), ("target_id", 1)],
            unique=True,
            name="sender_target_unique",
        )
        await self.db.whisper_targets.create_index(
            [("sender_id", 1), ("updated_at", -1)],
            name="sender_updated",
        )

    async def ping(self):
        await self.client.admin.command("ping")
        return True

    async def close(self):
        self.client.close()

    async def ensure_group(self, chat_id, title=""):
        await self.db.groups.update_one(
            {"chat_id": chat_id},
            {"$setOnInsert": {"chat_id": chat_id, "title": title, "created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def register_user(self, user_id):
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"last_seen": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def register_group(self, chat_id, title=""):
        await self.ensure_group(chat_id, title)
        await self.db.groups.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title, "last_seen": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def save_whisper(self, whisper_id, target_id, sender_id, message, chat_id=None, target_name=""):
        now = datetime.now(timezone.utc)
        await self.db.whispers.insert_one({
            "_id": whisper_id,
            "target_id": target_id,
            "sender_id": sender_id,
            "chat_id": chat_id,
            "target_name": target_name,
            "message": message,
            "created_at": now,
            "expires_at": now + timedelta(hours=24),
            "read_at": None,
        })

    async def get_whisper(self, whisper_id):
        return await self.db.whispers.find_one({"_id": whisper_id})

    async def mark_whisper_read(self, whisper_id, reader_id):
        now = datetime.now(timezone.utc)
        return await self.db.whispers.find_one_and_update(
            {"_id": whisper_id, "read_at": None},
            {"$set": {"read_at": now, "reader_id": reader_id}},
            return_document=__import__("pymongo").ReturnDocument.AFTER,
        )

    async def save_whisper_target(self, sender_id, target_id, target_name="", username=""):
        now = datetime.now(timezone.utc)
        target_id = int(target_id)
        existing = await self.db.whisper_targets.find_one({"sender_id": sender_id, "target_id": target_id})
        if existing:
            await self.db.whisper_targets.update_one(
                {"_id": existing["_id"]},
                {"$set": {"target_name": target_name or existing.get("target_name", str(target_id)), "username": username, "updated_at": now}},
            )
            return
        count = await self.db.whisper_targets.count_documents({"sender_id": sender_id})
        if count >= 10:
            oldest = await self.db.whisper_targets.find_one(
                {"sender_id": sender_id},
                sort=[("updated_at", 1), ("_id", 1)],
            )
            if oldest:
                await self.db.whisper_targets.delete_one({"_id": oldest["_id"]})
        await self.db.whisper_targets.insert_one({
            "sender_id": sender_id,
            "target_id": target_id,
            "target_name": target_name or str(target_id),
            "username": username,
            "updated_at": now,
        })

    async def update_whisper_target_identity(self, sender_id, target_id, target_name=None, username=None):
        target_id = int(target_id)
        update = {}
        if target_name:
            update["target_name"] = target_name
        if username is not None:
            update["username"] = username or ""
        if not update:
            return
        update["updated_at"] = datetime.now(timezone.utc)
        await self.db.whisper_targets.update_one(
            {"sender_id": sender_id, "target_id": target_id},
            {"$set": update},
        )

    async def get_whisper_targets(self, sender_id, limit=10):
        cursor = self.db.whisper_targets.find({"sender_id": sender_id}).sort("updated_at", -1).limit(limit)
        return [item async for item in cursor]

    async def get_whisper_target(self, sender_id):
        targets = await self.get_whisper_targets(sender_id, 1)
        return targets[0] if targets else None

    async def inc_stat(self, key, amount=1):
        await self.db.stats.update_one({"_id": key}, {"$inc": {"value": amount}}, upsert=True)

    async def get_stats(self):
        cursor = self.db.stats.find({}).sort("value", -1)
        return {x["_id"]: x.get("value", 0) async for x in cursor}

    async def count_users(self):
        return await self.db.users.count_documents({})

    async def count_groups(self):
        return await self.db.groups.count_documents({})

    async def get_all_targets(self):
        users = await self.db.users.distinct("user_id")
        groups = await self.db.groups.distinct("chat_id")
        return list(dict.fromkeys(users + groups))

from datetime import datetime, timezone, timedelta
from pymongo import ReturnDocument

class Database:
    def __init__(self, uri, name):
        from motor.motor_asyncio import AsyncIOMotorClient
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
        self.db = self.client[name]

    async def ensure_indexes(self):
        await self.db.users.create_index("user_id", unique=True)
        await self.db.groups.create_index("chat_id", unique=True)
        await self.db.notes.create_index([("chat_id", 1), ("name", 1)], unique=True)
        await self.db.admin_powers.create_index([("chat_id", 1), ("user_id", 1)], unique=True)
        await self.db.promoted_admins.create_index([("chat_id", 1), ("user_id", 1)], unique=True)
        await self.db.warnings.create_index([("chat_id", 1), ("user_id", 1)], unique=True)
        await self.db.whispers.create_index("expires_at", expireAfterSeconds=0)

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

    async def set_power(self, chat_id, user_id, power, enabled=True):
        await self.db.admin_powers.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {f"powers.{power}": enabled}},
            upsert=True,
        )

    async def get_powers(self, chat_id, user_id):
        doc = await self.db.admin_powers.find_one({"chat_id": chat_id, "user_id": user_id}) or {}
        return doc.get("powers", {})

    async def add_warning(self, chat_id, user_id, reason=""):
        doc = await self.db.warnings.find_one_and_update(
            {"chat_id": chat_id, "user_id": user_id},
            {"$inc": {"count": 1}, "$push": {"items": {"reason": reason, "at": datetime.now(timezone.utc)}}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int((doc or {}).get("count", 0))

    async def remove_warning(self, chat_id, user_id):
        doc = await self.db.warnings.find_one({"chat_id": chat_id, "user_id": user_id}) or {}
        count = max(0, int(doc.get("count", 0)) - 1)
        await self.db.warnings.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"count": count}},
            upsert=True,
        )
        return count

    async def get_warning(self, chat_id, user_id):
        return await self.db.warnings.find_one({"chat_id": chat_id, "user_id": user_id}) or {"count": 0, "items": []}

    async def save_note(self, chat_id, name, data):
        name = name.strip().lower()
        await self.db.notes.update_one(
            {"chat_id": chat_id, "name": name},
            {"$set": {"chat_id": chat_id, "name": name, "data": data, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def get_note(self, chat_id, name):
        return await self.db.notes.find_one({"chat_id": chat_id, "name": name.strip().lower()})

    async def list_notes(self, chat_id):
        cursor = self.db.notes.find({"chat_id": chat_id}, {"name": 1, "_id": 0}).sort("name", 1)
        return await cursor.to_list(length=500)

    async def delete_note(self, chat_id, name):
        result = await self.db.notes.delete_one({"chat_id": chat_id, "name": name.strip().lower()})
        return result.deleted_count > 0

    async def clear_notes(self, chat_id):
        result = await self.db.notes.delete_many({"chat_id": chat_id})
        return result.deleted_count

    async def mark_promoted(self, chat_id, user_id):
        await self.db.promoted_admins.update_one({"chat_id": chat_id, "user_id": user_id}, {"$set": {"chat_id": chat_id, "user_id": user_id}}, upsert=True)

    async def get_promoted_admins(self, chat_id):
        cursor = self.db.promoted_admins.find({"chat_id": chat_id}, {"user_id": 1, "_id": 0})
        return [x["user_id"] async for x in cursor]

    async def clear_promoted(self, chat_id, user_id):
        await self.db.promoted_admins.delete_one({"chat_id": chat_id, "user_id": user_id})

    async def save_whisper(self, whisper_id, target_id, sender_id, message):
        now = datetime.now(timezone.utc)
        await self.db.whispers.insert_one({
            "_id": whisper_id,
            "target_id": target_id,
            "sender_id": sender_id,
            "message": message,
            "created_at": now,
            "expires_at": now + timedelta(hours=24),
        })

    async def get_whisper(self, whisper_id):
        return await self.db.whispers.find_one({"_id": whisper_id})

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

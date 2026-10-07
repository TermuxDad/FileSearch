from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    def __init__(self, uri: str, name: str):
        self.uri = uri
        self.name = name
        self.client = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(
            self.uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        await self.client.admin.command("ping")
        self.db = self.client[self.name]

    async def close(self):
        if self.client:
            self.client.close()

    async def ensure_indexes(self):
        await self.db.players.create_index("user_id", unique=True)
        await self.db.players.create_index([("xp", -1)])
        await self.db.players.create_index([("level", -1), ("xp", -1)])
        await self.db.raids.create_index("chat_id", unique=True)
        await self.db.combats.create_index("user_id", unique=True)
        await self.db.combats.create_index("created_at")
        await self.db.missions.create_index([("user_id", 1), ("kind", 1)], unique=True)
        await self.db.backups.create_index([("created_at", -1)])

    async def get_player(self, user_id: int, name="", username=""):
        p = await self.db.players.find_one({"user_id": user_id})
        if p:
            updates = {}
            if name and p.get("name") != name:
                updates["name"] = name
            if username != p.get("username"):
                updates["username"] = username
            if "coins_earned" not in p:
                updates["coins_earned"] = 0
            if "weapon_upgrade" not in p:
                updates["weapon_upgrade"] = 0
            if "armor_upgrade" not in p:
                updates["armor_upgrade"] = 0
            if updates:
                await self.db.players.update_one({"user_id": user_id}, {"$set": updates})
                p.update(updates)
            return p
        now = datetime.now(timezone.utc)
        p = {
            "user_id": user_id,
            "name": name or "Survivor",
            "username": username,
            "level": 1,
            "xp": 0,
            "coins": 500,
            "coins_earned": 0,
            "hp": 100,
            "max_hp": 100,
            "energy": 100,
            "max_energy": 100,
            "weapon": "rusty_knife",
            "armor": "torn_jacket",
            "weapon_upgrade": 0,
            "armor_upgrade": 0,
            "inventory": {"rusty_knife": 1, "torn_jacket": 1, "scrap": 0, "medkit": 2},
            "kills": 0,
            "pvp_wins": 0,
            "raids": 0,
            "raid_damage": 0,
            "created_at": now,
            "last_daily": None,
            "last_energy": now,
        }
        await self.db.players.insert_one(p)
        return p

    async def update_player(self, user_id, update):
        await self.db.players.update_one({"user_id": user_id}, update)

    async def get_combat(self, user_id):
        return await self.db.combats.find_one({"user_id": user_id})

    async def set_combat(self, user_id, data):
        data = dict(data)
        data["user_id"] = user_id
        await self.db.combats.replace_one({"user_id": user_id}, data, upsert=True)

    async def delete_combat(self, user_id):
        await self.db.combats.delete_one({"user_id": user_id})

    async def get_active_raids(self):
        return await self.db.raids.find({}).to_list(length=None)

    async def get_raid(self, chat_id):
        return await self.db.raids.find_one({"chat_id": chat_id})

    async def set_raid(self, chat_id, data):
        await self.db.raids.replace_one({"chat_id": chat_id}, data, upsert=True)

    async def delete_raid(self, chat_id):
        await self.db.raids.delete_one({"chat_id": chat_id})

    async def leaderboard(self, limit=10):
        return await self.db.players.find({}).sort([("level", -1), ("xp", -1), ("kills", -1)]).limit(limit).to_list(length=limit)

    async def group_leaderboard(self, user_ids, limit=10):
        return await self.db.players.find({"user_id": {"$in": user_ids}}).sort([("level", -1), ("xp", -1)]).limit(limit).to_list(length=limit)

    async def count_players(self):
        return await self.db.players.count_documents({})

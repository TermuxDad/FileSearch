from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    def __init__(self, uri: str, name: str):
        self.uri, self.name = uri, name
        self.client = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(self.uri, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)
        await self.client.admin.command("ping")
        self.db = self.client[self.name]

    async def close(self):
        if self.client:
            self.client.close()

    async def ensure_indexes(self):
        await self.db.players.create_index("user_id", unique=True)
        await self.db.players.create_index([("level", -1), ("xp", -1)])
        await self.db.players.create_index([("pvp_wins", -1), ("pvp_streak", -1)])
        await self.db.players.create_index([("bounty", -1)])
        await self.db.raids.create_index("chat_id", unique=True)
        await self.db.combats.create_index("user_id", unique=True)
        await self.db.missions.create_index([("user_id", 1), ("kind", 1)], unique=True)
        await self.db.backups.create_index([("created_at", -1)])
        await self.db.pvp_challenges.create_index("challenge_id", unique=True)
        await self.db.pvp_fights.create_index("fight_id", unique=True)
        await self.db.clans.create_index("clan_id", unique=True)
        await self.db.clans.create_index("members")
        await self.db.clan_wars.create_index("war_id", unique=True)
        await self.db.clan_wars.create_index([("status", 1), ("ends_at", 1)])
        await self.db.territories.create_index("territory_id", unique=True)
        await self.db.event_claims.create_index([("user_id", 1), ("period", 1)], unique=True)
        await self.db.rivalries.create_index("key", unique=True)

    async def get_player(self, user_id: int, name="", username=""):
        p = await self.db.players.find_one({"user_id": user_id})
        defaults = {
            "coins_earned": 0, "weapon_upgrade": 0, "armor_upgrade": 0,
            "pvp_wins": 0, "pvp_losses": 0, "pvp_streak": 0, "best_streak": 0,
            "pvp_damage": 0, "reputation": 0, "bounty": 0, "bounties_claimed": 0,
            "bloodlust": 0, "rival_user_id": None, "clan_id": None,
            "injury_until": None, "last_energy": datetime.now(timezone.utc),
        }
        if p:
            updates = {}
            if name and p.get("name") != name: updates["name"] = name
            if username != p.get("username"): updates["username"] = username
            for k,v in defaults.items():
                if k not in p: updates[k]=v
            if updates:
                await self.db.players.update_one({"user_id": user_id}, {"$set": updates})
                p.update(updates)
            return p
        now = datetime.now(timezone.utc)
        p = {
            "user_id": user_id, "name": name or "Survivor", "username": username,
            "level": 1, "xp": 0, "coins": 500, "coins_earned": 0,
            "hp": 100, "max_hp": 100, "energy": 100, "max_energy": 100,
            "weapon": "rusty_knife", "armor": "torn_jacket", "weapon_upgrade": 0, "armor_upgrade": 0,
            "inventory": {"rusty_knife":1,"torn_jacket":1,"scrap":0,"medkit":2},
            "kills":0,"pvp_wins":0,"pvp_losses":0,"pvp_streak":0,"best_streak":0,"pvp_damage":0,
            "raids":0,"raid_damage":0,"reputation":0,"bounty":0,"bounties_claimed":0,"bloodlust":0,
            "rival_user_id":None,"clan_id":None,"injury_until":None,
            "created_at":now,"last_daily":None,"last_energy":now,
        }
        await self.db.players.insert_one(p)
        return p

    async def update_player(self, user_id, update):
        await self.db.players.update_one({"user_id": user_id}, update)

    async def get_combat(self, user_id): return await self.db.combats.find_one({"user_id": user_id})
    async def set_combat(self, user_id, data):
        d=dict(data); d["user_id"]=user_id; await self.db.combats.replace_one({"user_id":user_id},d,upsert=True)
    async def delete_combat(self,user_id): await self.db.combats.delete_one({"user_id":user_id})
    async def get_active_raids(self): return await self.db.raids.find({}).to_list(length=None)
    async def get_raid(self,chat_id): return await self.db.raids.find_one({"chat_id":chat_id})
    async def set_raid(self,chat_id,data): await self.db.raids.replace_one({"chat_id":chat_id},data,upsert=True)
    async def delete_raid(self,chat_id): await self.db.raids.delete_one({"chat_id":chat_id})
    async def leaderboard(self,limit=10): return await self.db.players.find({}).sort([("level",-1),("xp",-1),("kills",-1)]).limit(limit).to_list(length=limit)
    async def group_leaderboard(self,user_ids,limit=10): return await self.db.players.find({"user_id":{"$in":user_ids}}).sort([("level",-1),("xp",-1)]).limit(limit).to_list(length=limit)
    async def wanted(self,limit=10): return await self.db.players.find({"bounty":{"$gt":0}}).sort("bounty",-1).limit(limit).to_list(length=limit)
    async def count_players(self): return await self.db.players.count_documents({})

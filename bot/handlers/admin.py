from pyrogram import filters
from .common import btn, kb

def register(app, db, config):
    def owner(uid):
        return uid in config.OWNER_IDS

    @app.on_message(filters.command("stats") & filters.private)
    async def stats(_, message):
        if not owner(message.from_user.id):
            return
        count = await db.count_players()
        await message.reply_text(f"🛠️ <b>ADMIN STATS</b>\n\n👥 Players: <b>{count:,}</b>")

    @app.on_message(filters.command("givecoins") & filters.private)
    async def givecoins(_, message):
        if not owner(message.from_user.id):
            return
        parts = message.text.split()
        if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
            await message.reply_text("Usage: /givecoins USER_ID AMOUNT")
            return
        uid, amount = int(parts[1]), int(parts[2])
        await db.update_player(uid, {"$inc": {"coins": amount}})
        await message.reply_text("✅ Coins added.")

    @app.on_message(filters.command("setlevel") & filters.private)
    async def setlevel(_, message):
        if not owner(message.from_user.id):
            return
        parts = message.text.split()
        if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
            await message.reply_text("Usage: /setlevel USER_ID LEVEL")
            return
        uid, level = int(parts[1]), max(1, int(parts[2]))
        await db.update_player(uid, {"$set": {"level": level, "xp": 0, "max_hp": 100 + (level-1)*8, "max_energy": 100 + (level-1)*3}})
        await message.reply_text("✅ Level updated.")

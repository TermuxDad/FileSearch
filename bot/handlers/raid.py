import asyncio
import random
import time
from pyrogram import filters
from .common import btn, kb
from .missions import record_progress
from bot.game.data import weapon_attack
from bot.game.engine import apply_xp

RAID_DURATION = 300
BOSS = {"name": "☣️ MUTANT HORDE", "hp": 5000, "max_hp": 5000}


def raid_keyboard(chat_id):
    return kb([
        [btn("🟢 ☣️ Join Raid", f"raid:join:{chat_id}"), btn("🔵 ⚔️ Attack", f"raid:attack:{chat_id}")],
        [btn("🔴 🏁 End/View Raid", f"raid:view:{chat_id}")],
    ])


async def finish_raid(app, db, chat_id):
    raid = await db.get_raid(chat_id)
    if not raid:
        return False
    # Prevent duplicate rewards when timer + button both finish the same raid.
    locked = await db.db.raids.update_one(
        {"chat_id": chat_id, "status": {"$ne": "finished"}},
        {"$set": {"status": "finished"}},
    )
    if locked.modified_count != 1:
        return False

    participants = raid.get("participants", [])
    boss_hp = max(0, raid.get("boss_hp", 0))
    if boss_hp <= 0:
        reward = 1000
        xp_reward = 500
        result = "🏆 <b>HORDE DEFEATED!</b>\n\nEvery participant received:\n💰 +1,000 coins\n⭐ +500 XP"
    else:
        reward = 250
        xp_reward = 100
        result = "⏱️ <b>RAID ENDED</b>\n\nThe Horde survived.\nParticipants received consolation rewards."

    for uid in participants:
        p = await db.get_player(uid)
        if not p:
            continue
        new_xp, level, max_hp, max_energy, _ = apply_xp(p, xp_reward)
        await db.update_player(uid, {
            "$inc": {"raids": 1, "coins": reward, "coins_earned": reward},
            "$set": {"xp": new_xp, "level": level, "max_hp": max_hp, "max_energy": max_energy},
        })
        await record_progress(db, uid, "raids", 1)
        await record_progress(db, uid, "coins", reward)

    await db.delete_raid(chat_id)
    try:
        await app.send_message(chat_id, result)
    except Exception:
        pass
    return True


async def raid_timer(app, db, chat_id, ends_at):
    delay = max(0, int(ends_at) - int(time.time())) + 1
    await asyncio.sleep(delay)
    await finish_raid(app, db, chat_id)


def register(app, db):
    @app.on_message(filters.command("raid") & filters.group)
    async def raid_start(_, message):
        chat_id = message.chat.id
        existing = await db.get_raid(chat_id)
        if existing and int(time.time()) < existing.get("ends_at", 0):
            await message.reply_text("☣️ A raid is already active!", reply_markup=raid_keyboard(chat_id))
            return
        if existing:
            await finish_raid(app, db, chat_id)

        now = int(time.time())
        raid = {
            "chat_id": chat_id,
            "boss_hp": BOSS["max_hp"],
            "max_hp": BOSS["max_hp"],
            "participants": [],
            "damage": {},
            "created_at": now,
            "ends_at": now + RAID_DURATION,
            "status": "active",
        }
        await db.set_raid(chat_id, raid)
        await message.reply_text(
            "🚨 <b>ZOMBIE HORDE INCOMING!</b>\n\n"
            "☣️ Boss: <b>MUTANT HORDE</b>\n"
            "❤️ HP: <b>5,000</b>\n"
            "⏱️ Time: <b>5 minutes</b>\n\n"
            "Join the raid and attack together!",
            reply_markup=raid_keyboard(chat_id),
        )
        asyncio.create_task(raid_timer(app, db, chat_id, now + RAID_DURATION))

    @app.on_callback_query(filters.regex(r"^raid:join:(-?\d+)$"))
    async def raid_join(_, q):
        chat_id = int(q.matches[0].group(1))
        if not q.message or q.message.chat.id != chat_id:
            await q.answer("Invalid raid.", show_alert=True); return
        raid = await db.get_raid(chat_id)
        if not raid or raid.get("status") == "finished":
            await q.answer("No active raid.", show_alert=True); return
        if int(time.time()) >= raid["ends_at"]:
            await finish_raid(app, db, chat_id)
            await q.answer("Raid ended.", show_alert=True); return
        uid = q.from_user.id
        if uid not in raid["participants"]:
            raid["participants"].append(uid)
            raid["damage"][str(uid)] = 0
            await db.set_raid(chat_id, raid)
        await q.answer("You joined the Horde raid!", show_alert=True)

    @app.on_callback_query(filters.regex(r"^raid:attack:(-?\d+)$"))
    async def raid_attack(_, q):
        chat_id = int(q.matches[0].group(1))
        if not q.message or q.message.chat.id != chat_id:
            await q.answer("Invalid raid.", show_alert=True); return
        raid = await db.get_raid(chat_id)
        if not raid or raid.get("status") == "finished":
            await q.answer("No active raid.", show_alert=True); return
        if int(time.time()) >= raid["ends_at"]:
            await finish_raid(app, db, chat_id)
            await q.answer("Raid ended.", show_alert=True); return
        uid = q.from_user.id
        if uid not in raid["participants"]:
            await q.answer("Join the raid first.", show_alert=True); return
        p = await db.get_player(uid, q.from_user.first_name, q.from_user.username or "")
        if p["energy"] < 5:
            await q.answer("Not enough energy.", show_alert=True); return
        damage = max(1, int(weapon_attack(p["weapon"]) * random.uniform(0.9, 1.25)))
        raid["boss_hp"] = max(0, raid["boss_hp"] - damage)
        raid["damage"][str(uid)] = raid["damage"].get(str(uid), 0) + damage
        await db.set_raid(chat_id, raid)
        await db.update_player(uid, {"$inc": {"energy": -5, "raid_damage": damage}})
        await q.answer(f"⚔️ You dealt {damage} damage!", show_alert=True)
        if raid["boss_hp"] <= 0:
            await finish_raid(app, db, chat_id)

    @app.on_callback_query(filters.regex(r"^raid:view:(-?\d+)$"))
    async def raid_view(_, q):
        chat_id = int(q.matches[0].group(1))
        if not q.message or q.message.chat.id != chat_id:
            await q.answer("Invalid raid.", show_alert=True); return
        raid = await db.get_raid(chat_id)
        if not raid or raid.get("status") == "finished":
            await q.answer("No active raid.", show_alert=True); return
        left = max(0, raid["ends_at"] - int(time.time()))
        await q.message.reply_text(
            f"☣️ <b>MUTANT HORDE</b>\n\n"
            f"❤️ HP: <b>{raid['boss_hp']:,}/{raid['max_hp']:,}</b>\n"
            f"👥 Players: <b>{len(raid['participants'])}</b>\n"
            f"⏱️ Remaining: <b>{left//60}:{left%60:02d}</b>",
            reply_markup=raid_keyboard(chat_id),
        )
        await q.answer()

    async def restore_raids():
        for raid in await db.get_active_raids():
            if raid.get("status") == "finished":
                continue
            chat_id = raid["chat_id"]
            if int(time.time()) >= raid.get("ends_at", 0):
                asyncio.create_task(finish_raid(app, db, chat_id))
            else:
                asyncio.create_task(raid_timer(app, db, chat_id, raid["ends_at"]))

    app._zombie_restore_raids = restore_raids

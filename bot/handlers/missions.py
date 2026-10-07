from datetime import datetime, timezone

from pyrogram import filters
from .common import btn, kb, back_home
from bot.game.engine import apply_xp

MISSIONS = {
    "daily_kill5": ("🧟 Daily: Kill 5 Zombies", "kills", "daily", 5, 500, 100),
    "daily_coins2k": ("💰 Daily: Earn 2,000 Coins", "coins", "daily", 2000, 700, 150),
    "weekly_kill50": ("💀 Weekly: Kill 50 Zombies", "kills", "weekly", 50, 5000, 750),
    "weekly_coins25k": ("🪙 Weekly: Earn 25,000 Coins", "coins", "weekly", 25000, 7000, 1000),
    "weekly_raid3": ("☣️ Weekly: Join 3 Raids", "raids", "weekly", 3, 3500, 500),
    "weekly_pvp5": ("⚔️ Weekly: Win 5 PvP Fights", "pvp_wins", "weekly", 5, 6000, 900),
}

def period_key(period):
    now = datetime.now(timezone.utc)
    if period == "daily":
        return now.strftime("%Y-%m-%d")
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

async def mission_doc(db, uid, key):
    title, event, period, target, coins, xp = MISSIONS[key]
    current = period_key(period)
    m = await db.db.missions.find_one({"user_id": uid, "kind": key})
    if not m:
        m = {"user_id": uid, "kind": key, "period_key": current, "progress": 0, "claimed": False}
        await db.db.missions.insert_one(m)
        return m
    if m.get("period_key") != current:
        await db.db.missions.update_one(
            {"user_id": uid, "kind": key},
            {"$set": {"period_key": current, "progress": 0, "claimed": False}},
        )
        m.update({"period_key": current, "progress": 0, "claimed": False})
    return m

async def record_progress(db, uid, event, amount):
    if amount <= 0:
        return
    for key, (_, mission_event, period, target, _, _) in MISSIONS.items():
        if mission_event != event:
            continue
        m = await mission_doc(db, uid, key)
        if not m.get("claimed"):
            await db.db.missions.update_one(
                {"user_id": uid, "kind": key, "period_key": period_key(period), "claimed": False},
                {"$inc": {"progress": amount}},
            )

def register(app, db):
    @app.on_callback_query(filters.regex(r"^home:missions$"))
    async def missions(_, q):
        await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        rows = []
        text = "🎯 <b>MISSIONS</b>\n\n"
        for key, (title, event, period, target, coins, xp) in MISSIONS.items():
            m = await mission_doc(db, q.from_user.id, key)
            progress = min(target, int(m.get("progress", 0)))
            claimed = m.get("claimed", False)
            tag = "☀️ Daily" if period == "daily" else "📅 Weekly"
            text += f"{tag} • {title}\n<b>{progress:,}/{target:,}</b> • 🎁 {coins:,} coins + {xp} XP\n\n"
            if progress >= target and not claimed:
                rows.append([btn(f"🟢 Claim • {title}", f"mission:claim:{key}")])
        rows.append([btn("🔵 🏠 Home", "home")])
        await q.message.edit_text(text, reply_markup=kb(rows))
        await q.answer()

    @app.on_callback_query(filters.regex(r"^mission:claim:(.+)$"))
    async def claim(_, q):
        key = q.matches[0].group(1)
        if key not in MISSIONS:
            await q.answer("Unknown mission.", show_alert=True)
            return
        title, event, period, target, coins, xp = MISSIONS[key]
        uid = q.from_user.id
        p = await db.get_player(uid, q.from_user.first_name, q.from_user.username or "")
        m = await mission_doc(db, uid, key)
        if int(m.get("progress", 0)) < target or m.get("claimed"):
            await q.answer("Mission not ready.", show_alert=True)
            return
        # Claim the mission atomically first so double-clicks cannot pay twice.
        claimed = await db.db.missions.update_one(
            {
                "user_id": uid,
                "kind": key,
                "period_key": period_key(period),
                "claimed": False,
                "progress": {"$gte": target},
            },
            {"$set": {"claimed": True}},
        )
        if claimed.modified_count != 1:
            await q.answer("Mission was already claimed.", show_alert=True)
            return
        new_xp, level, max_hp, max_energy, leveled = apply_xp(p, xp)
        await db.update_player(uid, {
            "$inc": {"coins": coins, "coins_earned": coins},
            "$set": {"xp": new_xp, "level": level, "max_hp": max_hp, "max_energy": max_energy},
        })
        level_text = f"\n🎉 Level Up → <b>{level}</b>" if leveled else ""
        await q.message.edit_text(
            f"🎉 <b>MISSION COMPLETE!</b>\n\n{title}\n"
            f"💰 +{coins:,} coins\n⭐ +{xp} XP{level_text}",
            reply_markup=back_home(),
        )
        await q.answer()

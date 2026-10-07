import random
from datetime import datetime, timezone
from pyrogram import filters
from .common import btn, kb, back_home
from .missions import record_progress
from bot.game.data import LOCATIONS
from bot.game.engine import make_zombie, player_attack, player_defense, random_loot, apply_xp, location_info, regen_energy

COMBAT_TIMEOUT = 30 * 60


def home_text(p):
    return (
        "🎮 <b>Survival Menu</b>\n\n"
        f"❤️ HP: {p['hp']}/{p['max_hp']}\n"
        f"⚡ Energy: {p['energy']}/{p['max_energy']}\n"
        f"💰 Coins: {p['coins']:,}"
    )


def fight_text(c, p):
    z = c["zombie"]
    return (
        f"🧟 <b>{z['name']}</b>\n\n"
        f"☣️ Zombie HP: <b>{z['hp']}/{z['max_hp']}</b>\n"
        f"❤️ Your HP: <b>{p['hp']}/{p['max_hp']}</b>\n"
        f"⚡ Energy: <b>{p['energy']}/{p['max_energy']}</b>\n\n"
        "Choose your move."
    )


def fight_kb(uid):
    return kb([
        [btn("🟢 ⚔️ Attack", f"fight:{uid}:attack"), btn("🔵 🛡️ Defend", f"fight:{uid}:defend")],
        [btn("🟢 💊 Heal", f"fight:{uid}:heal"), btn("🔴 🏃 Escape", f"fight:{uid}:escape")],
    ])


async def load_combat(db, uid):
    c = await db.get_combat(uid)
    if not c:
        return None
    created = int(c.get("created_at", 0))
    if created and int(datetime.now(timezone.utc).timestamp()) - created > COMBAT_TIMEOUT:
        await db.delete_combat(uid)
        return None
    return c


def register(app, db):
    @app.on_callback_query(filters.regex(r"^home:play$"))
    async def play(_, q):
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        await q.message.edit_text(home_text(p), reply_markup=kb([
            [btn("🟢 🧟 Hunt Zombie", "game:hunt"), btn("🔵 🗺️ Explore", "home:explore")],
            [btn("🔴 ⬅️ Back", "home")],
        ]))
        await q.answer()

    @app.on_callback_query(filters.regex(r"^game:hunt$"))
    async def hunt(_, q):
        uid = q.from_user.id
        p = await db.get_player(uid, q.from_user.first_name, q.from_user.username or "")
        gain = regen_energy(p)
        if gain:
            p["energy"] += gain
            await db.update_player(uid, {"$inc": {"energy": gain}, "$set": {"last_energy": datetime.now(timezone.utc)}})
        if p["energy"] < 10:
            await q.answer("⚠️ Not enough energy. Wait for regeneration.", show_alert=True)
            return
        await db.update_player(uid, {"$inc": {"energy": -10}, "$set": {"last_energy": datetime.now(timezone.utc)}})
        p["energy"] -= 10
        zombie = make_zombie(p["level"])
        combat = {"zombie": zombie, "defending": False, "created_at": int(datetime.now(timezone.utc).timestamp())}
        await db.set_combat(uid, combat)
        await q.message.edit_text(f"🧟 <b>ENCOUNTER!</b>\n\n{fight_text(combat, p)}", reply_markup=fight_kb(uid))
        await q.answer()

    @app.on_callback_query(filters.regex(r"^fight:(\d+):(attack|defend|heal|escape)$"))
    async def fight(_, q):
        uid = q.from_user.id
        if uid != int(q.matches[0].group(1)):
            await q.answer("This fight belongs to another survivor.", show_alert=True)
            return
        c = await load_combat(db, uid)
        if not c:
            await q.answer("Fight expired. Start another hunt.", show_alert=True)
            return
        p = await db.get_player(uid, q.from_user.first_name, q.from_user.username or "")
        action = q.matches[0].group(2)
        z = c["zombie"]

        if action == "escape":
            # Escaping ends the encounter without granting kill/coin rewards.
            await db.delete_combat(uid)
            await q.message.edit_text("🏃 You escaped the encounter safely. No rewards were earned.", reply_markup=back_home())
            await q.answer()
            return

        if action == "heal":
            inv = p.setdefault("inventory", {})
            if inv.get("medkit", 0) <= 0:
                await q.answer("❌ No medkit.", show_alert=True)
                return
            heal = min(35, max(0, p["max_hp"] - p["hp"]))
            if heal <= 0:
                await q.answer("❤️ Your HP is already full.", show_alert=True)
                return
            damage = max(1, z["attack"] - player_defense(p) // 4)
            new_hp = max(1, p["hp"] + heal - damage)
            await db.update_player(uid, {"$set": {"hp": new_hp}, "$inc": {"inventory.medkit": -1}})
            p["hp"] = new_hp
            await q.message.edit_text(
                f"💊 Healed <b>{heal}</b> HP.\n"
                f"🧟 Enemy hit you for <b>{damage}</b>.\n\n{fight_text(c, p)}",
                reply_markup=fight_kb(uid),
            )
            await q.answer()
            return

        if action == "defend":
            damage = max(1, (z["attack"] // 2) - player_defense(p) // 5)
            new_hp = max(1, p["hp"] - damage)
            c["defending"] = True
            await db.set_combat(uid, c)
            await db.update_player(uid, {"$set": {"hp": new_hp}})
            p["hp"] = new_hp
            await q.message.edit_text(
                f"🛡️ You defend. Zombie deals only <b>{damage}</b> damage.\n\n{fight_text(c, p)}",
                reply_markup=fight_kb(uid),
            )
            await q.answer()
            return

        damage = player_attack(p)
        z["hp"] -= damage
        if z["hp"] <= 0:
            loot = random_loot(p["level"])
            xp, level, max_hp, max_energy, levels = apply_xp(p, z["xp"])
            inc = {"kills": 1, "coins": z["coins"], "coins_earned": z["coins"]}
            inc.update({f"inventory.{k}": v for k, v in loot.items()})
            await db.update_player(uid, {
                "$inc": inc,
                "$set": {
                    "xp": xp, "level": level, "max_hp": max_hp, "max_energy": max_energy,
                    "hp": max_hp if levels else p["hp"], "energy": p["energy"],
                },
            })
            await db.delete_combat(uid)
            loot_text = " ".join(f"{k} ×{v}" for k, v in loot.items())
            level_text = f"\n🎉 <b>LEVEL UP!</b> → {level}" if levels else ""
            await q.message.edit_text(
                f"💀 <b>ZOMBIE DEFEATED!</b>\n\n"
                f"⚔️ Damage: <b>{damage}</b>\n"
                f"⭐ XP: <b>+{z['xp']}</b>\n"
                f"💰 Coins: <b>+{z['coins']}</b>\n"
                f"🎁 Loot: <b>{loot_text}</b>{level_text}",
                reply_markup=kb([
                    [btn("🟢 🧟 Hunt Again", "game:hunt"), btn("🔵 🎒 Inventory", "home:inventory")],
                    [btn("🔵 🏠 Home", "home")],
                ]),
            )
            await q.answer()
            return

        damage_taken = max(1, z["attack"] - player_defense(p) // 4)
        if c.get("defending"):
            damage_taken = max(1, damage_taken // 2)
            c["defending"] = False
        p["hp"] -= damage_taken
        if p["hp"] <= 0:
            p["hp"] = 1
            await db.update_player(uid, {"$set": {"hp": 1}})
            await db.delete_combat(uid)
            await q.message.edit_text(
                f"☠️ <b>YOU WERE OVERWHELMED</b>\n\n"
                f"You dealt {damage} damage, but the zombie hit for {damage_taken}.\n"
                "Your HP has been saved at 1. Heal before your next fight.",
                reply_markup=back_home(),
            )
            await q.answer()
            return
        c["zombie"] = z
        await db.update_player(uid, {"$set": {"hp": p["hp"]}})
        await db.set_combat(uid, c)
        await q.message.edit_text(
            f"⚔️ You dealt <b>{damage}</b> damage.\n"
            f"🧟 Zombie hit you for <b>{damage_taken}</b>.\n\n{fight_text(c, p)}",
            reply_markup=fight_kb(uid),
        )
        await q.answer()

    @app.on_callback_query(filters.regex(r"^home:explore$"))
    async def explore(_, q):
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        locs = location_info(p["level"])
        rows = [[btn(f"{icon} {name} • Lv {req}", f"explore:{i}")] for i, (icon, name, req, mult) in enumerate(LOCATIONS) if req <= p["level"]]
        rows.append([btn("🔵 ⬅️ Back", "home:play"), btn("🔵 🏠 Home", "home")])
        await q.message.edit_text("🗺️ <b>EXPLORE</b>\n\nChoose a location. Higher areas give better loot.", reply_markup=kb(rows))
        await q.answer()

    @app.on_callback_query(filters.regex(r"^explore:(\d+)$"))
    async def do_explore(_, q):
        idx = int(q.matches[0].group(1))
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        if idx >= len(LOCATIONS):
            await q.answer("Invalid location.", show_alert=True); return
        icon, name, req, mult = LOCATIONS[idx]
        if p["level"] < req:
            await q.answer(f"Requires level {req}.", show_alert=True); return
        if p["energy"] < 15:
            await q.answer("Not enough energy.", show_alert=True); return
        await db.update_player(q.from_user.id, {"$inc": {"energy": -15}, "$set": {"last_energy": datetime.now(timezone.utc)}})
        if random.random() < 0.72:
            z = make_zombie(p["level"], mult)
            combat = {"zombie": z, "defending": False, "created_at": int(datetime.now(timezone.utc).timestamp())}
            await db.set_combat(q.from_user.id, combat)
            p["energy"] -= 15
            await q.message.edit_text(
                f"{icon} <b>{name}</b>\n\n🚨 You found <b>{z['name']}</b>!\n\n{fight_text(combat, p)}",
                reply_markup=fight_kb(q.from_user.id),
            )
        else:
            coins = random.randint(50, 250) * mult
            scrap = random.randint(1, 4) * mult
            await db.update_player(q.from_user.id, {"$inc": {"coins": coins, "coins_earned": coins, "inventory.scrap": scrap}})
            await record_progress(db, q.from_user.id, "coins", coins)
            await q.message.edit_text(
                f"{icon} <b>{name}</b>\n\n🎁 <b>Lucky find!</b>\n💰 +{coins} coins\n🔩 Scrap ×{scrap}",
                reply_markup=back_home(),
            )
        await q.answer()

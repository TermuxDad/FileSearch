from pyrogram import filters
from .common import btn, kb, back_home
from bot.game.data import WEAPONS, ARMOR
from bot.game.engine import weapon_upgrade_cost, armor_upgrade_cost

def register(app, db):
    @app.on_callback_query(filters.regex(r"^home:shop$"))
    async def shop(_, q):
        await q.message.edit_text(
            "🏪 <b>SHOP</b>\n\nChoose a category:",
            reply_markup=kb([
                [btn("🔫 Weapons", "shop:weapons"), btn("🛡️ Armor", "shop:armor")],
                [btn("💊 Medical", "shop:medical")],
                [btn("⬆️ Weapon Upgrade", "shop:upgrade:weapon"), btn("⬆️ Armor Upgrade", "shop:upgrade:armor")],
                [btn("🔵 🏠 Home", "home")],
            ]),
        )
        await q.answer()

    @app.on_callback_query(filters.regex(r"^shop:weapons(?::(\d+))?$"))
    async def weapons(_, q):
        page = int(q.matches[0].group(1) or 1)
        items = list(WEAPONS.items())
        per_page = 8
        pages = max(1, (len(items) + per_page - 1) // per_page)
        page = max(1, min(page, pages))
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        rows = []
        start_i = (page - 1) * per_page
        for key, (name, attack, price) in items[start_i:start_i + per_page]:
            owned = p["inventory"].get(key, 0) > 0
            label = f"{name} +{attack} • {'OWNED' if owned else f'💰 {price:,}'}"
            rows.append([btn(label[:58], f"buy:w:{key}")])
        nav = []
        if page > 1:
            nav.append(btn("🔵 ◀️ Prev", f"shop:weapons:{page-1}"))
        if page < pages:
            nav.append(btn("🔵 Next ▶️", f"shop:weapons:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([btn(f"🔵 📄 Page {page}/{pages}", "shop:weapons:1")])
        rows.append([btn("🔵 ⬅️ Shop", "home:shop")])
        await q.message.edit_text(
            f"🔫 <b>WEAPONS</b> — Page {page}/{pages}\n\nBuy a weapon to automatically equip it.",
            reply_markup=kb(rows),
        )
        await q.answer()

    @app.on_callback_query(filters.regex(r"^shop:armor(?::(\d+))?$"))
    async def armor(_, q):
        page = int(q.matches[0].group(1) or 1)
        items = list(ARMOR.items())
        per_page = 8
        pages = max(1, (len(items) + per_page - 1) // per_page)
        page = max(1, min(page, pages))
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        rows = []
        start_i = (page - 1) * per_page
        for key, (name, defense, price) in items[start_i:start_i + per_page]:
            owned = p["inventory"].get(key, 0) > 0
            label = f"{name} +{defense} DEF • {'OWNED' if owned else f'💰 {price:,}'}"
            rows.append([btn(label[:58], f"buy:a:{key}")])
        nav = []
        if page > 1:
            nav.append(btn("🔵 ◀️ Prev", f"shop:armor:{page-1}"))
        if page < pages:
            nav.append(btn("🔵 Next ▶️", f"shop:armor:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([btn(f"🔵 📄 Page {page}/{pages}", "shop:armor:1")])
        rows.append([btn("🔵 ⬅️ Shop", "home:shop")])
        await q.message.edit_text(
            f"🛡️ <b>ARMOR</b> — Page {page}/{pages}\n\nBuy armor to automatically equip it.",
            reply_markup=kb(rows),
        )
        await q.answer()

    @app.on_callback_query(filters.regex(r"^shop:medical$"))
    async def medical(_, q):
        await q.message.edit_text(
            "💊 <b>MEDICAL</b>\n\nMedkit restores up to 35 HP during combat.\nPrice: 250 coins.",
            reply_markup=kb([
                [btn("🟢 💊 Buy Medkit — 250", "buy:medkit")],
                [btn("🔵 ⬅️ Shop", "home:shop")],
            ]),
        )
        await q.answer()

    @app.on_callback_query(filters.regex(r"^buy:w:(.+)$"))
    async def buy_weapon(_, q):
        key = q.matches[0].group(1)
        if key not in WEAPONS:
            await q.answer("Unknown item.", show_alert=True); return
        name, attack, price = WEAPONS[key]
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        if p["inventory"].get(key, 0) > 0:
            await db.update_player(q.from_user.id, {"$set": {"weapon": key}})
            await q.answer("Equipped!", show_alert=True); return
        result = await db.db.players.update_one(
            {"user_id": q.from_user.id, "coins": {"$gte": price}, f"inventory.{key}": {"$not": {"$gt": 0}}},
            {"$inc": {"coins": -price, f"inventory.{key}": 1}, "$set": {"weapon": key}},
        )
        if result.modified_count != 1:
            await q.answer("Not enough coins or item was just purchased.", show_alert=True); return
        await q.answer(f"Purchased {name}!", show_alert=True)
        await q.message.edit_text(f"🟢 <b>{name} equipped!</b>\nAttack: +{attack}", reply_markup=back_home())

    @app.on_callback_query(filters.regex(r"^buy:a:(.+)$"))
    async def buy_armor(_, q):
        key = q.matches[0].group(1)
        if key not in ARMOR:
            await q.answer("Unknown item.", show_alert=True); return
        name, defense, price = ARMOR[key]
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        if p["inventory"].get(key, 0) > 0:
            await db.update_player(q.from_user.id, {"$set": {"armor": key}})
            await q.answer("Equipped!", show_alert=True); return
        result = await db.db.players.update_one(
            {"user_id": q.from_user.id, "coins": {"$gte": price}, f"inventory.{key}": {"$not": {"$gt": 0}}},
            {"$inc": {"coins": -price, f"inventory.{key}": 1}, "$set": {"armor": key}},
        )
        if result.modified_count != 1:
            await q.answer("Not enough coins or item was just purchased.", show_alert=True); return
        await q.answer(f"Purchased {name}!", show_alert=True)
        await q.message.edit_text(f"🟢 <b>{name} equipped!</b>\nDefense: +{defense}", reply_markup=back_home())

    @app.on_callback_query(filters.regex(r"^buy:medkit$"))
    async def buy_medkit(_, q):
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        result = await db.db.players.update_one(
            {"user_id": q.from_user.id, "coins": {"$gte": 250}},
            {"$inc": {"coins": -250, "inventory.medkit": 1}},
        )
        if result.modified_count != 1:
            await q.answer("Not enough coins.", show_alert=True); return
        await q.answer("Medkit purchased!", show_alert=True)

from pyrogram import filters
from .common import btn, kb


def register(app, db):
    @app.on_callback_query(filters.regex(r"^home:leaderboard$"))
    async def leaderboard(_, q):
        players = await db.leaderboard(10)
        text = "🏆 <b>GLOBAL SURVIVOR LEADERBOARD</b>\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, p in enumerate(players, 1):
            medal = medals[i-1] if i <= 3 else f"<b>{i}.</b>"
            text += f"{medal} {p.get('name','Survivor')} — Lv {p['level']} • {p['xp']} XP • 💀 {p.get('kills',0)}\n"
        if not players:
            text += "No survivors yet."

        rows = []
        chat = q.message.chat
        if chat and chat.type in ("group", "supergroup"):
            try:
                ids = []
                async for member in app.get_chat_members(chat.id, limit=200):
                    if member.user and not member.user.is_bot:
                        ids.append(member.user.id)
                group_players = await db.group_leaderboard(ids, 10)
                text += "\n\n👥 <b>GROUP LEADERBOARD</b>\n\n"
                for i, p in enumerate(group_players, 1):
                    medal = medals[i-1] if i <= 3 else f"<b>{i}.</b>"
                    text += f"{medal} {p.get('name','Survivor')} — Lv {p['level']} • {p['xp']} XP\n"
            except Exception:
                text += "\n\n👥 <b>GROUP LEADERBOARD</b>\n\nUnable to read group members right now."

        rows.append([btn("🔵 🏠 Home", "home")])
        await q.message.edit_text(text, reply_markup=kb(rows))
        await q.answer()

    @app.on_callback_query(filters.regex(r"^home:inventory$"))
    async def inventory(_, q):
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        inv = p.get("inventory", {})
        text = "🎒 <b>INVENTORY</b>\n\n"
        shown = 0
        for key, count in inv.items():
            if count:
                text += f"• <code>{key}</code> × {count}\n"
                shown += 1
        if not shown:
            text += "Your inventory is empty."
        text += f"\n🔫 Equipped: <code>{p['weapon']}</code>\n🛡️ Equipped: <code>{p['armor']}</code>"
        await q.message.edit_text(text, reply_markup=kb([[btn("🔵 🏠 Home", "home")]]))
        await q.answer()

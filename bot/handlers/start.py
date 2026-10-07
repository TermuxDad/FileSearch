from pyrogram import filters
from .common import home_kb, safe_name

def register(app, db):
    @app.on_message(filters.command(["start", "menu"]))
    async def start(_, message):
        p = await db.get_player(
            message.from_user.id,
            safe_name(message.from_user),
            message.from_user.username or "",
        )
        text = (
            "🧟 <b>ZOMBIE SURVIVAL</b>\n\n"
            "The world has fallen. Survive, grow stronger and "
            "fight the Horde with your group.\n\n"
            f"❤️ HP: <b>{p['hp']}/{p['max_hp']}</b>\n"
            f"⚡ Energy: <b>{p['energy']}/{p['max_energy']}</b>\n"
            f"💰 Coins: <b>{p['coins']:,}</b>\n"
            f"⭐ Level: <b>{p['level']}</b>\n\n"
            "Choose an action below."
        )
        await message.reply_text(text, reply_markup=home_kb())

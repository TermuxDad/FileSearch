from pyrogram import filters
from .common import home_kb,safe_name

def register(app,db):
    @app.on_message(filters.command(['start','menu']))
    async def start(_,message):
        p=await db.get_player(message.from_user.id,safe_name(message.from_user),message.from_user.username or '')
        await message.reply_text(f'''🧟 <b>ZOMBIE SURVIVAL V2</b>\n\nThe apocalypse is no longer just zombies. Survive the Horde, hunt rivals, build a clan and become the most wanted survivor.\n\n❤️ HP: <b>{p['hp']}/{p['max_hp']}</b>\n⚡ Energy: <b>{p['energy']}/{p['max_energy']}</b>\n💰 Coins: <b>{p['coins']:,}</b>\n⭐ Level: <b>{p['level']}</b>\n⚔️ PvP Wins: <b>{p.get('pvp_wins',0)}</b>\n☠️ Bounty: <b>{p.get('bounty',0):,}</b>\n🩸 Bloodlust: <b>{p.get('bloodlust',0)}%</b>\n\nChoose your action.''',reply_markup=home_kb())

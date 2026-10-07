from pyrogram import filters
from .common import back_home
from bot.game.data import weapon_attack,armor_defense
from bot.game.engine import xp_for_level,regen_energy

def profile_text(p):
    return (f"👤 <b>{p['name']}</b>\n⭐ Level: <b>{p['level']}</b>\n✨ XP: <b>{p['xp']}/{xp_for_level(p['level'])}</b>\n\n"
            f"❤️ HP: <b>{p['hp']}/{p['max_hp']}</b>\n⚡ Energy: <b>{p['energy']}/{p['max_energy']}</b>\n💰 Coins: <b>{p['coins']:,}</b>\n"
            f"💀 Zombie Kills: <b>{p.get('kills',0):,}</b>\n⚔️ PvP Wins: <b>{p.get('pvp_wins',0):,}</b> / Losses <b>{p.get('pvp_losses',0):,}</b>\n"
            f"🔥 PvP Streak: <b>{p.get('pvp_streak',0)}</b> (Best {p.get('best_streak',0)})\n☠️ Bounty: <b>{p.get('bounty',0):,}</b>\n⭐ Reputation: <b>{p.get('reputation',0):,}</b>\n"
            f"🩸 Bloodlust: <b>{p.get('bloodlust',0)}%</b>\n☠️ Rival: <b>{p.get('rival_user_id') or 'None'}</b>\n\n"
            f"🔫 Weapon: <b>{p['weapon']}</b> (+{weapon_attack(p['weapon'])}) • Upgrade Lv {p.get('weapon_upgrade',0)}\n"
            f"🛡️ Armor: <b>{p['armor']}</b> (+{armor_defense(p['armor'])} DEF) • Upgrade Lv {p.get('armor_upgrade',0)}")

def register(app,db):
    @app.on_callback_query(filters.regex(r'^(home:profile|profile)$'))
    async def profile(_,q):
        p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or '')
        gain=regen_energy(p)
        if gain:
            from datetime import datetime,timezone
            await db.update_player(q.from_user.id,{'$inc':{'energy':gain},'$set':{'last_energy':datetime.now(timezone.utc)}}); p['energy']+=gain
        await q.message.edit_text(profile_text(p),reply_markup=back_home()); await q.answer()

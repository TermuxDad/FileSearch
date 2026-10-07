from pyrogram import filters
from .common import back_home

def register_help(app,db):
    @app.on_message(filters.command('help'))
    async def help_command(_,m):
        await m.reply_text('''❓ <b>ZOMBIE SURVIVAL V2</b>\n\n🎮 /start — open the game\n⚔️ /duel — reply to a player to challenge them\n☠️ /bounty AMOUNT — place a bounty by replying to a player\n👑 /clan create NAME — create a clan\n👑 /clan join ID — join a clan\n💰 /clan donate AMOUNT — fund your clan bank\n🏰 /clanwar ID — declare clan war\n⚔️ /clanwarattack — strike during an active war\n☣️ /raid — start a group Horde raid\n🛠️ /stats — owner stats\n🗄️ /backup — owner backup\n\n<b>PvP:</b> duels affect wins, streaks, reputation, bounties and rivalries.\n<b>Clans:</b> capture territories and fight wars.\n<b>Events:</b> a rotating event cache changes every 6 hours.\n<b>Safety:</b> all losses are bounded in-game coins/items; no real-money stakes.''',reply_markup=back_home())
    @app.on_callback_query(filters.regex(r'^home:help$'))
    async def help_menu(_,q):
        await q.message.edit_text('''❓ <b>HOW TO PLAY</b>\n\n🧟 Hunt zombies for XP, coins and loot.\n🗺️ Explore higher zones for stronger enemies.\n⚔️ Duel other players with /duel.\n☠️ Put bounties on rivals with /bounty.\n👑 Build a clan, capture territories and start wars.\n🌑 Check Events for rotating rewards.\n☣️ Use /raid in groups for cooperative Horde fights.\n⬆️ Upgrade weapons and armor with coins + scrap.\n\nYour progress is stored in MongoDB and included in disaster-recovery backups.''',reply_markup=back_home()); await q.answer()
    @app.on_callback_query(filters.regex(r'^home$'))
    async def home(_,q):
        from .common import home_kb
        p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or '')
        await q.message.edit_text(f"🧟 <b>ZOMBIE SURVIVAL V2</b>\n\n❤️ {p['hp']}/{p['max_hp']}   ⚡ {p['energy']}/{p['max_energy']}\n💰 {p['coins']:,}   ⭐ Lv {p['level']}\n☠️ Bounty {p.get('bounty',0):,}\n\nChoose your next move.",reply_markup=home_kb()); await q.answer()
    @app.on_callback_query(filters.regex(r'^home:daily$'))
    async def daily(_,q):
        from datetime import datetime,timezone
        from .missions import record_progress
        p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or ''); last=p.get('last_daily'); now=datetime.now(timezone.utc)
        if last and last.tzinfo is None: last=last.replace(tzinfo=timezone.utc)
        if last and last.date()==now.date(): await q.message.edit_text("🎁 <b>DAILY REWARD</b>\n\nAlready claimed today.",reply_markup=back_home()); await q.answer(); return
        await db.update_player(q.from_user.id,{'$inc':{'coins':1000,'coins_earned':1000,'energy':25},'$set':{'last_daily':now}}); await record_progress(db,q.from_user.id,'coins',1000)
        await q.message.edit_text('🎉 <b>DAILY REWARD CLAIMED!</b>\n\n💰 +1,000 coins\n⚡ +25 energy',reply_markup=back_home()); await q.answer()

from pyrogram import filters
from .common import btn,kb

def register(app,db):
    @app.on_callback_query(filters.regex(r'^home:leaderboard$'))
    async def leaderboard(_,q):
        players=await db.leaderboard(10); text='🏆 <b>GLOBAL LEADERBOARD</b>\n\n'; medals=['🥇','🥈','🥉']
        for i,p in enumerate(players,1): text+=f"{medals[i-1] if i<=3 else str(i)+'.'} <b>{p.get('name','Survivor')}</b> — Lv {p.get('level',1)} • XP {p.get('xp',0)} • 💀 {p.get('kills',0)}\n"
        text+='\n⚔️ <b>TOP PVP</b>\n\n'; pvp=await db.db.players.find({}).sort([('pvp_wins',-1),('best_streak',-1)]).limit(5).to_list(length=5)
        for i,p in enumerate(pvp,1): text+=f"{i}. {p.get('name','Survivor')} — ⚔️ {p.get('pvp_wins',0)} wins • 🔥 {p.get('best_streak',0)} streak\n"
        if q.message.chat and q.message.chat.type in ('group','supergroup'):
            try:
                ids=[]
                async for member in app.get_chat_members(q.message.chat.id,limit=200):
                    if member.user and not member.user.is_bot: ids.append(member.user.id)
                gp=await db.group_leaderboard(ids,10); text+='\n👥 <b>GROUP LEADERBOARD</b>\n\n'
                for i,p in enumerate(gp,1): text+=f'{i}. {p.get("name","Survivor")} — Lv {p.get("level",1)} • XP {p.get("xp",0)}\n'
            except Exception: text+='\n👥 Group leaderboard unavailable right now.\n'
        await q.message.edit_text(text,reply_markup=kb([[btn('🔴 ☠️ Most Wanted','home:wanted')],[btn('🔵 🏠 Home','home')]])); await q.answer()
    @app.on_callback_query(filters.regex(r'^home:inventory$'))
    async def inventory(_,q):
        p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or ''); inv=p.get('inventory',{}); text='🎒 <b>INVENTORY</b>\n\n'
        for key,count in inv.items():
            if count: text+=f'• <code>{key}</code> × {count}\n'
        text+=f"\n🔫 Equipped: <code>{p['weapon']}</code>\n🛡️ Equipped: <code>{p['armor']}</code>\n🔩 Scrap: <b>{inv.get('scrap',0)}</b>\n💊 Medkits: <b>{inv.get('medkit',0)}</b>"
        await q.message.edit_text(text,reply_markup=kb([[btn('🔵 🏪 Shop','home:shop'),btn('🔵 🏠 Home','home')]])); await q.answer()

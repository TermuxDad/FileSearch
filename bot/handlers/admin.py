from pyrogram import filters

def register(app,db,config):
    def owner(uid): return uid in config.OWNER_IDS
    @app.on_message(filters.command('stats') & filters.private)
    async def stats(_,m):
        if not owner(m.from_user.id): return
        await m.reply_text(f'🛠️ <b>ADMIN STATS</b>\n\n👥 Players: <b>{await db.count_players():,}</b>\n⚔️ PvP fights: <b>{await db.db.pvp_fights.count_documents({}):,}</b>\n👑 Clans: <b>{await db.db.clans.count_documents({}):,}</b>')
    @app.on_message(filters.command('givecoins') & filters.private)
    async def givecoins(_,m):
        if not owner(m.from_user.id): return
        parts=m.text.split()
        if len(parts)!=3 or not parts[1].isdigit() or not parts[2].isdigit(): await m.reply_text('Usage: /givecoins USER_ID AMOUNT'); return
        uid,amount=int(parts[1]),int(parts[2])
        if amount<1: await m.reply_text('Amount must be positive.'); return
        p=await db.get_player(uid)
        if not p: await m.reply_text('Player not found.'); return
        await db.update_player(uid,{'$inc':{'coins':amount,'coins_earned':amount}}); await m.reply_text('✅ Coins added.')
    @app.on_message(filters.command('setlevel') & filters.private)
    async def setlevel(_,m):
        if not owner(m.from_user.id): return
        parts=m.text.split()
        if len(parts)!=3 or not parts[1].isdigit() or not parts[2].isdigit(): await m.reply_text('Usage: /setlevel USER_ID LEVEL'); return
        uid,level=int(parts[1]),max(1,min(1000,int(parts[2]))); p=await db.get_player(uid)
        await db.update_player(uid,{'$set':{'level':level,'xp':0,'max_hp':100+(level-1)*8,'max_energy':100+(level-1)*3,'hp':100+(level-1)*8}}); await m.reply_text('✅ Level updated.')
    @app.on_message(filters.command('heal') & filters.private)
    async def heal(_,m):
        if not owner(m.from_user.id): return
        parts=m.text.split()
        if len(parts)!=2 or not parts[1].isdigit(): await m.reply_text('Usage: /heal USER_ID'); return
        uid=int(parts[1]); p=await db.get_player(uid)
        await db.update_player(uid,{'$set':{'hp':p['max_hp'],'energy':p['max_energy'],'injury_until':None}}); await m.reply_text('❤️ Player fully healed.')

import time, secrets, re
from pyrogram import filters
from .common import btn,kb,back_home

TERRITORIES=[
 ('graveyard','☠️ Graveyard',1000),('hospital','🏥 Dead Hospital',1500),('factory','🏭 Iron Factory',2200),
 ('bunker','🪖 Last Bunker',3000),('fortress','🏰 Zombie Fortress',4500),('wasteland','☣️ Toxic Wasteland',7000)
]

def clan_id(): return secrets.token_hex(4).upper()
def clean_name(s): return re.sub(r'[^A-Za-z0-9 _-]','',s).strip()[:24]

async def clan_for(db,uid):
    p=await db.get_player(uid)
    cid=p.get('clan_id') if p else None
    return await db.db.clans.find_one({'clan_id':cid}) if cid else None

def clan_text(c):
    if not c:return '👑 <b>CLAN</b>\n\nYou are not in a clan.\n\nCreate one with <code>/clan create NAME</code> or join with <code>/clan join CLAN_ID</code>.'
    return f"👑 <b>{c['name']}</b>\n\n🆔 <code>{c['clan_id']}</code>\n👥 Members: <b>{len(c.get('members',[]))}</b>\n💰 Bank: <b>{c.get('bank',0):,}</b>\n🏰 Territories: <b>{len(c.get('territories',[]))}</b>\n⚔️ War Wins: <b>{c.get('war_wins',0)}</b>"

def register(app,db):
    @app.on_callback_query(filters.regex(r'^home:clan$'))
    async def clan_menu(_,q):
        c=await clan_for(db,q.from_user.id)
        rows=[]
        if c: rows=[[btn('🟢 🏰 Territories','territories'),btn('🔴 ⚔️ Clan Wars','clanwars')],[btn('🔵 Leave Clan','clan:leave')]]
        else: rows=[[btn('🟢 📜 Clan Guide','clan:guide')]]
        rows.append([btn('🔵 🏠 Home','home')]); await q.message.edit_text(clan_text(c),reply_markup=kb(rows)); await q.answer()
    @app.on_callback_query(filters.regex(r'^clan:leave$'))
    async def clan_leave_button(_,q):
        p=await db.get_player(q.from_user.id); c=await clan_for(db,q.from_user.id)
        if not c: await q.answer('You are not in a clan.',show_alert=True); return
        if c['leader']==p['user_id'] and len(c.get('members',[]))>1: await q.answer('Leader must transfer leadership before leaving.',show_alert=True); return
        await db.db.clans.update_one({'clan_id':c['clan_id']},{'$pull':{'members':p['user_id']}}); await db.update_player(p['user_id'],{'$set':{'clan_id':None}})
        await q.message.edit_text('🏳️ <b>Left clan.</b>',reply_markup=back_home()); await q.answer()
    @app.on_callback_query(filters.regex(r'^clan:guide$'))
    async def guide(_,q): await q.message.edit_text('👑 <b>CLAN SYSTEM</b>\n\nCreate: <code>/clan create NAME</code>\nJoin: <code>/clan join CLAN_ID</code>\nLeave: <code>/clan leave</code>\nWar: challenge another clan from the Clan Wars menu.\n\nClans capture territories and build a shared bank.',reply_markup=back_home()); await q.answer()
    @app.on_message(filters.command('clan'))
    async def clan_cmd(_,m):
        if not m.from_user:return
        p=await db.get_player(m.from_user.id,m.from_user.first_name,m.from_user.username or '')
        parts=m.text.split(maxsplit=2)
        sub=parts[1].lower() if len(parts)>1 else 'info'
        if sub=='create':
            if p.get('clan_id'): await m.reply_text('❌ You are already in a clan.'); return
            if len(parts)<3: await m.reply_text('Usage: /clan create NAME'); return
            name=clean_name(parts[2])
            if len(name)<3: await m.reply_text('Clan name must be at least 3 characters.'); return
            cid=clan_id(); doc={'clan_id':cid,'name':name,'leader':p['user_id'],'members':[p['user_id']],'bank':0,'territories':[],'war_wins':0,'created_at':int(time.time())}
            try: await db.db.clans.insert_one(doc)
            except Exception: await m.reply_text('❌ Clan ID collision. Try again.'); return
            await db.update_player(p['user_id'],{'$set':{'clan_id':cid}}); await m.reply_text(f'👑 <b>CLAN CREATED</b>\n\n{name}\nID: <code>{cid}</code>\nShare the ID so friends can join.')
        elif sub=='join':
            if p.get('clan_id'): await m.reply_text('❌ Leave your current clan first.'); return
            if len(parts)<3: await m.reply_text('Usage: /clan join CLAN_ID'); return
            cid=parts[2].upper(); c=await db.db.clans.find_one({'clan_id':cid})
            if not c: await m.reply_text('❌ Clan not found.'); return
            if len(c.get('members',[]))>=50: await m.reply_text('❌ Clan is full.'); return
            res=await db.db.clans.update_one({'clan_id':cid,'members':{'$ne':p['user_id']}},{'$addToSet':{'members':p['user_id']}})
            if res.modified_count: await db.update_player(p['user_id'],{'$set':{'clan_id':cid}}); await m.reply_text(f'✅ Joined <b>{c["name"]}</b>.')
            else: await m.reply_text('❌ Could not join this clan.')
        elif sub=='donate':
            if len(parts)<3 or not parts[2].isdigit(): await m.reply_text('Usage: /clan donate AMOUNT'); return
            c=await clan_for(db,p['user_id'])
            amount=int(parts[2])
            if not c: await m.reply_text('Join a clan first.'); return
            if amount<100: await m.reply_text('Minimum donation is 100 coins.'); return
            res=await db.db.players.update_one({'user_id':p['user_id'],'coins':{'$gte':amount}},{'$inc':{'coins':-amount}})
            if res.modified_count!=1: await m.reply_text('Not enough coins.'); return
            await db.db.clans.update_one({'clan_id':c['clan_id']},{'$inc':{'bank':amount}})
            await m.reply_text(f'💰 Donated <b>{amount:,}</b> coins to {c["name"]}.')
        elif sub=='leave':
            c=await clan_for(db,p['user_id'])
            if not c: await m.reply_text('You are not in a clan.'); return
            if c['leader']==p['user_id'] and len(c.get('members',[]))>1: await m.reply_text('❌ Leader must transfer leadership before leaving.'); return
            await db.db.clans.update_one({'clan_id':c['clan_id']},{'$pull':{'members':p['user_id']}}); await db.update_player(p['user_id'],{'$set':{'clan_id':None}}); await m.reply_text('🏳️ You left the clan.')
        else: await m.reply_text(clan_text(await clan_for(db,p['user_id'])),reply_markup=kb([[btn('🔵 Clan Menu','home:clan')]]))
    @app.on_callback_query(filters.regex(r'^territories$'))
    async def territories(_,q):
        c=await clan_for(db,q.from_user.id)
        if not c: await q.answer('Join a clan first.',show_alert=True); return
        rows=[]; text='🏰 <b>TERRITORIES</b>\n\n'
        for tid,name,power in TERRITORIES:
            t=await db.db.territories.find_one({'territory_id':tid}); owner=t.get('clan_id') if t else None
            text+=f'{name} • Power {power:,} • Owner: <b>{owner or "Nobody"}</b>\n'
            if owner!=c['clan_id']: rows.append([btn(f'⚔️ Capture {name}',f'territory:{tid}')])
        rows.append([btn('🔵 ⬅️ Clan','home:clan'),btn('🔵 🏠 Home','home')]); await q.message.edit_text(text,reply_markup=kb(rows)); await q.answer()
    @app.on_callback_query(filters.regex(r'^territory:([a-z]+)$'))
    async def capture(_,q):
        tid=q.matches[0].group(1); c=await clan_for(db,q.from_user.id); spec=next((x for x in TERRITORIES if x[0]==tid),None)
        if not c or not spec: await q.answer('Invalid territory.',show_alert=True); return
        _,name,power=spec; t=await db.db.territories.find_one({'territory_id':tid}); owner=t.get('clan_id') if t else None
        if owner==c['clan_id']: await q.answer('Your clan already controls it.',show_alert=True); return
        if c.get('bank',0)<power//10: await q.answer(f'Clan bank needs {power//10:,} coins.',show_alert=True); return
        attack_power=len(c.get('members',[]))*250 + int((await db.get_player(q.from_user.id)).get('level',1))*100
        if attack_power < power: await q.answer(f'Capture failed. Need {power:,} clan power; current {attack_power:,}.',show_alert=True); return
        await db.db.territories.update_one({'territory_id':tid},{'$set':{'territory_id':tid,'clan_id':c['clan_id'],'captured_at':int(time.time())}},upsert=True)
        await db.db.clans.update_one({'clan_id':c['clan_id']},{'$inc':{'bank':-(power//10)},'$addToSet':{'territories':tid}})
        if owner: await db.db.clans.update_one({'clan_id':owner},{'$pull':{'territories':tid}})
        await q.message.edit_text(f'🏰 <b>TERRITORY CAPTURED</b>\n\n{name}\n👑 Clan: <b>{c["name"]}</b>\n💰 Cost: {power//10:,}',reply_markup=back_home()); await q.answer()
    @app.on_callback_query(filters.regex(r'^clanwars$'))
    async def wars(_,q):
        c=await clan_for(db,q.from_user.id)
        if not c: await q.answer('Join a clan first.',show_alert=True); return
        wars=await db.db.clan_wars.find({'$or':[{'a':c['clan_id']},{'b':c['clan_id']}],'status':'active'}).to_list(length=5)
        text='⚔️ <b>CLAN WARS</b>\n\n'
        rows=[]
        if wars:
            for w in wars:
                text+=f"{w['a']} {w['score'].get(w['a'],0)} — {w['score'].get(w['b'],0)} {w['b']}\n"
                rows.append([btn('⚔️ Strike for Clan',f"warstrike:{w['war_id']}")])
        else:text+='No active war.\n\nChallenge with <code>/clanwar CLAN_ID</code>.'
        rows.append([btn('🔵 ⬅️ Clan','home:clan'),btn('🔵 🏠 Home','home')]); await q.message.edit_text(text,reply_markup=kb(rows)); await q.answer()
    @app.on_message(filters.command('clanwar'))
    async def clanwar(_,m):
        c=await clan_for(db,m.from_user.id)
        if not c or c['leader']!=m.from_user.id: await m.reply_text('❌ Only a clan leader can start a war.'); return
        if len(m.command)<2: await m.reply_text('Usage: /clanwar CLAN_ID'); return
        target=await db.db.clans.find_one({'clan_id':m.command[1].upper()})
        if not target or target['clan_id']==c['clan_id']: await m.reply_text('❌ Invalid target clan.'); return
        wid=secrets.token_hex(5); w={'war_id':wid,'a':c['clan_id'],'b':target['clan_id'],'score':{c['clan_id']:0,target['clan_id']:0},'status':'pending','created_at':int(time.time()),'ends_at':int(time.time())+600}
        await db.db.clan_wars.insert_one(w); await m.reply_text(f'⚔️ <b>WAR DECLARED</b>\n{c["name"]} → {target["name"]}',reply_markup=kb([[btn('🟢 Accept War',f'waraccept:{wid}'),btn('🔴 Decline',f'wardecline:{wid}')]]))
    @app.on_callback_query(filters.regex(r'^waraccept:([0-9a-f]+)$'))
    async def war_accept(_,q):
        w=await db.db.clan_wars.find_one({'war_id':q.matches[0].group(1)}); c=await clan_for(db,q.from_user.id)
        if not w or not c or c['clan_id']!=w['b'] or w['status']!='pending': await q.answer('Invalid war.',show_alert=True); return
        await db.db.clan_wars.update_one({'war_id':w['war_id']},{'$set':{'status':'active','ends_at':int(time.time())+600}}); await q.message.edit_text('⚔️ <b>WAR STARTED!</b>\nUse /clanwarattack to strike for your clan.'); await q.answer()
    @app.on_callback_query(filters.regex(r'^wardecline:([0-9a-f]+)$'))
    async def war_decline(_,q):
        w=await db.db.clan_wars.find_one({'war_id':q.matches[0].group(1)}); c=await clan_for(db,q.from_user.id)
        if not w or not c or c['clan_id']!=w['b']: await q.answer('Invalid war.',show_alert=True); return
        await db.db.clan_wars.update_one({'war_id':w['war_id']},{'$set':{'status':'declined'}}); await q.message.edit_text('🏳️ War declined.',reply_markup=back_home()); await q.answer()
    @app.on_callback_query(filters.regex(r'^warstrike:([0-9a-f]+)$'))
    async def war_strike_button(_,q):
        c=await clan_for(db,q.from_user.id); wid=q.matches[0].group(1)
        if not c: await q.answer('Join a clan first.',show_alert=True); return
        w=await db.db.clan_wars.find_one({'war_id':wid,'status':'active'})
        if not w or c['clan_id'] not in (w['a'],w['b']): await q.answer('Invalid war.',show_alert=True); return
        if int(time.time())>=w['ends_at']:
            await db.db.clan_wars.update_one({'war_id':wid},{'$set':{'status':'finished'}}); await q.answer('War ended.',show_alert=True); return
        p=await db.get_player(q.from_user.id); damage=max(50,int(p['level']*35+p.get('weapon_upgrade',0)*25))
        await db.db.clan_wars.update_one({'war_id':wid},{'$inc':{f'score.{c["clan_id"]}':damage}})
        w=await db.db.clan_wars.find_one({'war_id':wid})
        my=w['score'].get(c['clan_id'],0); enemy=w['b'] if w['a']==c['clan_id'] else w['a']; enemy_score=w['score'].get(enemy,0)
        if my>=10000:
            await db.db.clan_wars.update_one({'war_id':wid},{'$set':{'status':'finished','winner':c['clan_id']}}); await db.db.clans.update_one({'clan_id':c['clan_id']},{'$inc':{'war_wins':1,'bank':5000}}); result='🏆 WAR WON! +5,000 clan bank.'
        else: result=f'⚔️ +{damage} war points. Score: {my} — {enemy_score}.'
        await q.answer(result,show_alert=True)
    @app.on_message(filters.command('clanwarattack'))
    async def war_attack(_,m):
        c=await clan_for(db,m.from_user.id)
        if not c: await m.reply_text('Join a clan first.'); return
        w=await db.db.clan_wars.find_one({'$or':[{'a':c['clan_id']},{'b':c['clan_id']}],'status':'active'})
        if not w: await m.reply_text('No active clan war.'); return
        if int(time.time())>=w['ends_at']:
            await db.db.clan_wars.update_one({'war_id':w['war_id']},{'$set':{'status':'finished'}}); await m.reply_text('⏱️ War ended.'); return
        p=await db.get_player(m.from_user.id); enemy=w['b'] if w['a']==c['clan_id'] else w['a']; damage=max(50,int((p['level']*35)+(p.get('weapon_upgrade',0)*25)))
        await db.db.clan_wars.update_one({'war_id':w['war_id']},{'$inc':{f'score.{c["clan_id"]}':damage}})
        w=await db.db.clan_wars.find_one({'war_id':w['war_id']})
        if w['score'].get(c['clan_id'],0)>=10000:
            await db.db.clan_wars.update_one({'war_id':w['war_id']},{'$set':{'status':'finished','winner':c['clan_id']}}); await db.db.clans.update_one({'clan_id':c['clan_id']},{'$inc':{'war_wins':1,'bank':5000}}); await m.reply_text('🏆 WAR WON! +5,000 clan bank.')
        else: await m.reply_text(f'⚔️ Clan strike landed for <b>{damage}</b> war points against {enemy}.')
    @app.on_callback_query(filters.regex(r'^home:event$'))
    async def event(_,q):
        period=int(time.time())//21600; events=[('blood_moon','🌑 BLOOD MOON','PvP wins grant +50% reputation.'),('supply_drop','📦 SUPPLY DROP','Exploration grants extra scrap.'),('horde_hour','🧟 HORDE HOUR','Zombie kills grant bonus coins.'),('bounty_rush','☠️ BOUNTY RUSH','Bounty claims grant bonus reputation.')]; key,title,desc=events[period%len(events)]
        claimed=await db.db.event_claims.find_one({'user_id':q.from_user.id,'period':str(period)})
        await q.message.edit_text(f'🌑 <b>LIVE EVENT</b>\n\n{title}\n{desc}\n\n⏳ Event cycle: <b>{period%len(events)+1}/4</b>',reply_markup=kb([[btn('🟢 Claim Event Cache',f'eventclaim:{period}:{key}')],[btn('🔵 🏠 Home','home')]])); await q.answer()
    @app.on_callback_query(filters.regex(r'^eventclaim:(\d+):([a-z_]+)$'))
    async def event_claim(_,q):
        period=int(q.matches[0].group(1)); key=q.matches[0].group(2); uid=q.from_user.id
        if period!=int(time.time())//21600: await q.answer('Event rotated. Open Events again.',show_alert=True); return
        try: await db.db.event_claims.insert_one({'user_id':uid,'period':str(period),'event':key,'created_at':int(time.time())})
        except Exception: await q.answer('You already claimed this event cache.',show_alert=True); return
        reward=1000+int((await db.get_player(uid))['level'])*100; await db.update_player(uid,{'$inc':{'coins':reward,'coins_earned':reward}}); await q.message.edit_text(f'🎁 <b>EVENT CACHE OPENED</b>\n\n💰 +{reward:,} coins',reply_markup=back_home()); await q.answer()

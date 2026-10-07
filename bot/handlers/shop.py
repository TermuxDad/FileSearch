from pyrogram import filters
from .common import btn,kb,back_home
from bot.game.data import WEAPONS, ARMOR
from bot.game.engine import weapon_upgrade_cost, armor_upgrade_cost

def register(app, db):
    @app.on_callback_query(filters.regex(r'^home:shop$'))
    async def shop(_,q):
        await q.message.edit_text('🏪 <b>APOCALYPSE SHOP</b>\n\nGear, medical supplies and permanent upgrades.',reply_markup=kb([
            [btn('🔫 Weapons','shop:weapons'),btn('🛡️ Armor','shop:armor')],
            [btn('💊 Medical','shop:medical')],
            [btn('⬆️ Weapon Upgrade','shop:upgrade:weapon'),btn('⬆️ Armor Upgrade','shop:upgrade:armor')],
            [btn('🔵 🏠 Home','home')]])); await q.answer()
    @app.on_callback_query(filters.regex(r'^shop:weapons(?::(\d+))?$'))
    async def weapons(_,q):
        page=int(q.matches[0].group(1) or 1); items=list(WEAPONS.items()); per=6; pages=max(1,(len(items)+per-1)//per); page=max(1,min(page,pages)); p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or '')
        rows=[]
        for key,(name,attack,price) in items[(page-1)*per:page*per]:
            owned=p.get('inventory',{}).get(key,0)>0; rows.append([btn(f'{name} +{attack} • '+('OWNED' if owned else f'💰 {price:,}')[:58],f'buy:w:{key}')])
        nav=[]
        if page>1: nav.append(btn('🔵 ◀️ Prev',f'shop:weapons:{page-1}'))
        if page<pages: nav.append(btn('🔵 Next ▶️',f'shop:weapons:{page+1}'))
        if nav: rows.append(nav)
        rows.append([btn(f'🔵 Page {page}/{pages}','shop:weapons:1'),btn('🔵 ⬅️ Shop','home:shop')]); await q.message.edit_text(f'🔫 <b>WEAPONS</b> — {page}/{pages}\n\nBuying a new weapon equips it automatically.',reply_markup=kb(rows)); await q.answer()
    @app.on_callback_query(filters.regex(r'^shop:armor(?::(\d+))?$'))
    async def armor(_,q):
        page=int(q.matches[0].group(1) or 1); items=list(ARMOR.items()); per=6; pages=max(1,(len(items)+per-1)//per); page=max(1,min(page,pages)); p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or '')
        rows=[]
        for key,(name,defense,price) in items[(page-1)*per:page*per]:
            owned=p.get('inventory',{}).get(key,0)>0; rows.append([btn(f'{name} +{defense} DEF • '+('OWNED' if owned else f'💰 {price:,}')[:58],f'buy:a:{key}')])
        nav=[]
        if page>1: nav.append(btn('🔵 ◀️ Prev',f'shop:armor:{page-1}'))
        if page<pages: nav.append(btn('🔵 Next ▶️',f'shop:armor:{page+1}'))
        if nav: rows.append(nav)
        rows.append([btn(f'🔵 Page {page}/{pages}','shop:armor:1'),btn('🔵 ⬅️ Shop','home:shop')]); await q.message.edit_text(f'🛡️ <b>ARMOR</b> — {page}/{pages}',reply_markup=kb(rows)); await q.answer()
    @app.on_callback_query(filters.regex(r'^shop:medical$'))
    async def medical(_,q): await q.message.edit_text('💊 <b>MEDICAL</b>\n\nMedkit restores up to 35 HP during zombie combat.\nPrice: 250 coins.',reply_markup=kb([[btn('🟢 💊 Buy Medkit — 250','buy:medkit')],[btn('🔵 ⬅️ Shop','home:shop')]])); await q.answer()
    @app.on_callback_query(filters.regex(r'^shop:upgrade:(weapon|armor)$'))
    async def upgrade_menu(_,q):
        kind=q.matches[0].group(1); p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or '')
        level=int(p.get(f'{kind}_upgrade',0)); cost=weapon_upgrade_cost(level) if kind=='weapon' else armor_upgrade_cost(level); label='Weapon' if kind=='weapon' else 'Armor'
        await q.message.edit_text(f'⬆️ <b>{label.upper()} UPGRADE</b>\n\nCurrent level: <b>{level}</b>\nNext cost: 💰 <b>{cost:,}</b> + 🔩 1 scrap\n\nEach level gives +8% power.',reply_markup=kb([[btn(f'🟢 Upgrade {label}','upgrade:'+kind)],[btn('🔵 ⬅️ Shop','home:shop')]])); await q.answer()
    @app.on_callback_query(filters.regex(r'^upgrade:(weapon|armor)$'))
    async def upgrade(_,q):
        kind=q.matches[0].group(1); p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or ''); field=f'{kind}_upgrade'; level=int(p.get(field,0)); cost=weapon_upgrade_cost(level) if kind=='weapon' else armor_upgrade_cost(level)
        res=await db.db.players.update_one({'user_id':p['user_id'],'coins':{'$gte':cost},'inventory.scrap':{'$gte':1},field:level},{'$inc':{'coins':-cost,'inventory.scrap':-1,field:1}})
        if res.modified_count!=1: await q.answer('Need more coins/scrap or upgrade changed.',show_alert=True); return
        await q.message.edit_text(f'⬆️ <b>{kind.title()} upgraded!</b>\n\nLevel: <b>{level+1}</b>\nPower bonus: <b>+{(level+1)*8}%</b>',reply_markup=back_home()); await q.answer('Upgrade successful!')
    @app.on_callback_query(filters.regex(r'^buy:w:(.+)$'))
    async def buy_weapon(_,q):
        key=q.matches[0].group(1)
        if key not in WEAPONS: await q.answer('Unknown item.',show_alert=True); return
        name,attack,price=WEAPONS[key]; p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or '')
        if p.get('inventory',{}).get(key,0)>0: await db.update_player(p['user_id'],{'$set':{'weapon':key}}); await q.answer('Equipped!',show_alert=True); return
        res=await db.db.players.update_one({'user_id':p['user_id'],'coins':{'$gte':price},f'inventory.{key}':{'$not':{'$gt':0}}},{'$inc':{'coins':-price,f'inventory.{key}':1},'$set':{'weapon':key}})
        if res.modified_count!=1: await q.answer('Not enough coins or already owned.',show_alert=True); return
        await q.message.edit_text(f'🟢 <b>{name} equipped!</b>\nAttack: +{attack}',reply_markup=back_home()); await q.answer('Purchased!')
    @app.on_callback_query(filters.regex(r'^buy:a:(.+)$'))
    async def buy_armor(_,q):
        key=q.matches[0].group(1)
        if key not in ARMOR: await q.answer('Unknown item.',show_alert=True); return
        name,defense,price=ARMOR[key]; p=await db.get_player(q.from_user.id,q.from_user.first_name,q.from_user.username or '')
        if p.get('inventory',{}).get(key,0)>0: await db.update_player(p['user_id'],{'$set':{'armor':key}}); await q.answer('Equipped!',show_alert=True); return
        res=await db.db.players.update_one({'user_id':p['user_id'],'coins':{'$gte':price},f'inventory.{key}':{'$not':{'$gt':0}}},{'$inc':{'coins':-price,f'inventory.{key}':1},'$set':{'armor':key}})
        if res.modified_count!=1: await q.answer('Not enough coins or already owned.',show_alert=True); return
        await q.message.edit_text(f'🟢 <b>{name} equipped!</b>\nDefense: +{defense}',reply_markup=back_home()); await q.answer('Purchased!')
    @app.on_callback_query(filters.regex(r'^buy:medkit$'))
    async def buy_medkit(_,q):
        res=await db.db.players.update_one({'user_id':q.from_user.id,'coins':{'$gte':250}},{'$inc':{'coins':-250,'inventory.medkit':1}})
        if res.modified_count!=1: await q.answer('Not enough coins.',show_alert=True); return
        await q.answer('Medkit purchased!',show_alert=True); await q.message.edit_text('💊 <b>Medkit purchased!</b>',reply_markup=back_home())

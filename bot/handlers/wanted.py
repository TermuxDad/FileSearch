import time
from pyrogram import filters
from .common import btn, kb, back_home

MIN_BOUNTY = 500
MAX_BOUNTY = 1_000_000

async def wanted_text(db):
    rows = await db.wanted(10)
    text = "☠️ <b>MOST WANTED</b>\n\n"
    if not rows:
        text += "Nobody has a bounty yet.\n"
    for i,p in enumerate(rows,1):
        text += f"{i}. <b>{p.get('name','Survivor')}</b> — 💰 <b>{int(p.get('bounty',0)):,}</b>\n"
    text += "\n💡 Set a bounty by replying to a player's message with <code>/bounty AMOUNT</code>."
    return text

def register(app, db):
    @app.on_callback_query(filters.regex(r'^home:wanted$'))
    async def wanted(_, q):
        await q.message.edit_text(await wanted_text(db), reply_markup=kb([[btn('🔵 🔄 Refresh','home:wanted')],[btn('🔵 🏠 Home','home')]]))
        await q.answer()

    @app.on_message(filters.command('bounty'))
    async def bounty(_, message):
        if not message.from_user:
            return
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply_text('☠️ Reply to a player message and use /bounty AMOUNT')
            return
        target = message.reply_to_message.from_user
        if target.is_bot or target.id == message.from_user.id:
            await message.reply_text('❌ You cannot place a bounty on yourself or a bot.')
            return
        if len(message.command) != 2 or not message.command[1].isdigit():
            await message.reply_text(f'Usage: /bounty AMOUNT (min {MIN_BOUNTY:,}, max {MAX_BOUNTY:,})')
            return
        amount = max(MIN_BOUNTY, min(MAX_BOUNTY, int(message.command[1])))
        p = await db.get_player(message.from_user.id, message.from_user.first_name, message.from_user.username or '')
        result = await db.db.players.update_one({'user_id':p['user_id'],'coins':{'$gte':amount}}, {'$inc':{'coins':-amount}})
        if result.modified_count != 1:
            await message.reply_text('❌ Not enough coins.')
            return
        await db.get_player(target.id, target.first_name, target.username or '')
        await db.db.players.update_one({'user_id':target.id},{'$inc':{'bounty':amount}})
        await message.reply_text(f'☠️ Bounty placed!\n\nTarget: <b>{target.first_name}</b>\n💰 +{amount:,} bounty')

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ButtonStyle
import config
from Client.premium import premium_emoji

def kb():
    username = config.BOT_USERNAME or "VeyroBot"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Hᴇʟᴘ", callback_data="v_help", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("Fᴇᴀᴛᴜʀᴇꜱ", callback_data="v_features", style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("Aᴅᴅ Tᴏ Gʀᴏᴜᴘ", url=f"https://t.me/{username}?startgroup=true", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="v_about", style=ButtonStyle.PRIMARY),
        ],
    ])

@Client.on_message(filters.text & filters.regex(r"^/start(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def start(client, message):
    if message.from_user:
        await client.db.register_user(message.from_user.id)
    if message.chat.type.name in ("GROUP", "SUPERGROUP"):
        await client.db.register_group(message.chat.id, message.chat.title or "")
    text = (
        f"{premium_emoji('home','👋')} <b>Wᴇʟᴄᴏᴍᴇ Tᴏ Vᴇʏʀᴏ.</b>\n\n"
        "<b>Yᴏᴜʀ Aʟʟ-Iɴ-Oɴᴇ Tᴇʟᴇɢʀᴀᴍ Gʀᴏᴜᴘ Aꜱꜱɪꜱᴛᴀɴᴛ.</b>\n\n"
        f"{premium_emoji('settings','⚙️')} Gʀᴏᴜᴘ Mᴀɴᴀɢᴇᴍᴇɴᴛ\n"
        f"{premium_emoji('home','👥')} Tᴀɢɢɪɴɢ & Mᴇɴᴛɪᴏɴꜱ\n"
        f"{premium_emoji('lock','🔐')} Pʀɪᴠᴀᴛᴇ Wʜɪꜱᴘᴇʀꜱ\n"
        f"{premium_emoji('help','📝')} Nᴏᴛᴇꜱ & Aᴅᴍɪɴ Pᴏᴡᴇʀꜱ\n\n"
        "Cʜᴏᴏꜱᴇ Aɴ Oᴘᴛɪᴏɴ Bᴇʟᴏᴡ."
    )
    await message.reply_text(text, reply_markup=kb())

@Client.on_callback_query(filters.regex(r"^v_"))
async def start_callbacks(client, query):
    action = query.data
    if action == "v_help":
        text = "<b>Hᴇʟᴘ Cᴇɴᴛᴇʀ</b>\n\nUꜱᴇ <b>/help</b> Tᴏ Vɪᴇᴡ Aʟʟ Cᴏᴍᴍᴀɴᴅꜱ."
    elif action == "v_features":
        text = "<b>Fᴇᴀᴛᴜʀᴇꜱ</b>\n\nWʜɪꜱᴘᴇʀꜱ • Tᴀɢɢɪɴɢ • Mᴏᴅᴇʀᴀᴛɪᴏɴ • Nᴏᴛᴇꜱ • Aᴅᴍɪɴ Pᴏᴡᴇʀꜱ."
    elif action == "v_about":
        text = "<b>Aʙᴏᴜᴛ Vᴇʏʀᴏ</b>\n\nA Pʀᴏꜰᴇꜱꜱɪᴏɴᴀʟ Gʀᴏᴜᴘ Mᴀɴᴀɢᴇᴍᴇɴᴛ Bᴏᴛ."
    else:
        text = "<b>Wᴇʟᴄᴏᴍᴇ Tᴏ Vᴇʏʀᴏ.</b>\n\nCʜᴏᴏꜱᴇ Aɴ Oᴘᴛɪᴏɴ Bᴇʟᴏᴡ."
    await query.answer()
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bᴀᴄᴋ", callback_data="v_home", style=ButtonStyle.PRIMARY)]]))

@Client.on_message(filters.text & filters.regex(r"^/help(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def help_command(client, message):
    text = (
        "<b>Hᴇʟᴘ Cᴇɴᴛᴇʀ</b>\n\n"
        "<b>Tᴀɢɢɪɴɢ</b>\n<code>/gmtag</code> • Gᴏᴏᴅ Mᴏʀɴɪɴɢ\n<code>/gntag</code> • Gᴏᴏᴅ Nɪɢʜᴛ\n<code>/tagall</code> • Tᴀɢ Aʟʟ\n<code>/vctag</code> • Vᴄ Tᴀɢ\n<code>/admin</code> • Aᴅᴍɪɴ Tᴀɢ\n<code>/all</code> • Aʟʟ Mᴇᴍʙᴇʀ Tᴀɢ\n<code>/stop</code> • Sᴛᴏᴘ Tᴀɢɢɪɴɢ\n<code>/pause</code> • Pᴀᴜꜱᴇ Tᴀɢɢɪɴɢ\n<code>/resume</code> • Rᴇꜱᴜᴍᴇ Tᴀɢɢɪɴɢ\n\n"
        "<b>Mᴏᴅᴇʀᴀᴛɪᴏɴ</b>\n<code>/warn /unwarn /warns</code>\n<code>/mute /unmute</code>\n<code>/ban /unban /kick</code>\n<code>/dmute /smute /dban /sban /skick</code>\n<code>/pin /unpin /d</code>\n\n"
        "<b>Aᴅᴍɪɴ</b>\n<code>/res /add /remove</code>\n<code>/promote /demote /demote_all</code>\n<code>/title</code>\n\n"
        "<b>Nᴏᴛᴇꜱ</b>\n<code>/save /get /notes /delnote /clear_notes</code>\n\n"
        "<b>Oᴡɴᴇʀ</b>\n<code>/broadcast /stats /update</code>\n\n"
        f"<b>Wʜɪꜱᴘᴇʀ</b>\nUꜱᴇ Vᴇʏʀᴏ Iɴ Tᴇʟᴇɢʀᴀᴍ Iɴʟɪɴᴇ Mᴏᴅᴇ: <code>@{config.BOT_USERNAME or 'VeyroBot'} @username message</code>."
    )
    await message.reply_text(text)

@Client.on_callback_query(filters.regex(r"^v_home$"))
async def back(client, query):
    await query.answer()
    await query.message.edit_text("<b>Wᴇʟᴄᴏᴍᴇ Tᴏ Vᴇʏʀᴏ.</b>\n\nCʜᴏᴏꜱᴇ Aɴ Oᴘᴛɪᴏɴ Bᴇʟᴏᴡ.", reply_markup=kb())

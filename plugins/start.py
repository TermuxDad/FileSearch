from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ButtonStyle
from pyrogram.errors import MessageNotModified
import config
from Client.premium import premium_emoji

START_IMAGE = "https://graph.org/file/561e78c3cea6f4ddba6c3-8a76966417c17d34db.jpg"

def kb():
    username = config.BOT_USERNAME or "VeyroBot"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Sᴜᴍᴍᴏɴ Mᴇ", url=f"https://t.me/{username}?startgroup=true", style=ButtonStyle.DANGER)],
        [
            InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ", url="https://t.me/ArchonCare", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("Uᴘᴅᴀᴛᴇ", url="https://t.me/ArchonNetwork", style=ButtonStyle.PRIMARY)
        ],
        [InlineKeyboardButton("Hᴇʟᴘ Cᴇɴᴛᴇʀ", callback_data="v_help", style=ButtonStyle.SUCCESS)]
    ])

def start_text(name="User"):
    return (
        f"<b>Wᴇʟᴄᴏᴍᴇ, {name}!</b> <tg-emoji emoji-id='5413694143601842851'>👋</tg-emoji>\n\n"
        "Tʜɪꜱ Iꜱ Vᴇʏʀᴏ — A Pʀᴏғᴇꜱꜱɪᴏɴᴀʟ Tᴇʟᴇɢʀᴀᴍ Aꜱꜱɪꜱᴛᴀɴᴛ.\n\n"
        "<i>Eʟᴇɢᴀɴᴛ. Fᴀꜱᴛ. Rᴇʟɪᴀʙʟᴇ.\n"
        "Eᴠᴇʀʏᴛʜɪɴɢ Iꜱ Jᴜꜱᴛ A Tᴀᴘ Aᴡᴀʏ.</i>"
    )

def help_text():
    return (
        "<b>Hᴇʟᴘ Cᴇɴᴛᴇʀ</b>\n\n"
        "<b>Tᴀɢɢɪɴɢ</b>\n"
        "<code>/gmtag</code> • Gᴏᴏᴅ Mᴏʀɴɪɴɢ\n"
        "<code>/gntag</code> • Gᴏᴏᴅ Nɪɢʜᴛ\n"
        "<code>/tagall</code> • Tᴀɢ Aʟʟ\n"
        "<code>/vctag</code> • Vᴄ Tᴀɢ\n"
        "<code>/admin</code> • Aᴅᴍɪɴ Tᴀɢ\n"
        "<code>/all</code> • Aʟʟ Mᴇᴍʙᴇʀ Tᴀɢ\n"
        "<code>/stop</code> • Sᴛᴏᴘ Tᴀɢɢɪɴɢ\n"
        "<code>/pause</code> • Pᴀᴜꜱᴇ Tᴀɢɢɪɴɢ\n"
        "<code>/resume</code> • Rᴇꜱᴜᴍᴇ Tᴀɢɢɪɴɢ\n\n"
        "<b>Oᴡɴᴇʀ</b>\n"
        "<code>/broadcast</code> <code>/stats</code> <code>/update</code>\n\n"
        "<b>Wʜɪꜱᴘᴇʀ</b>\n"
        "Uꜱᴇ Vᴇʏʀᴏ Iɴ Tᴇʟᴇɢʀᴀᴍ Iɴʟɪɴᴇ Mᴏᴅᴇ:\n"
        f"<code>@{config.BOT_USERNAME or 'VeyroBot'}</code> <code>message</code>\n"
        "Fɪʀꜱᴛ Tɪᴍᴇ, Cʜᴏᴏꜱᴇ Tʜᴇ Uꜱᴇʀ Fʀᴏᴍ Tʜᴇ Wʜɪꜱᴘᴇʀ Oᴘᴛɪᴏɴꜱ. Tʜᴇ Lᴀꜱᴛ Sᴇʟᴇᴄᴛᴇᴅ Uꜱᴇʀ Wɪʟʟ Bᴇ Sᴀᴠᴇᴅ Fᴏʀ Yᴏᴜ."
    )

def back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="v_home", style=ButtonStyle.PRIMARY)]
    ])

async def send_start(client, chat_id):
    user = await client.get_users(chat_id)
    name = user.first_name or "User"
    await client.send_photo(chat_id, START_IMAGE, caption=start_text(name), reply_markup=kb())

@Client.on_message(filters.text & filters.regex(r"^/start(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def start(client, message):
    if message.from_user:
        await client.db.register_user(message.from_user.id)
    if message.chat.type.name in ("GROUP", "SUPERGROUP"):
        await client.db.register_group(message.chat.id, message.chat.title or "")
    await send_start(client, message.chat.id)

@Client.on_callback_query(filters.regex(r"^v_help$"))
async def help_callback(client, query):
    await query.answer()
    try:
        await query.message.edit_caption(caption=help_text(), reply_markup=back_kb())
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r"^v_features$"))
async def features_callback(client, query):
    await query.answer()
    try:
        await query.message.edit_caption(
            caption="<b>Fᴇᴀᴛᴜʀᴇꜱ</b>\n\nWʜɪꜱᴘᴇʀꜱ • Tᴀɢɢɪɴɢ • Mᴏᴅᴇʀᴀᴛɪᴏɴ • Nᴏᴛᴇꜱ • Aᴅᴍɪɴ Pᴏᴡᴇʀꜱ.",
            reply_markup=back_kb()
        )
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r"^v_about$"))
async def about_callback(client, query):
    await query.answer()
    try:
        await query.message.edit_caption(
            caption="<b>Aʙᴏᴜᴛ Vᴇʏʀᴏ</b>\n\nA Pʀᴏꜰᴇꜱꜱɪᴏɴᴀʟ Gʀᴏᴜᴘ Mᴀɴᴀɢᴇᴍᴇɴᴛ Bᴏᴛ.",
            reply_markup=back_kb()
        )
    except MessageNotModified:
        pass

@Client.on_message(filters.text & filters.regex(r"^/help(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def help_command(client, message):
    await message.reply_text(help_text(), reply_markup=back_kb())

@Client.on_callback_query(filters.regex(r"^v_home$"))
async def back(client, query):
    await query.answer()
    try:
        await query.message.delete()
        await send_start(client, query.message.chat.id)
    except Exception as e:
        print(f"BACK ERROR: {type(e).__name__}: {e}", flush=True)

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ButtonStyle
from pyrogram.errors import MessageNotModified
import config
from Client.premium import premium_emoji

def kb():
    username = config.BOT_USERNAME or "VeyroBot"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Hᴇʟᴘ", callback_data="v_help", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("Fᴇᴀᴛᴜʀᴇꜱ", callback_data="v_features", style=ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton("Aᴅᴅ Tᴏ Gʀᴏᴜᴘ", url=f"https://t.me/{username}?startgroup=true", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="v_about", style=ButtonStyle.PRIMARY)
        ]
    ])

def start_text():
    return (
        f"{premium_emoji('home','👋')} <b>Wᴇʟᴄᴏᴍᴇ Tᴏ Vᴇʏʀᴏ.</b>\n\n"
        "<b>Yᴏᴜʀ Aʟʟ-Iɴ-Oɴᴇ Tᴇʟᴇɢʀᴀᴍ Gʀᴏᴜᴘ Aꜱꜱɪꜱᴛᴀɴᴛ.</b>\n\n"
        f"{premium_emoji('settings','⚙️')} Gʀᴏᴜᴘ Mᴀɴᴀɢᴇᴍᴇɴᴛ\n"
        f"{premium_emoji('home','👥')} Tᴀɢɢɪɴɢ & Mᴇɴᴛɪᴏɴꜱ\n"
        f"{premium_emoji('lock','🔐')} Pʀɪᴠᴀᴛᴇ Wʜɪꜱᴘᴇʀꜱ\n"
        f"{premium_emoji('help','📝')} Nᴏᴛᴇꜱ & Aᴅᴍɪɴ Pᴏᴡᴇʀꜱ\n\n"
        "Cʜᴏᴏꜱᴇ Aɴ Oᴘᴛɪᴏɴ Bᴇʟᴏᴡ."
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
        "<b>Mᴏᴅᴇʀᴀᴛɪᴏɴ</b>\n"
        "<code>/warn</code> <code>/unwarn</code> <code>/warns</code>\n"
        "<code>/mute</code> <code>/unmute</code>\n"
        "<code>/ban</code> <code>/unban</code> <code>/kick</code>\n"
        "<code>/dmute</code> <code>/smute</code> <code>/dban</code> <code>/sban</code> <code>/skick</code>\n"
        "<code>/pin</code> <code>/unpin</code> <code>/d</code>\n\n"
        "<b>Aᴅᴍɪɴ</b>\n"
        "<code>/res</code> <code>/add</code> <code>/remove</code>\n"
        "<code>/promote</code> <code>/demote</code> <code>/demote_all</code>\n"
        "<code>/title</code>\n\n"
        "<b>Nᴏᴛᴇꜱ</b>\n"
        "<code>/save</code> <code>/get</code> <code>/notes</code> <code>/delnote</code> <code>/clear_notes</code>\n\n"
        "<b>Oᴡɴᴇʀ</b>\n"
        "<code>/broadcast</code> <code>/stats</code> <code>/update</code>\n\n"
        "<b>Wʜɪꜱᴘᴇʀ</b>\n"
        "Uꜱᴇ Vᴇʏʀᴏ Iɴ Tᴇʟᴇɢʀᴀᴍ Iɴʟɪɴᴇ Mᴏᴅᴇ:\n"
        f"<code>@{config.BOT_USERNAME or 'VeyroBot'}</code> <code>@username</code> <code>message</code>"
    )

@Client.on_message(filters.text & filters.regex(r"^/start(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def start(client, message):
    if message.from_user:
        await client.db.register_user(message.from_user.id)
    if message.chat.type.name in ("GROUP", "SUPERGROUP"):
        await client.db.register_group(message.chat.id, message.chat.title or "")
    await message.reply_text(start_text(), reply_markup=kb())

@Client.on_callback_query(filters.regex(r"^v_"))
async def start_callbacks(client, query):
    action = query.data
    if action == "v_help":
        text = help_text()
    elif action == "v_features":
        text = "<b>Fᴇᴀᴛᴜʀᴇꜱ</b>\n\nWʜɪꜱᴘᴇʀꜱ • Tᴀɢɢɪɴɢ • Mᴏᴅᴇʀᴀᴛɪᴏɴ • Nᴏᴛᴇꜱ • Aᴅᴍɪɴ Pᴏᴡᴇʀꜱ."
    elif action == "v_about":
        text = "<b>Aʙᴏᴜᴛ Vᴇʏʀᴏ</b>\n\nA Pʀᴏꜰᴇꜱꜱɪᴏɴᴀʟ Gʀᴏᴜᴘ Mᴀɴᴀɢᴇᴍᴇɴᴛ Bᴏᴛ."
    else:
        text = start_text()
    await query.answer()
    try:
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="v_home", style=ButtonStyle.PRIMARY)]
            ])
        )
    except MessageNotModified:
        pass

@Client.on_message(filters.text & filters.regex(r"^/help(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def help_command(client, message):
    await message.reply_text(
        help_text(),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="v_home", style=ButtonStyle.PRIMARY)]
        ])
    )

@Client.on_callback_query(filters.regex(r"^v_home$"))
async def back(client, query):
    await query.answer()
    try:
        await query.message.edit_text(start_text(), reply_markup=kb())
    except MessageNotModified:
        pass

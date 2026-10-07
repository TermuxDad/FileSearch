import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import ButtonStyle
from Client.helpers import resolve_user

@Client.on_inline_query()
async def whisper_inline(client, query):
    text = (query.query or "").strip()
    if not text:
        return
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return
    target_raw, msg = parts
    if len(msg) > 180:
        return await query.answer("Wʜɪꜱᴘᴇʀ Mᴜꜱᴛ Bᴇ 180 Cʜᴀʀᴀᴄᴛᴇʀꜱ Oʀ Lᴇꜱꜱ.", cache_time=0, is_personal=True)
    try:
        target = await client.get_users(int(target_raw) if target_raw.lstrip("-").isdigit() else target_raw.lstrip("@"))
    except Exception:
        return
    whisper_id = uuid.uuid4().hex
    await client.db.save_whisper(whisper_id, target.id, query.from_user.id, msg)
    result = InlineQueryResultArticle(
        title="Sᴇᴄʀᴇᴛ Wʜɪꜱᴘᴇʀ",
        description="Oɴʟʏ Tʜᴇ Tᴀʀɢᴇᴛ Uꜱᴇʀ Cᴀɴ Oᴘᴇɴ Tʜɪꜱ Mᴇꜱꜱᴀɢᴇ.",
        input_message_content=InputTextMessageContent(
            f"<b>A Wʜɪꜱᴘᴇʀ Hᴀꜱ Bᴇᴇɴ Sᴇɴᴛ Tᴏ {target.first_name}.</b>\n\n"
            "<b>Oɴʟʏ Tʜᴇ Tᴀʀɢᴇᴛ Uꜱᴇʀ Cᴀɴ Oᴘᴇɴ Iᴛ.</b>"
        ),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Sʜᴏᴡ Mᴇꜱꜱᴀɢᴇ", callback_data=f"whisper:{whisper_id}", style=ButtonStyle.PRIMARY)
        ]]),
    )
    await query.answer([result], cache_time=0)

@Client.on_callback_query(filters.regex(r"^whisper:"))
async def whisper_callback(client, query):
    whisper_id = query.data.split(":", 1)[1]
    item = await client.db.get_whisper(whisper_id)
    if not item:
        return await query.answer("Mᴇꜱꜱᴀɢᴇ Eᴋꜱᴘɪʀᴇᴅ.", show_alert=True)
    if query.from_user.id != item["target_id"]:
        return await query.answer("Tʜɪꜱ Mᴇꜱꜱᴀɢᴇ Iꜱ Nᴏᴛ Fᴏʀ Yᴏᴜ.", show_alert=True)
    await query.answer(item["message"], show_alert=True)

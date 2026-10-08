import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import ButtonStyle
from Client.premium import premium_emoji

MAX_WHISPER_LENGTH = 180


def safe_name(user):
    return (user.first_name or user.username or str(user.id)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mention(user):
    return f'<a href="tg://user?id={user.id}">{safe_name(user)}</a>'


def whisper_result(title, description, whisper_id, target_name, target_id, sender_id, message, chat_id=None):
    return InlineQueryResultArticle(
        title=title,
        description=description,
        input_message_content=InputTextMessageContent(
            f"<b>A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ {target_name}.</b>\n"
            f"<b>Oɴʟʏ Tʜᴇ Tᴀʀɢᴇᴛ Cᴀɴ Rᴇᴀᴅ Tʜᴇ Mᴇꜱꜱᴀɢᴇ.</b>" if target_id else
            "<b>A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ Aɴʏᴏɴᴇ.</b>\n"
            "<b>Eᴠᴇʀʏᴏɴᴇ Cᴀɴ Oᴘᴇɴ Tʜɪꜱ Wʜɪꜱᴘᴇʀ.</b>"
        ),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"{premium_emoji('lock','🔐')}",
                callback_data=f"whisper:{whisper_id}",
                style=ButtonStyle.PRIMARY,
            )
        ]]),
    )


async def create_whisper(client, sender_id, chat_id, target_id, target_name, message):
    whisper_id = uuid.uuid4().hex
    await client.db.save_whisper(
        whisper_id,
        target_id,
        sender_id,
        message,
        chat_id=chat_id,
        target_name=target_name,
    )
    return whisper_id


@Client.on_inline_query()
async def whisper_inline(client, query):
    text = (query.query or "").strip()
    if len(text) > MAX_WHISPER_LENGTH + 40:
        text = text[:MAX_WHISPER_LENGTH + 40]
    parts = text.split(maxsplit=1)
    sender_id = query.from_user.id
    saved = await client.db.get_whisper_target(sender_id)
    target = None
    message = text
    explicit_target = False
    if parts and parts[0].startswith("@"):
        explicit_target = True
        target_ref = parts[0][1:]
        message = parts[1].strip() if len(parts) == 2 else ""
        if target_ref:
            try:
                target = await client.get_users(target_ref)
            except Exception:
                target = None
    elif parts and parts[0].lstrip("-").isdigit() and len(parts) == 2:
        explicit_target = True
        try:
            target = await client.get_users(int(parts[0]))
        except Exception:
            target = None
        message = parts[1].strip()
    if len(message) > MAX_WHISPER_LENGTH:
        return await query.answer(
            f"Wʜɪꜱᴘᴇʀ Mᴜꜱᴛ Bᴇ {MAX_WHISPER_LENGTH} Cʜᴀʀᴀᴄᴛᴇʀꜱ Oʀ Lᴇꜱꜱ.",
            cache_time=0,
            is_personal=True,
        )
    if explicit_target:
        if not target or not message:
            return await query.answer(
                [InlineQueryResultArticle(
                    title="Iɴᴠᴀʟɪᴅ Wʜɪꜱᴘᴇʀ! Pʟᴇᴀꜱᴇ Cʀᴇᴀᴛᴇ Aɴᴏᴛʜᴇʀ Oɴᴇ!",
                    description="Uꜱᴇ @username Oʀ Uꜱᴇʀ ID Fᴏʟʟᴏᴡᴇᴅ Bʏ Yᴏᴜʀ Mᴇꜱꜱᴀɢᴇ.",
                    input_message_content=InputTextMessageContent("<b>Iɴᴠᴀʟɪᴅ Wʜɪꜱᴘᴇʀ! Pʟᴇᴀꜱᴇ Cʀᴇᴀᴛᴇ Aɴᴏᴛʜᴇʀ Oɴᴇ!</b>"),
                )],
                cache_time=0,
                is_personal=True,
            )
        target_name = safe_name(target)
        await client.db.save_whisper_target(sender_id, target.id, target_name, target.username or "")
        whisper_id = await create_whisper(client, sender_id, None, target.id, target_name, message)
        result = whisper_result(
            "Sᴇɴᴅ Wʜɪꜱᴘᴇʀ",
            f"Sᴇɴᴅ Tᴏ {target_name}",
            whisper_id,
            target_name,
            target.id,
            sender_id,
            message,
        )
        return await query.answer([result], cache_time=0, is_personal=True)
    if not message:
        return
    results = [InlineQueryResultArticle(
        title="Iɴᴠᴀʟɪᴅ Wʜɪꜱᴘᴇʀ! Pʟᴇᴀꜱᴇ Cʀᴇᴀᴛᴇ Aɴᴏᴛʜᴇʀ Oɴᴇ!",
        description="Cʜᴏᴏꜱᴇ A Tᴀʀɢᴇᴛ Bᴇʟᴏᴡ.",
        input_message_content=InputTextMessageContent("<b>Iɴᴠᴀʟɪᴅ Wʜɪꜱᴘᴇʀ! Pʟᴇᴀꜱᴇ Cʀᴇᴀᴛᴇ Aɴᴏᴛʜᴇʀ Oɴᴇ!</b>"),
    )]
    anyone_id = await create_whisper(client, sender_id, None, 0, "Aɴʏᴏɴᴇ", message)
    results.append(whisper_result(
        "📖 A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ Aɴʏᴏɴᴇ!",
        "Eᴠᴇʀʏᴏɴᴇ Wɪʟʟ Bᴇ Aʙʟᴇ Tᴏ Oᴘᴇɴ Tʜɪꜱ Wʜɪꜱᴘᴇʀ.",
        anyone_id,
        "Aɴʏᴏɴᴇ",
        0,
        sender_id,
        message,
    ))
    if saved:
        try:
            target = await client.get_users(int(saved["target_id"]))
        except Exception:
            target = None
        if target:
            target_name = safe_name(target)
            target_id = target.id
            await client.db.save_whisper_target(sender_id, target_id, target_name, target.username or "")
            whisper_id = await create_whisper(client, sender_id, None, target_id, target_name, message)
            results.append(whisper_result(
                f"💌 A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ {target_name}",
                f"Oɴʟʏ {target_name} Cᴀɴ Oᴘᴇɴ Tʜɪꜱ Wʜɪꜱᴘᴇʀ.",
                whisper_id,
                target_name,
                target_id,
                sender_id,
                message,
            ))
    await query.answer(results, cache_time=0, is_personal=True)


@Client.on_callback_query(filters.regex(r"^whisper:"))
async def whisper_callback(client, query):
    whisper_id = query.data.split(":", 1)[1]
    item = await client.db.get_whisper(whisper_id)
    if not item:
        return await query.answer("Iɴᴠᴀʟɪᴅ Wʜɪꜱᴘᴇʀ! Pʟᴇᴀꜱᴇ Cʀᴇᴀᴛᴇ Aɴᴏᴛʜᴇʀ Oɴᴇ!", show_alert=True)
    if item.get("read_at"):
        return await query.answer("Tʜɪꜱ Wʜɪꜱᴘᴇʀ Hᴀꜱ Aʟʀᴇᴀᴅʏ Bᴇᴇɴ Rᴇᴀᴅ.", show_alert=True)
    target_id = int(item.get("target_id", 0))
    if target_id and query.from_user.id != target_id:
        return await query.answer("Tʜɪꜱ Wʜɪꜱᴘᴇʀ Iꜱ Nᴏᴛ Fᴏʀ Yᴏᴜ.", show_alert=True)
    updated = await client.db.mark_whisper_read(whisper_id, query.from_user.id)
    if not updated:
        return await query.answer("Tʜɪꜱ Wʜɪꜱᴘᴇʀ Hᴀꜱ Aʟʀᴇᴀᴅʏ Bᴇᴇɴ Rᴇᴀᴅ.", show_alert=True)
    await query.answer(item["message"], show_alert=True)
    if query.message:
        reader = safe_name(query.from_user)
        try:
            await query.message.edit_text(
                f"<b>{reader} Rᴇᴀᴅ Tʜᴇ Wʜɪꜱᴘᴇʀ.</b>"
            )
        except Exception:
            pass

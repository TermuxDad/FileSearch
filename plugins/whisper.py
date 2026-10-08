import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import ButtonStyle

MAX_WHISPER_LENGTH = 180
BUTTON_EMOJI_ID = "6271537028307881531"


def safe_name(user):
    name = getattr(user, "first_name", None)
    username = getattr(user, "username", None)
    user_id = getattr(user, "id", user)
    return (name or username or str(user_id)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mention(user_id, name):
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def whisper_button(whisper_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "Rᴇᴀᴅ Wʜɪꜱᴘᴇʀ",
            callback_data=f"whisper:{whisper_id}",
            style=ButtonStyle.PRIMARY,
            icon_custom_emoji_id=BUTTON_EMOJI_ID,
        )
    ]])


def whisper_result(title, description, whisper_id, target_name, target_id):
    if target_id:
        text = (
            f"<b>A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ {target_name}.</b>\n"
            "<b>Oɴʟʏ Tʜᴇ Tᴀʀɢᴇᴛ Cᴀɴ Rᴇᴀᴅ Tʜᴇ Mᴇꜱꜱᴀɢᴇ.</b>"
        )
    else:
        text = (
            "<b>A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ Aɴʏᴏɴᴇ.</b>\n"
            "<b>Eᴠᴇʀʏᴏɴᴇ Cᴀɴ Oᴘᴇɴ Tʜɪꜱ Wʜɪꜱᴘᴇʀ.</b>"
        )
    return InlineQueryResultArticle(
        title=title,
        description=description,
        input_message_content=InputTextMessageContent(text),
        reply_markup=whisper_button(whisper_id),
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


async def answer_results(query, results):
    await query.answer(results, cache_time=0, is_personal=True)


@Client.on_inline_query()
async def whisper_inline(client, query):
    text = (query.query or "").strip()
    sender_id = query.from_user.id
    if not text:
        return
    parts = text.split(maxsplit=1)
    saved_targets = await client.db.get_whisper_targets(sender_id, 10)
    target = None
    target_id = 0
    target_name = "Aɴʏᴏɴᴇ"
    message = text
    explicit_target = False

    if parts[0].startswith("@") and len(parts[0]) > 1:
        explicit_target = True
        target_ref = parts[0][1:]
        message = parts[1].strip() if len(parts) == 2 else ""
        try:
            target = await client.get_users(target_ref)
        except Exception:
            target = None
        if target:
            target_id = target.id
            target_name = safe_name(target)
    elif parts[0].lstrip("-").isdigit() and len(parts) == 2:
        explicit_target = True
        target_id = int(parts[0])
        message = parts[1].strip()
        saved_match = next((item for item in saved_targets if int(item.get("target_id", 0)) == target_id), None)
        if saved_match:
            target_name = saved_match.get("target_name") or str(target_id)
        else:
            try:
                target = await client.get_users(target_id)
                target_name = safe_name(target)
            except Exception:
                target_name = str(target_id)

    if len(message) > MAX_WHISPER_LENGTH:
        return await answer_results(query, [InlineQueryResultArticle(
            title=f"Wʜɪꜱᴘᴇʀ Mᴜꜱᴛ Bᴇ {MAX_WHISPER_LENGTH} Cʜᴀʀᴀᴄᴛᴇʀꜱ Oʀ Lᴇꜱꜱ.",
            description="Pʟᴇᴀꜱᴇ Sʜᴏʀᴛᴇɴ Yᴏᴜʀ Mᴇꜱꜱᴀɢᴇ.",
            input_message_content=InputTextMessageContent(
                f"<b>Wʜɪꜱᴘᴇʀ Mᴜꜱᴛ Bᴇ {MAX_WHISPER_LENGTH} Cʜᴀʀᴀᴄᴛᴇʀꜱ Oʀ Lᴇꜱꜱ.</b>"
            ),
        )])

    if explicit_target:
        if not target_id or not message:
            return await answer_results(query, [InlineQueryResultArticle(
                title="Iɴᴠᴀʟɪᴅ Wʜɪꜱᴘᴇʀ! Pʟᴇᴀꜱᴇ Cʀᴇᴀᴛᴇ Aɴᴏᴛʜᴇʀ Oɴᴇ!",
                description="Uꜱᴇ @username Oʀ Uꜱᴇʀ ID Fᴏʟʟᴏᴡᴇᴅ Bʏ Yᴏᴜʀ Mᴇꜱꜱᴀɢᴇ.",
                input_message_content=InputTextMessageContent(
                    "<b>Iɴᴠᴀʟɪᴅ Wʜɪꜱᴘᴇʀ! Pʟᴇᴀꜱᴇ Cʀᴇᴀᴛᴇ Aɴᴏᴛʜᴇʀ Oɴᴇ!</b>"
                ),
            )])
        await client.db.save_whisper_target(
            sender_id,
            target_id,
            target_name,
            getattr(target, "username", "") if target else "",
        )
        whisper_id = await create_whisper(client, sender_id, None, target_id, target_name, message)
        return await answer_results(query, [whisper_result(
            "Sᴇɴᴅ Wʜɪꜱᴘᴇʀ",
            f"Sᴇɴᴅ Tᴏ {target_name}",
            whisper_id,
            target_name,
            target_id,
        )])

    results = []
    anyone_id = await create_whisper(client, sender_id, None, 0, target_name, message)
    results.append(whisper_result(
        "A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ Aɴʏᴏɴᴇ",
        "Eᴠᴇʀʏᴏɴᴇ Wɪʟʟ Bᴇ Aʙʟᴇ Tᴏ Oᴘᴇɴ Tʜɪꜱ Wʜɪꜱᴘᴇʀ.",
        anyone_id,
        "Aɴʏᴏɴᴇ",
        0,
    ))

    for saved in saved_targets:
        saved_id = int(saved.get("target_id", 0))
        if not saved_id:
            continue
        saved_name = saved.get("target_name") or str(saved_id)
        whisper_id = await create_whisper(client, sender_id, None, saved_id, saved_name, message)
        results.append(whisper_result(
            f"A Wʜɪꜱᴘᴇʀ Mᴇꜱꜱᴀɢᴇ Tᴏ {saved_name}",
            f"Oɴʟʏ {saved_name} Cᴀɴ Oᴘᴇɴ Tʜɪꜱ Wʜɪꜱᴘᴇʀ.",
            whisper_id,
            saved_name,
            saved_id,
        ))

    await answer_results(query, results)


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
    reader = mention(query.from_user.id, safe_name(query.from_user))
    read_text = f"<b>{reader} Rᴇᴀᴅ Tʜᴇ Wʜɪꜱᴘᴇʀ.</b>"
    try:
        if query.inline_message_id:
            await client.edit_inline_text(query.inline_message_id, read_text)
        elif query.message:
            await query.message.edit_text(read_text)
    except Exception as e:
        print(f"WHISPER READ UPDATE ERROR: {type(e).__name__}: {e}", flush=True)

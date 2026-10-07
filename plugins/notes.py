from pyrogram import Client, filters
from pyrogram.enums import ChatType
from Client.helpers import require_admin

async def serialize_message(message):
    data = {"type": "message", "chat_id": message.chat.id, "message_id": message.id}
    if message.text:
        data.update(type="text", text=message.text)
    elif message.caption:
        data.update(type="caption", caption=message.caption)
    return data

@Client.on_message(filters.text & filters.regex(r"^/(save|get|notes|delnote|clear_notes)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def notes(client, message):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP) or not await require_admin(client, message):
        return
    parts = message.text.split(maxsplit=2)
    cmd = parts[0][1:].lower()
    if cmd == "notes":
        docs = await client.db.list_notes(message.chat.id)
        if not docs:
            return await message.reply_text("<b>Nᴏ Nᴏᴛᴇꜱ Sᴀᴠᴇᴅ.</b>")
        return await message.reply_text("<b>Nᴏᴛᴇꜱ:</b>\n" + "\n".join(f"• <code>{x['name']}</code>" for x in docs))
    if cmd == "clear_notes":
        count = await client.db.clear_notes(message.chat.id)
        return await message.reply_text(f"<b>Cʟᴇᴀʀᴇᴅ:</b> {count} Nᴏᴛᴇꜱ.")
    if len(parts) < 2:
        return await message.reply_text(f"<b>Uꜱᴇ /{cmd} &lt;name&gt;.</b>")
    name = parts[1]
    if cmd == "save":
        if message.reply_to_message:
            data = await serialize_message(message.reply_to_message)
        elif len(parts) >= 3:
            data = {"type": "text", "text": parts[2]}
        else:
            return await message.reply_text("<b>Rᴇᴘʟʏ Tᴏ A Mᴇꜱꜱᴀɢᴇ Oʀ Pʀᴏᴠɪᴅᴇ Tᴇxᴛ.</b>")
        await client.db.save_note(message.chat.id, name, data)
        return await message.reply_text("<b>Nᴏᴛᴇ Sᴀᴠᴇᴅ.</b>")
    if cmd == "get":
        note = await client.db.get_note(message.chat.id, name)
        if not note:
            return await message.reply_text("<b>Nᴏᴛᴇ Nᴏᴛ Fᴏᴜɴᴅ.</b>")
        data = note["data"]
        if data["type"] == "text":
            return await message.reply_text(data["text"])
        try:
            await client.copy_message(message.chat.id, data["chat_id"], data["message_id"])
        except Exception:
            await message.reply_text("<b>Tʜᴇ Sᴀᴠᴇᴅ Mᴇꜱꜱᴀɢᴇ Cᴏᴜʟᴅ Nᴏᴛ Bᴇ Cᴏᴘɪᴇᴅ.</b>")
    elif cmd == "delnote":
        ok = await client.db.delete_note(message.chat.id, name)
        await message.reply_text("<b>Nᴏᴛᴇ Dᴇʟᴇᴛᴇᴅ.</b>" if ok else "<b>Nᴏᴛᴇ Nᴏᴛ Fᴏᴜɴᴅ.</b>")

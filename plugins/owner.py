import asyncio
import re
from pyrogram import Client, filters
import config

COMMAND_RE = r"^/(?:{cmd})(?:@[^\s]+)?(?:\s|$)"


def is_owner(message):
    return bool(message.from_user and config.OWNER_ID and message.from_user.id == config.OWNER_ID)


@Client.on_message(filters.text & filters.regex(COMMAND_RE.format(cmd="broadcast")))
async def broadcast(client, message):
    if not is_owner(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text("<b>Uꜱᴇ /broadcast &lt;message&gt;.</b>")
    targets = await client.db.get_all_targets()
    sent = failed = 0
    for target in targets:
        try:
            await client.send_message(target, parts[1])
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.08)
    await message.reply_text(f"<b>Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴘʟᴇᴛᴇ.</b>\n\nSᴇɴᴛ: {sent}\nFᴀɪʟᴇᴅ: {failed}")


@Client.on_message(filters.text & filters.regex(COMMAND_RE.format(cmd="stats")))
async def stats(client, message):
    if not is_owner(message):
        return
    try:
        data = await client.db.get_stats()
        users = await client.db.count_users()
        groups = await client.db.count_groups()
        commands = [(k.split(":", 1)[1], int(v or 0)) for k, v in data.items() if k.startswith("command:")]
        commands.sort(key=lambda x: x[1], reverse=True)
        top = "\n".join(f"/{name}: {count}" for name, count in commands[:15]) or "Nᴏ Cᴏᴍᴍᴀɴᴅ Sᴛᴀᴛꜱ Yᴇᴛ."
        await message.reply_text(
            f"<b>Vᴇʏʀᴏ Sᴛᴀᴛɪꜱᴛɪᴄꜱ</b>\n\n"
            f"Uꜱᴇʀꜱ: {users}\n"
            f"Gʀᴏᴜᴘꜱ: {groups}\n\n"
            f"<b>Tᴏᴘ Cᴏᴍᴍᴀɴᴅꜱ</b>\n{top}"
        )
    except Exception:
        await message.reply_text("<b>Uɴᴀʙʟᴇ Tᴏ Lᴏᴀᴅ Sᴛᴀᴛɪꜱᴛɪᴄꜱ. Pʟᴇᴀꜱᴇ Cʜᴇᴄᴋ Tʜᴇ Dᴀᴛᴀʙᴀꜱᴇ Cᴏɴɴᴇᴄᴛɪᴏɴ.</b>")

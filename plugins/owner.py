import asyncio
from pyrogram import Client, filters
import config

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast(client, message):
    if not message.from_user or message.from_user.id != config.OWNER_ID:
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

@Client.on_message(filters.command("stats") & filters.private)
async def stats(client, message):
    if not message.from_user or message.from_user.id != config.OWNER_ID:
        return
    data = await client.db.get_stats()
    users = len(await client.db.db.users.distinct("user_id"))
    groups = len(await client.db.db.groups.distinct("chat_id"))
    commands = [(k.split(":", 1)[1], v) for k, v in data.items() if k.startswith("command:")]
    commands.sort(key=lambda x: x[1], reverse=True)
    top = "\n".join(f"/{name}: {count}" for name, count in commands[:15]) or "Nᴏ Cᴏᴍᴍᴀɴᴅ Sᴛᴀᴛꜱ Yᴇᴛ."
    await message.reply_text(f"<b>Vᴇʏʀᴏ Sᴛᴀᴛɪꜱᴛɪᴄꜱ</b>\n\nUꜱᴇʀꜱ: {users}\nGʀᴏᴜᴘꜱ: {groups}\n\n<b>Tᴏᴘ Cᴏᴍᴍᴀɴᴅꜱ</b>\n{top}")

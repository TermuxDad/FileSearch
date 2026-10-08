from pyrogram import Client, filters

@Client.on_message(filters.text & filters.regex(r"^/[A-Za-z_]+(?:\s|$)"), group=99)
async def track(client, message):
    if not message.from_user:
        return
    cmd = message.text.split(None, 1)[0][1:].split("@", 1)[0].lower()
    try:
        await client.db.inc_stat(f"command:{cmd}")
        await client.db.register_user(message.from_user.id)
        if message.chat and message.chat.type.name in ("GROUP", "SUPERGROUP"):
            await client.db.register_group(message.chat.id, message.chat.title or "")
    except Exception:
        pass

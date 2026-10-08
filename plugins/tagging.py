import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus
from pyrogram.errors import RPCError
from Client.helpers import mention, require_admin, require_power

async def collect_members(client, chat_id, admins=False, online=False):
    users = []
    kwargs = {"filter": ChatMembersFilter.ADMINISTRATORS} if admins else {}
    async for member in client.get_chat_members(chat_id, **kwargs):
        user = member.user
        if not user or user.is_bot:
            continue
        if online:
            status = getattr(user, "status", None)
            status_name = getattr(status, "name", str(status).split(".")[-1] if status else "")
            if status_name not in ("ONLINE", "RECENTLY"):
                continue
        users.append(user)
    return users

async def bot_can_read_members(client, chat_id):
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return False
        privileges = member.privileges
        if not privileges:
            return False
        return bool(
            getattr(privileges, "can_manage_chat", False)
            or getattr(privileges, "can_delete_messages", False)
            or getattr(privileges, "can_restrict_members", False)
            or getattr(privileges, "can_invite_users", False)
            or getattr(privileges, "can_pin_messages", False)
            or getattr(privileges, "can_promote_members", False)
            or getattr(privileges, "can_manage_video_chats", False)
        )
    except Exception:
        return False

async def run_tag(client, message, mode, custom=""):
    if not await require_admin(client, message):
        return
    if mode == "vc" and not await require_power(client, message, "vctag"):
        return
    if message.chat.id in client.tag_jobs:
        return await message.reply_text("<b>A Tᴀɢɢɪɴɢ Jᴏʙ Iꜱ Aʟʀᴇᴀᴅʏ Rᴜɴɴɪɴɢ.</b>")
    if not await bot_can_read_members(client, message.chat.id):
        return await message.reply_text(
            "<b>Vᴇʏʀᴏ Nᴇᴇᴅꜱ Aᴅᴍɪɴ Aᴄᴄᴇꜱꜱ.</b>\n\n"
            "Pʀᴏᴍᴏᴛᴇ Vᴇʏʀᴏ Aꜱ Aɴ Aᴅᴍɪɴ Aɴᴅ Gɪᴠᴇ Iᴛ Tʜᴇ Rᴇǫᴜɪʀᴇᴅ Cʜᴀᴛ Mᴀɴᴀɢᴇᴍᴇɴᴛ Pᴇʀᴍɪꜱꜱɪᴏɴ."
        )
    try:
        users = await collect_members(client, message.chat.id, admins=mode == "admin", online=mode == "vc")
    except RPCError as error:
        return await message.reply_text(
            f"<b>Uɴᴀʙʟᴇ Tᴏ Rᴇᴀᴅ Gʀᴏᴜᴘ Mᴇᴍʙᴇʀꜱ.</b>\n\n"
            f"Tᴇʟᴇɢʀᴀᴍ Eʀʀᴏʀ: <code>{type(error).__name__}</code>"
        )
    except Exception as error:
        return await message.reply_text(
            f"<b>Uɴᴀʙʟᴇ Tᴏ Rᴇᴀᴅ Gʀᴏᴜᴘ Mᴇᴍʙᴇʀꜱ.</b>\n\n"
            f"Eʀʀᴏʀ: <code>{type(error).__name__}</code>"
        )
    if not users:
        return await message.reply_text("<b>Nᴏ Uꜱᴇʀꜱ Fᴏᴜɴᴅ.</b>")
    stop = asyncio.Event()
    pause = asyncio.Event()
    pause.set()
    state = {"stop": stop, "pause": pause, "task": None}
    client.tag_jobs[message.chat.id] = state

    async def worker():
        try:
            header = custom or {
                "gm": "Gᴏᴏᴅ Mᴏʀɴɪɴɢ, Sᴀʙᴋᴏ Sᴜᴘʀᴀʙʜᴀᴛ!",
                "gn": "Gᴏᴏᴅ Nɪɢʜᴛ, Sᴀʙᴋᴏ Sʜᴜʙʜ Rᴀᴛʀɪ!",
                "tagall": "Hᴇʟʟᴏ Eᴠᴇʀʏᴏɴᴇ",
                "vc": "Vᴏɪᴄᴇ Cʜᴀᴛ Tɪᴍᴇ, Pʟᴇᴀꜱᴇ Jᴏɪɴ",
                "admin": "Aᴅᴍɪɴ Aʟᴇʀᴛ",
                "all": "Hᴇʟʟᴏ Eᴠᴇʀʏᴏɴᴇ",
            }.get(mode, "Tᴀɢ")
            for i in range(0, len(users), 6):
                if stop.is_set():
                    break
                await pause.wait()
                await client.send_message(
                    message.chat.id,
                    f"<b>{header}</b>\n\n" + " ".join(mention(u) for u in users[i:i + 6]),
                )
                await asyncio.sleep(1.2)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        finally:
            client.tag_jobs.pop(message.chat.id, None)

    state["task"] = asyncio.create_task(worker())


@Client.on_message(filters.text & filters.regex(r"^/(gmtag|gntag|tagall|vctag|admin|all)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def tagging(client, message):
    match = message.text.split(None, 1)
    cmd = match[0][1:].split("@", 1)[0].lower()
    custom = match[1].strip() if len(match) > 1 else ""
    await run_tag(client, message, {"gmtag": "gm", "gntag": "gn", "tagall": "tagall", "vctag": "vc", "admin": "admin", "all": "all"}[cmd], custom)


@Client.on_message(filters.text & filters.regex(r"^/(stop|pause|resume)(?:@[A-Za-z0-9_]+)?$"))
async def tag_control(client, message):
    if not await require_admin(client, message):
        return
    state = client.tag_jobs.get(message.chat.id)
    if not state:
        return await message.reply_text("<b>Nᴏ Aᴄᴛɪᴠᴇ Tᴀɢɢɪɴɢ Jᴏʙ.</b>")
    cmd = message.text[1:].split("@", 1)[0].lower()
    if cmd == "stop":
        state["stop"].set()
        state["task"].cancel()
    elif cmd == "pause":
        state["pause"].clear()
    else:
        state["pause"].set()
    await message.reply_text(f"<b>Tᴀɢɢɪɴɢ {cmd.title()}ᴅ.</b>")

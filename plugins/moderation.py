from datetime import datetime, timedelta, timezone
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import ChatPermissions, ChatPrivileges
from Client.helpers import resolve_user, parse_duration, require_power, command_match, mention, safe_delete, bot_can, POWER_NAMES

async def action_ok(client, message, command):
    return bool(
        message.chat and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
        and await require_power(client, message, command)
    )

async def punish(client, message, mode, silent=False, delete=False):
    cmd = command_match(message.text).group(1).lower()
    if not await action_ok(client, message, cmd):
        return
    parts = (message.text or "").split()
    user = await resolve_user(client, message, parts[1] if len(parts) > 1 else None)
    if not user:
        return await message.reply_text("<b>Uꜱᴇ A Rᴇᴘʟʏ, Uꜱᴇʀɴᴀᴍᴇ Oʀ Uꜱᴇʀ ID.</b>")
    if user.id == message.from_user.id or user.is_bot:
        return await message.reply_text("<b>Tʜɪꜱ Uꜱᴇʀ Cᴀɴɴᴏᴛ Bᴇ Pᴜɴɪꜱʜᴇᴅ.</b>")
    duration = parse_duration(parts[2]) if len(parts) > 2 else None
    if len(parts) > 2 and parts[2].lower() not in ("0", "forever", "permanent", "perm") and duration is None:
        return await message.reply_text("<b>Iɴᴠᴀʟɪᴅ Dᴜʀᴀᴛɪᴏɴ.</b> Uꜱᴇ 30m, 2h, 1d, Eᴛᴄ.")
    required = "can_restrict_members"
    if not await bot_can(client, message.chat.id, required):
        return await message.reply_text("<b>Vᴇʏʀᴏ Nᴇᴇᴅꜱ Pᴇʀᴍɪꜱꜱɪᴏɴ Tᴏ Pᴇʀꜰᴏʀᴍ Tʜɪꜱ Aᴄᴛɪᴏɴ.</b>")
    try:
        if mode == "mute":
            until_date = datetime.now(timezone.utc) + timedelta(seconds=duration) if duration else None
            permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False, can_add_web_page_previews=False)
            await client.restrict_chat_member(message.chat.id, user.id, permissions=permissions, until_date=until_date)
        else:
            await client.ban_chat_member(message.chat.id, user.id)
            if mode == "kick":
                await client.unban_chat_member(message.chat.id, user.id)
        if delete and message.reply_to_message:
            await safe_delete(client, message.chat.id, message.reply_to_message.id)
        if not silent:
            result = "Mᴜᴛᴇᴅ" if mode == "mute" else "Bᴀɴɴᴇᴅ" if mode == "ban" else "Kɪᴄᴋᴇᴅ"
            await message.reply_text(f"<b>{result}:</b> {mention(user)}")
    except Exception as e:
        await message.reply_text(f"<b>Aᴄᴛɪᴏɴ Fᴀɪʟᴇᴅ:</b> <code>{type(e).__name__}</code>")

@Client.on_message(filters.text & filters.regex(r"^/(mute|dmute|smute|ban|dban|sban|kick|skick)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def punish_handler(client, message):
    cmd = command_match(message.text).group(1).lower()
    mode = "mute" if "mute" in cmd else "ban" if "ban" in cmd else "kick"
    await punish(client, message, mode, silent=cmd.startswith("s"), delete=cmd.startswith("d"))

@Client.on_message(filters.text & filters.regex(r"^/(unmute|unban)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def unpunish(client, message):
    cmd = command_match(message.text).group(1).lower()
    if not await action_ok(client, message, cmd):
        return
    parts = message.text.split()
    user = await resolve_user(client, message, parts[1] if len(parts) > 1 else None)
    if not user:
        return await message.reply_text("<b>Uꜱᴇ A Rᴇᴘʟʏ, Uꜱᴇʀɴᴀᴍᴇ Oʀ Uꜱᴇʀ ID.</b>")
    if not await bot_can(client, message.chat.id, "can_restrict_members"):
        return await message.reply_text("<b>Vᴇʏʀᴏ Nᴇᴇᴅꜱ Rᴇꜱᴛʀɪᴄᴛ Mᴇᴍʙᴇʀꜱ Pᴇʀᴍɪꜱꜱɪᴏɴ.</b>")
    try:
        if cmd == "unmute":
            permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
            await client.restrict_chat_member(message.chat.id, user.id, permissions=permissions)
        else:
            await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"<b>{'Uɴᴍᴜᴛᴇᴅ' if cmd == 'unmute' else 'Uɴʙᴀɴɴᴇᴅ'}:</b> {mention(user)}")
    except Exception as e:
        await message.reply_text(f"<b>Aᴄᴛɪᴏɴ Fᴀɪʟᴇᴅ:</b> <code>{type(e).__name__}</code>")

@Client.on_message(filters.text & filters.regex(r"^/(warn|unwarn|warns)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def warnings(client, message):
    cmd = command_match(message.text).group(1).lower()
    if not await action_ok(client, message, cmd):
        return
    parts = message.text.split(maxsplit=2)
    user = await resolve_user(client, message, parts[1] if len(parts) > 1 else None)
    if not user:
        return await message.reply_text("<b>Uꜱᴇ A Rᴇᴘʟʏ, Uꜱᴇʀɴᴀᴍᴇ Oʀ Uꜱᴇʀ ID.</b>")
    if cmd == "warns":
        doc = await client.db.get_warning(message.chat.id, user.id)
        return await message.reply_text(f"<b>Wᴀʀɴɪɴɢꜱ Fᴏʀ {mention(user)}:</b> {doc.get('count', 0)}")
    if cmd == "unwarn":
        count = await client.db.remove_warning(message.chat.id, user.id)
        return await message.reply_text(f"<b>Wᴀʀɴɪɴɢ Rᴇᴍᴏᴠᴇᴅ.</b> {count} Rᴇᴍᴀɪɴɪɴɢ.")
    count = await client.db.add_warning(message.chat.id, user.id, "Manual warning")
    if count >= 3:
        await client.ban_chat_member(message.chat.id, user.id)
        return await message.reply_text(f"<b>3 Wᴀʀɴɪɴɢꜱ Rᴇᴀᴄʜᴇᴅ.</b> {mention(user)} Wᴀꜱ Bᴀɴɴᴇᴅ.")
    await message.reply_text(f"<b>Wᴀʀɴɪɴɢ {count}/3:</b> {mention(user)}")

@Client.on_message(filters.text & filters.regex(r"^/(pin|unpin|d)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def message_actions(client, message):
    cmd = command_match(message.text).group(1).lower()
    if not await action_ok(client, message, cmd):
        return
    if cmd == "d" and not await bot_can(client, message.chat.id, "can_delete_messages"):
        return await message.reply_text("<b>Vᴇʏʀᴏ Nᴇᴇᴅꜱ Dᴇʟᴇᴛᴇ Mᴇꜱꜱᴀɢᴇꜱ Pᴇʀᴍɪꜱꜱɪᴏɴ.</b>")
    if cmd in ("pin", "unpin") and not await bot_can(client, message.chat.id, "can_pin_messages"):
        return await message.reply_text("<b>Vᴇʏʀᴏ Nᴇᴇᴅꜱ Pɪɴ Mᴇꜱꜱᴀɢᴇꜱ Pᴇʀᴍɪꜱꜱɪᴏɴ.</b>")
    try:
        if cmd == "pin":
            if not message.reply_to_message:
                return await message.reply_text("<b>Rᴇᴘʟʏ Tᴏ A Mᴇꜱꜱᴀɢᴇ Tᴏ Pɪɴ Iᴛ.</b>")
            await message.reply_to_message.pin()
        elif cmd == "unpin":
            await client.unpin_chat_message(message.chat.id)
        else:
            target = message.reply_to_message or message
            await client.delete_messages(message.chat.id, target.id)
            return
        await message.reply_text("<b>Aᴄᴛɪᴏɴ Cᴏᴍᴘʟᴇᴛᴇᴅ.</b>")
    except Exception as e:
        await message.reply_text(f"<b>Aᴄᴛɪᴏɴ Fᴀɪʟᴇᴅ:</b> <code>{type(e).__name__}</code>")

@Client.on_message(filters.text & filters.regex(r"^/(promote|demote|demote_all|title)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def admin_tools(client, message):
    cmd = command_match(message.text).group(1).lower()
    if not await action_ok(client, message, cmd):
        return
    if cmd == "demote_all":
        count = 0
        for user_id in await client.db.get_promoted_admins(message.chat.id):
            try:
                member = await client.get_chat_member(message.chat.id, user_id)
                if member.status == ChatMemberStatus.ADMINISTRATOR:
                    await client.promote_chat_member(message.chat.id, user_id, privileges=ChatPrivileges())
                    count += 1
                await client.db.clear_promoted(message.chat.id, user_id)
            except Exception:
                pass
        return await message.reply_text(f"<b>Dᴇᴍᴏᴛᴇᴅ:</b> {count}")
    parts = message.text.split(maxsplit=2)
    user = await resolve_user(client, message, parts[1] if len(parts) > 1 else None)
    if not user:
        return await message.reply_text("<b>Uꜱᴇ A Rᴇᴘʟʏ, Uꜱᴇʀɴᴀᴍᴇ Oʀ Uꜱᴇʀ ID.</b>")
    try:
        if cmd == "demote":
            await client.promote_chat_member(message.chat.id, user.id, privileges=ChatPrivileges())
            await client.db.clear_promoted(message.chat.id, user.id)
        elif cmd == "title":
            if len(parts) < 3:
                return await message.reply_text("<b>Uꜱᴇ /title &lt;user&gt; &lt;title&gt;.</b>")
            member = await client.get_chat_member(message.chat.id, user.id)
            privileges = member.privileges or ChatPrivileges()
            await client.promote_chat_member(message.chat.id, user.id, privileges=privileges, custom_title=parts[2][:16])
        else:
            try:
                level = int(parts[2]) if len(parts) > 2 else 0
            except ValueError:
                return await message.reply_text("<b>Lᴇᴠᴇʟ Mᴜꜱᴛ Bᴇ 0, 1, 2 Oʀ 3.</b>")
            if level not in (0, 1, 2, 3):
                return await message.reply_text("<b>Lᴇᴠᴇʟ Mᴜꜱᴛ Bᴇ 0, 1, 2 Oʀ 3.</b>")
            base = dict(can_manage_chat=True, can_delete_messages=True, can_invite_users=True)
            if level >= 1:
                base["can_restrict_members"] = True
            if level >= 2:
                base.update(can_pin_messages=True, can_manage_video_chats=True)
            if level >= 3:
                base.update(can_change_info=True, can_promote_members=True)
            await client.promote_chat_member(message.chat.id, user.id, privileges=ChatPrivileges(**base))
            await client.db.mark_promoted(message.chat.id, user.id)
        await message.reply_text("<b>Aᴅᴍɪɴ Aᴄᴛɪᴏɴ Cᴏᴍᴘʟᴇᴛᴇᴅ.</b>")
    except Exception as e:
        await message.reply_text(f"<b>Aᴅᴍɪɴ Aᴄᴛɪᴏɴ Fᴀɪʟᴇᴅ:</b> <code>{type(e).__name__}</code>")

@Client.on_message(filters.text & filters.regex(r"^/(add|remove|res)(?:@[A-Za-z0-9_]+)?(?:\s|$)"))
async def powers(client, message):
    cmd = command_match(message.text).group(1).lower()
    if not await action_ok(client, message, cmd):
        return
    parts = message.text.split()
    user = await resolve_user(client, message, parts[1] if len(parts) > 1 else None)
    if not user:
        return await message.reply_text("<b>Uꜱᴇ A Rᴇᴘʟʏ, Uꜱᴇʀɴᴀᴍᴇ Oʀ Uꜱᴇʀ ID.</b>")
    if cmd == "res":
        raw = parts[2] if len(parts) > 2 else ""
        enabled = not raw.startswith("-")
        power = raw.lstrip("+-").lower()
    else:
        if len(parts) < 3:
            return await message.reply_text("<b>Uꜱᴇ /add &lt;user&gt; &lt;power&gt; Oʀ /remove &lt;user&gt; &lt;power&gt;.</b>")
        power = parts[2].lower()
        enabled = cmd == "add"
    if power not in POWER_NAMES:
        return await message.reply_text("<b>Uɴᴋɴᴏᴡɴ Pᴏᴡᴇʀ.</b> Aᴠᴀɪʟᴀʙʟᴇ: info, delete, restrict, invite, pin, promote, manage.")
    await client.db.set_power(message.chat.id, user.id, power, enabled)
    await message.reply_text(f"<b>Pᴏᴡᴇʀ {'Eɴᴀʙʟᴇᴅ' if enabled else 'Dɪꜱᴀʙʟᴇᴅ'}:</b> {power}")

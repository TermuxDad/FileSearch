import re
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import RPCError

POWER_NAMES = {
    "info": "can_change_info",
    "delete": "can_delete_messages",
    "restrict": "can_restrict_members",
    "invite": "can_invite_users",
    "pin": "can_pin_messages",
    "promote": "can_promote_members",
    "manage": "can_manage_video_chats",
}
COMMAND_POWER = {
    "mute": "restrict", "dmute": "restrict", "smute": "restrict", "unmute": "restrict",
    "ban": "restrict", "dban": "restrict", "sban": "restrict", "unban": "restrict",
    "kick": "restrict", "skick": "restrict", "warn": "restrict", "unwarn": "restrict", "warns": "restrict",
    "pin": "pin", "unpin": "pin", "d": "delete",
    "promote": "promote", "demote": "promote", "demote_all": "promote", "title": "promote",
    "add": "promote", "remove": "promote", "res": "promote", "vctag": "manage",
}

def command_match(text):
    if not text:
        return None
    return re.match(r"^/([A-Za-z_]+)(?:@[A-Za-z0-9_]+)?(?:\s+(.*))?$", text.strip(), re.S)

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except RPCError:
        return False

async def is_owner(client, chat_id, user_id):
    try:
        return (await client.get_chat_member(chat_id, user_id)).status == ChatMemberStatus.OWNER
    except RPCError:
        return False

async def resolve_user(client, message, value=None):
    if message.reply_to_message and not value:
        return message.reply_to_message.from_user
    if not value:
        return None
    value = value.strip().lstrip("@")
    try:
        return await client.get_users(int(value))
    except (ValueError, RPCError):
        try:
            return await client.get_users(value)
        except RPCError:
            return None

def parse_duration(value):
    if not value:
        return None
    value = value.strip().lower()
    if value in ("0", "forever", "permanent", "perm"):
        return None
    match = re.fullmatch(r"(\d+)(s|m|h|d|w)", value)
    if not match:
        return None
    return int(match.group(1)) * {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[match.group(2)]

def mention(user):
    name = (getattr(user, "first_name", None) or "User").replace("<", "").replace(">", "")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"

async def safe_delete(client, chat_id, message_id):
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception:
        pass

async def require_admin(client, message):
    return bool(message.from_user and message.chat and await is_admin(client, message.chat.id, message.from_user.id))

async def require_owner(client, message):
    import config
    if not message.from_user:
        return False
    return message.from_user.id == config.OWNER_ID or bool(message.chat and await is_owner(client, message.chat.id, message.from_user.id))

async def require_power(client, message, command):
    if not message.from_user or not message.chat:
        return False
    import config
    if message.from_user.id == config.OWNER_ID:
        return True
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return False
        power = COMMAND_POWER.get(command)
        if not power:
            return True
        privileges = member.privileges
        if not privileges or not getattr(privileges, POWER_NAMES[power], False):
            return False
        saved = await client.db.get_powers(message.chat.id, message.from_user.id)
        return saved.get(power, True)
    except Exception:
        return False

async def bot_can(client, chat_id, permission):
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        return bool(member.privileges and getattr(member.privileges, permission, False))
    except Exception:
        return False

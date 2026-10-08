from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import RPCError

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except RPCError:
        return False

async def require_admin(client, message):
    return bool(message.from_user and message.chat and await is_admin(client, message.chat.id, message.from_user.id))

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
        if member.status != ChatMemberStatus.ADMINISTRATOR or not member.privileges:
            return False
        permission = "can_manage_video_chats" if command == "vctag" else None
        return True if not permission else bool(getattr(member.privileges, permission, False))
    except Exception:
        return False

def mention(user):
    name = (getattr(user, "first_name", None) or "User").replace("<", "").replace(">", "")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"

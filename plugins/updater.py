import asyncio
import os
import urllib.request
from pyrogram import Client, filters
import config

async def run_process(*args):
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")

@Client.on_message(filters.command("update") & filters.private)
async def update(client, message):
    if not message.from_user or message.from_user.id != config.OWNER_ID:
        return
    if os.getenv("RENDER", "").lower() == "true":
        if not config.RENDER_DEPLOY_HOOK:
            return await message.reply_text("<b>Rᴇɴᴅᴇʀ Uᴘᴅᴀᴛᴇ Hᴏᴏᴋ Iꜱ Nᴏᴛ Cᴏɴꜰɪɢᴜʀᴇᴅ.</b> Pᴜꜱʜ Tʜᴇ Lᴀᴛᴇꜱᴛ Cᴏᴅᴇ Tᴏ Gɪᴛʜᴜʙ Tᴏ Rᴇᴅᴇᴘʟᴏʏ.")
        try:
            req = urllib.request.Request(config.RENDER_DEPLOY_HOOK, method="POST")
            await asyncio.to_thread(urllib.request.urlopen, req, timeout=15)
            return await message.reply_text("<b>Rᴇɴᴅᴇʀ Dᴇᴘʟᴏʏ Tʀɪɢɢᴇʀᴇᴅ.</b>")
        except Exception as e:
            return await message.reply_text(f"<b>Dᴇᴘʟᴏʏ Fᴀɪʟᴇᴅ:</b> <code>{type(e).__name__}</code>")
    if not config.GITHUB_REPO:
        return await message.reply_text("<b>GITHUB_REPO Iꜱ Nᴏᴛ Cᴏɴꜰɪɢᴜʀᴇᴅ.</b>")
    await message.reply_text("<b>Uᴘᴅᴀᴛᴇ Cʜᴇᴄᴋ Sᴛᴀʀᴛᴇᴅ.</b>")
    code, _, err = await run_process("git", "fetch", "origin", config.GITHUB_BRANCH)
    if code != 0:
        return await message.reply_text(f"<b>Fᴇᴛᴄʜ Fᴀɪʟᴇᴅ:</b> <code>{err[-300:]}</code>")
    code, _, err = await run_process("git", "reset", "--hard", f"origin/{config.GITHUB_BRANCH}")
    if code != 0:
        return await message.reply_text(f"<b>Uᴘᴅᴀᴛᴇ Fᴀɪʟᴇᴅ:</b> <code>{err[-300:]}</code>")
    await message.reply_text("<b>Uᴘᴅᴀᴛᴇ Aᴘᴘʟɪᴇᴅ.</b> Rᴇꜱᴛᴀʀᴛ Tʜᴇ Bᴏᴛ Tᴏ Fɪɴɪꜱʜ.")

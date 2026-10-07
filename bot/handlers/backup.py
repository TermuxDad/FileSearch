from __future__ import annotations

import asyncio
from pyrogram import filters


def register(app, db, config):
    @app.on_message(filters.command("backup") & filters.private)
    async def backup_command(_, message):
        if message.from_user.id not in config.OWNER_IDS:
            await message.reply_text("⛔ Owner only.")
            return
        manager = getattr(app, "_zombie_backup_manager", None)
        if not manager or not manager.enabled:
            await message.reply_text("⚠️ Telegram backup is not configured.")
            return
        await message.reply_text("🗄 Creating a database backup... Please wait.")
        try:
            result = await manager.create_backup(reason="manual")
            await message.reply_text(
                "✅ <b>Backup completed.</b>\n\n"
                f"👥 Players: <b>{result['players']:,}</b>\n"
                f"📦 Compressed: <b>{result['compressed_bytes']:,} bytes</b>\n"
                f"🔐 SHA-256: <code>{result['sha256']}</code>"
            )
        except Exception as exc:
            await message.reply_text(f"❌ Backup failed: <code>{type(exc).__name__}</code>")

    @app.on_message(filters.command("backupstatus") & filters.private)
    async def backup_status(_, message):
        if message.from_user.id not in config.OWNER_IDS:
            await message.reply_text("⛔ Owner only.")
            return
        manager = getattr(app, "_zombie_backup_manager", None)
        if not manager:
            await message.reply_text("⚠️ Backup manager is not running yet.")
            return
        status = await manager.status()
        latest = status.get("latest") or {}
        await message.reply_text(
            "🛡 <b>Backup Status</b>\n\n"
            f"Status: <b>{'ON' if status['enabled'] else 'OFF'}</b>\n"
            f"Interval: <b>{status['interval_seconds']}s</b>\n"
            f"Auto restore: <b>{'ON' if status['auto_restore'] else 'OFF'}</b>\n"
            f"Latest backup: <b>{latest.get('created_at', 'None')}</b>\n"
            f"Players: <b>{latest.get('players', 0):,}</b>\n"
            f"Size: <b>{latest.get('compressed_bytes', 0):,} bytes</b>"
        )

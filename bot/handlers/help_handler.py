from pyrogram import filters
from .common import back_home

def register_help(app, db):
    @app.on_message(filters.command("help"))
    async def help_command(_, message):
        await message.reply_text(
            "❓ <b>ZOMBIE SURVIVAL HELP</b>\n\n"
            "Use /start to open the game menu. In groups, use /raid to start a Horde raid.",
            reply_markup=back_home(),
        )

    @app.on_callback_query(filters.regex(r"^home:help$"))
    async def help_menu(_, q):
        text = (
            "❓ <b>HOW TO PLAY</b>\n\n"
            "🧟 <b>Hunt:</b> Fight zombies for XP and coins.\n"
            "🗺️ <b>Explore:</b> Visit locations for stronger enemies and better loot.\n"
            "🏪 <b>Shop:</b> Buy and equip weapons and armor.\n"
            "🎯 <b>Missions:</b> Complete daily and weekly objectives for rewards.\n"
            "⬆️ <b>Upgrades:</b> Upgrade your equipped weapon and armor using coins + scrap.\n"
            "☣️ <b>Raid:</b> In a group, use /raid and team up against the Horde.\n"
            "🏆 <b>Leaderboard:</b> Compete for the highest level and XP.\n\n"
            "<b>Energy</b> regenerates over time. Keep your HP healthy and upgrade regularly."
        )
        await q.message.edit_text(text, reply_markup=back_home())
        await q.answer()

    @app.on_callback_query(filters.regex(r"^home$"))
    async def home(_, q):
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        from .common import home_kb
        await q.message.edit_text(
            f"🧟 <b>ZOMBIE SURVIVAL</b>\n\n"
            f"❤️ {p['hp']}/{p['max_hp']}   ⚡ {p['energy']}/{p['max_energy']}   💰 {p['coins']:,}\n"
            f"⭐ Level {p['level']}\n\nChoose an action:",
            reply_markup=home_kb(),
        )
        await q.answer()

    @app.on_callback_query(filters.regex(r"^home:daily$"))
    async def daily(_, q):
        from datetime import datetime, timezone
        p = await db.get_player(q.from_user.id, q.from_user.first_name, q.from_user.username or "")
        last = p.get("last_daily")
        now = datetime.now(timezone.utc)
        if last and last.date() == now.date():
            await q.message.edit_text(
                "🎁 <b>DAILY REWARD</b>\n\nYou already claimed today's reward. Come back tomorrow.",
                reply_markup=back_home(),
            )
            await q.answer()
            return
        await db.update_player(
            q.from_user.id,
            {"$inc": {"coins": 1000, "coins_earned": 1000, "energy": 25}, "$set": {"last_daily": now}},
        )
        # Daily reward contributes to the daily/weekly coin missions.
        from .missions import record_progress
        await record_progress(db, q.from_user.id, "coins", 1000)
        await q.message.edit_text(
            "🎉 <b>DAILY REWARD CLAIMED!</b>\n\n💰 +1,000 coins\n⚡ +25 energy",
            reply_markup=back_home(),
        )
        await q.answer()

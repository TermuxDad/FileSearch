import asyncio
import html
import random
import time
import secrets
from datetime import datetime, timezone

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton

from .data import weapon_attack, armor_defense
from .engine import apply_xp

CHALLENGE_TTL = 120
FIGHT_TTL = 900
TURN_TTL = 60

# Process-local locks stop double-click/race conditions while the bot is running.
_FIGHT_LOCKS = {}


def challenge_id():
    return secrets.token_hex(6)


def fight_id():
    return secrets.token_hex(6)


def _lock_for(fid):
    return _FIGHT_LOCKS.setdefault(fid, asyncio.Lock())


def power(p):
    return (
        weapon_attack(p["weapon"]) * (1 + 0.08 * int(p.get("weapon_upgrade", 0)))
        + armor_defense(p["armor"]) * 0.35
    )


def hit_damage(p, heavy=False, bloodlust=0):
    base = weapon_attack(p["weapon"]) * (1 + 0.08 * int(p.get("weapon_upgrade", 0)))
    mult = random.uniform(0.82, 1.18)
    if heavy:
        mult *= 1.55
    mult *= 1 + min(0.20, int(bloodlust) / 100)
    return max(2, int(base * mult))


def crit(p):
    return random.random() < min(0.35, 0.08 + 0.01 * int(p.get("pvp_wins", 0)) ** 0.5)


def normalize_target(player, target):
    return player and target and player["user_id"] != target["user_id"]


async def create_challenge(db, challenger, target):
    now = int(time.time())
    cid = challenge_id()
    doc = {
        "challenge_id": cid,
        "from": challenger["user_id"],
        "to": target["user_id"],
        "created_at": now,
        "expires_at": now + CHALLENGE_TTL,
        "status": "pending",
    }
    await db.db.pvp_challenges.insert_one(doc)
    return doc


async def create_fight(db, a, b, chat_id=None, message_id=None, battle_is_group=False, battle_chat_username=None):
    now = int(time.time())
    fid = fight_id()
    doc = {
        "fight_id": fid,
        "a": a["user_id"],
        "b": b["user_id"],
        "hp": {
            str(a["user_id"]): a["max_hp"],
            str(b["user_id"]): b["max_hp"],
        },
        "turn": a["user_id"],
        "round": 1,
        "created_at": now,
        "expires_at": now + FIGHT_TTL,
        "turn_expires_at": now + TURN_TTL,
        "log": [],
        "status": "active",
        "battle_chat_id": chat_id,
        "battle_message_id": message_id,
        "battle_is_group": bool(battle_is_group),
        "battle_chat_username": battle_chat_username,
        "turn_notice_chat_id": chat_id if battle_is_group else None,
        "turn_notice_message_id": None,
    }
    await db.db.pvp_fights.insert_one(doc)
    return doc


def other(f, uid):
    return f["b"] if int(uid) == int(f["a"]) else f["a"]


def combat_hp(f, uid):
    return int(f["hp"].get(str(uid), 0))


def action_result(f, attacker, defender, action, ap, dp):
    if action == "dodge":
        f["dodge_user"] = attacker
        return f"💨 <b>{html.escape(ap['name'])}</b> prepares to dodge."

    if action == "defend":
        f["defend_user"] = attacker
        return f"🛡️ <b>{html.escape(ap['name'])}</b> takes a defensive stance."

    if action == "heal":
        heal = min(25, max(0, ap["max_hp"] - combat_hp(f, attacker)))
        if heal <= 0:
            return None
        f["hp"][str(attacker)] = combat_hp(f, attacker) + heal
        return f"🧪 <b>{html.escape(ap['name'])}</b> recovered <b>{heal}</b> HP."

    heavy = action == "heavy"
    damage = hit_damage(ap, heavy, int(ap.get("bloodlust", 0)))

    if crit(ap):
        damage = int(damage * 1.75)
        critical = True
    else:
        critical = False

    if f.get("dodge_user") == defender:
        damage = 0
        f.pop("dodge_user", None)
        result = (
            f"💨 <b>{html.escape(dp['name'])}</b> dodged "
            f"<b>{html.escape(ap['name'])}</b>'s attack!"
        )
        return result

    if f.get("defend_user") == defender:
        damage = max(1, damage // 2)
        f.pop("defend_user", None)

    f["hp"][str(defender)] = max(0, combat_hp(f, defender) - damage)
    tag = " 💥 <b>CRITICAL!</b>" if critical else ""
    attack_name = "Heavy Attack" if heavy else "Strike"
    return (
        f"⚔️ <b>{html.escape(ap['name'])}</b> used "
        f"<b>{attack_name}</b> → <b>{damage}</b> damage to "
        f"<b>{html.escape(dp['name'])}</b>.{tag}"
    )


def _mention(user):
    name = html.escape(user.get("name") or "Survivor")
    uid = int(user["user_id"])
    username = (user.get("username") or "").strip().lstrip("@")
    if username:
        return f"@{html.escape(username)}"
    return f'<a href="tg://user?id={uid}">{name}</a>'


def _jump_url(chat_id, message_id, username=None):
    if not chat_id or not message_id:
        return None
    if username:
        return f"https://t.me/{username.lstrip('@')}/{int(message_id)}"
    chat_id = int(chat_id)
    if chat_id < -1000000000000:
        internal = str(abs(chat_id) - 1000000000000)
        return f"https://t.me/c/{internal}/{int(message_id)}"
    return None


async def _delete_turn_notice(app, f):
    mid = f.get("turn_notice_message_id")
    chat_id = f.get("turn_notice_chat_id") or f.get("battle_chat_id")
    if not mid or not chat_id:
        return
    try:
        await app.delete_messages(chat_id, mid)
    except Exception:
        # Deleting the previous notice is an anti-spam optimisation only.
        pass
    f["turn_notice_message_id"] = None


async def _send_turn_notice(app, db, f, player):
    chat_id = f.get("battle_chat_id")
    if not chat_id or not f.get("battle_is_group"):
        return

    await _delete_turn_notice(app, f)

    username = f.get("battle_chat_username")
    link = _jump_url(chat_id, f.get("battle_message_id"), username)
    buttons = []
    if link:
        buttons.append(
            InlineKeyboardButton("⚔️ OPEN LIVE BATTLE", url=link)
        )

    who = _mention(player)
    text = (
        f"🔔 <b>{who}</b> — <b>YOUR TURN!</b>\n"
        f"⚔️ The duel is live. Make your move now."
    )

    try:
        msg = await app.send_message(
            chat_id,
            text,
            reply_markup=(
                __import__("pyrogram.types", fromlist=["InlineKeyboardMarkup"])
                .InlineKeyboardMarkup([buttons])
                if buttons else None
            ),
        )
        f["turn_notice_message_id"] = msg.id
        f["turn_notice_chat_id"] = chat_id
    except Exception:
        # The fight itself must never fail because a notification could not be sent.
        pass


def render(f, a, b, last_action=None):
    turn_player = a if int(f["turn"]) == int(a["user_id"]) else b
    a_hp = combat_hp(f, a["user_id"])
    b_hp = combat_hp(f, b["user_id"])

    logs = f.get("log") or []
    log_text = "\n".join(f"• {x}" for x in logs[-6:]) or "• The duel has just started."

    return (
        "⚔️ <b>DEADLY DUEL — LIVE</b>\n\n"
        f"👤 <b>{html.escape(a['name'])}</b> — ❤️ <b>{a_hp}/{a['max_hp']}</b>\n"
        f"👤 <b>{html.escape(b['name'])}</b> — ❤️ <b>{b_hp}/{b['max_hp']}</b>\n\n"
        f"🎯 <b>TURN:</b> {html.escape(turn_player['name'])}\n"
        f"⏳ <b>Turn timer:</b> {max(0, int(f.get('turn_expires_at', time.time()) - time.time()))}s\n"
        f"🔥 <b>Round:</b> {f.get('round', 1)}\n\n"
        "📜 <b>LIVE BATTLE LOG</b>\n"
        f"{log_text}\n\n"
        "👀 <i>Spectators can watch every move live in this message.</i>\n"
        "⚠️ Only the player whose turn it is can use the action buttons."
    )


def fight_kb(fid):
    from .common import btn, kb

    return kb([
        [btn("🟢 ⚔️ Strike", f"pvpact:{fid}:strike"),
         btn("🔴 💥 Heavy", f"pvpact:{fid}:heavy")],
        [btn("🔵 🛡️ Defend", f"pvpact:{fid}:defend"),
         btn("🔵 💨 Dodge", f"pvpact:{fid}:dodge")],
        [btn("🟢 🧪 Heal", f"pvpact:{fid}:heal"),
         btn("🔴 🏳️ Surrender", f"pvpact:{fid}:surrender")],
    ])


async def finish(app, db, f, winner, loser, reason="victory"):
    if f.get("status") != "active":
        return None

    f["status"] = "finished"
    f["winner"] = winner["user_id"]
    f["loser"] = loser["user_id"]
    f["finish_reason"] = reason

    wp = await db.get_player(winner["user_id"])
    lp = await db.get_player(loser["user_id"])

    coin = max(100, min(10000, int(lp.get("coins", 0) * 0.05))) if lp.get("coins", 0) > 0 else 0
    bounty = int(lp.get("bounty", 0))
    total = coin + bounty

    wxp, wl, wmh, wme, _ = apply_xp(wp, 250)
    await db.update_player(
        winner["user_id"],
        {
            "$inc": {
                "pvp_wins": 1,
                "pvp_streak": 1,
                "reputation": 25,
                "coins": total,
                "coins_earned": total,
                "bounties_claimed": 1 if bounty else 0,
                "bloodlust": 10,
            },
            "$set": {
                "xp": wxp,
                "level": wl,
                "max_hp": wmh,
                "max_energy": wme,
                "bounty": 0,
            },
        },
    )

    best = max(
        int(wp.get("best_streak", 0)),
        int(wp.get("pvp_streak", 0)) + 1,
    )
    await db.update_player(winner["user_id"], {"$set": {"best_streak": best}})

    await db.update_player(
        loser["user_id"],
        {
            "$inc": {"pvp_losses": 1, "reputation": -10},
            "$set": {
                "pvp_streak": 0,
                "rival_user_id": winner["user_id"],
                "injury_until": int(time.time()) + 300,
            },
        },
    )

    from .missions import record_progress

    await record_progress(db, winner["user_id"], "pvp_wins", 1)

    key = ":".join(
        map(str, sorted([winner["user_id"], loser["user_id"]]))
    )
    await db.db.rivalries.update_one(
        {"key": key},
        {
            "$set": {
                "key": key,
                "a": min(winner["user_id"], loser["user_id"]),
                "b": max(winner["user_id"], loser["user_id"]),
                "last_winner": winner["user_id"],
            },
            "$inc": {
                "fights": 1,
                "a_wins": 1 if winner["user_id"] == min(winner["user_id"], loser["user_id"]) else 0,
                "b_wins": 1 if winner["user_id"] == max(winner["user_id"], loser["user_id"]) else 0,
            },
        },
        upsert=True,
    )

    await _delete_turn_notice(app, f)
    await db.db.pvp_fights.delete_one({"fight_id": f["fight_id"]})

    text = (
        "☠️ <b>DUEL OVER</b>\n\n"
        f"🏆 Winner: <b>{html.escape(winner['name'])}</b>\n"
        f"💀 Defeated: <b>{html.escape(loser['name'])}</b>\n\n"
        f"💰 Loot: <b>+{total:,}</b> coins\n"
        "⭐ XP: <b>+250</b>\n"
        f"🔥 Streak: <b>{best}</b>\n"
        f"☠️ Reason: <b>{html.escape(reason)}</b>"
    )

    # Group battles get a public final result. Private duels still get private results.
    chat_id = f.get("battle_chat_id")
    if chat_id and not (f.get("battle_is_group") and f.get("battle_message_id")):
        try:
            await app.send_message(chat_id, text)
        except Exception:
            pass

    # Keep personal result notifications as a convenience.
    try:
        await app.send_message(winner["user_id"], text)
    except Exception:
        pass
    try:
        await app.send_message(loser["user_id"], text)
    except Exception:
        pass

    _FIGHT_LOCKS.pop(f["fight_id"], None)
    return text


async def _timeout_fight(app, db, fid):
    lock = _lock_for(fid)
    async with lock:
        f = await db.db.pvp_fights.find_one({"fight_id": fid})
        if not f or f.get("status") != "active":
            return
        if int(time.time()) < int(f.get("turn_expires_at", f.get("expires_at", 0))):
            return

        a = await db.get_player(f["a"])
        b = await db.get_player(f["b"])
        if not a or not b:
            return

        winner = b if int(f["turn"]) == int(a["user_id"]) else a
        loser = a if winner["user_id"] == b["user_id"] else b
        text = await finish(app, db, f, winner, loser, "turn timeout")

        if text and f.get("battle_chat_id") and f.get("battle_message_id"):
            try:
                await app.edit_message_text(
                    f["battle_chat_id"],
                    f["battle_message_id"],
                    text,
                    reply_markup=None,
                )
            except Exception:
                pass


def _schedule_turn_timeout(app, db, f):
    async def runner():
        delay = max(0, int(f.get("turn_expires_at", time.time())) - int(time.time())) + 1
        await asyncio.sleep(delay)
        await _timeout_fight(app, db, f["fight_id"])

    task = asyncio.create_task(runner())
    return task


async def restore_fights(app, db):
    fights = await db.db.pvp_fights.find({"status": "active"}).to_list(length=None)
    for f in fights:
        # Global fight timeout is also enforced after a restart.
        if int(time.time()) >= int(f.get("expires_at", 0)):
            a = await db.get_player(f["a"])
            b = await db.get_player(f["b"])
            if a and b:
                lock = _lock_for(f["fight_id"])
                async with lock:
                    fresh = await db.db.pvp_fights.find_one({"fight_id": f["fight_id"]})
                    if fresh and fresh.get("status") == "active":
                        winner = b if fresh["turn"] == a["user_id"] else a
                        loser = a if winner["user_id"] == b["user_id"] else b
                        await finish(app, db, fresh, winner, loser, "duel expired")
        else:
            _schedule_turn_timeout(app, db, f)


def register(app, db):
    @app.on_callback_query(filters.regex(r"^home:pvp$"))
    async def pvp_menu(_, q):
        await q.message.edit_text(
            "⚔️ <b>PVP ARENA</b>\n\n"
            "Challenge another player with <code>/duel</code> by replying to their message.\n\n"
            "In groups, accepted duels become a <b>LIVE BATTLE</b>: one shared message is updated after every move, while a small turn alert keeps the active player from losing the fight in chat.",
            reply_markup=__import__("bot.handlers.common", fromlist=["kb", "btn"]).kb([
                [__import__("bot.handlers.common", fromlist=["btn"]).btn("🔴 ☠️ Wanted Players", "home:wanted")],
                [__import__("bot.handlers.common", fromlist=["btn"]).btn("🔵 🏠 Home", "home")],
            ]),
        )
        await q.answer()

    @app.on_message(filters.command("duel"))
    async def duel(_, m):
        if not m.from_user:
            return

        target = None
        if m.reply_to_message and m.reply_to_message.from_user:
            target = m.reply_to_message.from_user
        elif len(m.command) > 1 and m.command[1].isdigit():
            try:
                target = await app.get_users(int(m.command[1]))
            except Exception:
                target = None

        if not target or target.is_bot or target.id == m.from_user.id:
            await m.reply_text(
                "⚔️ Reply to a player message and use /duel, or use /duel USER_ID."
            )
            return

        a = await db.get_player(
            m.from_user.id,
            m.from_user.first_name,
            m.from_user.username or "",
        )
        b = await db.get_player(
            target.id,
            target.first_name,
            target.username or "",
        )

        now = int(time.time())
        if a.get("injury_until", 0) and int(a["injury_until"]) > now:
            await m.reply_text("🩹 You are injured. Heal before dueling.")
            return
        if b.get("injury_until", 0) and int(b["injury_until"]) > now:
            await m.reply_text("🩹 That player is currently injured.")
            return

        existing = await db.db.pvp_fights.find_one({
            "$or": [{"a": a["user_id"]}, {"b": a["user_id"]}],
            "status": "active",
        })
        if existing:
            await m.reply_text("⚔️ You already have an active duel.")
            return

        existing = await db.db.pvp_fights.find_one({
            "$or": [{"a": b["user_id"]}, {"b": b["user_id"]}],
            "status": "active",
        })
        if existing:
            await m.reply_text("⚔️ That player is already in an active duel.")
            return

        c = await create_challenge(db, a, b)
        await m.reply_text(
            f"⚔️ <b>DUEL CHALLENGE</b>\n\n"
            f"<b>{html.escape(a['name'])}</b> challenges <b>{html.escape(b['name'])}</b>.\n"
            "👥 If this is a group, everyone can watch the duel live after acceptance.\n"
            "⏱️ Expires in 2 minutes.",
            reply_markup=__import__("bot.handlers.common", fromlist=["kb", "btn"]).kb([
                [
                    __import__("bot.handlers.common", fromlist=["btn"]).btn(
                        "🟢 Accept", f"pvpaccept:{c['challenge_id']}"
                    ),
                    __import__("bot.handlers.common", fromlist=["btn"]).btn(
                        "🔴 Decline", f"pvpdecline:{c['challenge_id']}"
                    ),
                ]
            ]),
        )

    @app.on_callback_query(filters.regex(r"^pvpaccept:([0-9a-f]+)$"))
    async def accept(_, q):
        cid = q.matches[0].group(1)
        c = await db.db.pvp_challenges.find_one({"challenge_id": cid})

        if not c or c["status"] != "pending" or int(time.time()) > c["expires_at"]:
            await q.answer("Challenge expired.", show_alert=True)
            return
        if q.from_user.id != c["to"]:
            await q.answer("Only the challenged player can accept.", show_alert=True)
            return

        # One final check prevents a player from entering two simultaneous duels.
        active = await db.db.pvp_fights.find_one({
            "$or": [{"a": q.from_user.id}, {"b": q.from_user.id}],
            "status": "active",
        })
        if active:
            await q.answer("You already have an active duel.", show_alert=True)
            return

        a = await db.get_player(c["from"])
        b = await db.get_player(c["to"])
        f = await create_fight(
            db,
            a,
            b,
            chat_id=q.message.chat.id if q.message else None,
            message_id=q.message.id if q.message else None,
            battle_is_group=bool(
                q.message and getattr(q.message.chat, "type", None) in ("group", "supergroup")
            ),
            battle_chat_username=(
                getattr(q.message.chat, "username", None)
                if q.message else None
            ),
        )
        await db.db.pvp_challenges.update_one(
            {"challenge_id": cid, "status": "pending"},
            {"$set": {"status": "accepted"}},
        )

        # The original challenge message becomes the one permanent live battle message.
        await q.message.edit_text(
            render(f, a, b),
            reply_markup=fight_kb(f["fight_id"]),
        )
        await _send_turn_notice(app, db, f, a)
        await db.db.pvp_fights.update_one(
            {"fight_id": f["fight_id"]},
            {
                "$set": {
                    "turn_notice_message_id": f.get("turn_notice_message_id"),
                    "turn_notice_chat_id": f.get("turn_notice_chat_id"),
                }
            },
        )
        _schedule_turn_timeout(app, db, f)
        await q.answer("⚔️ Duel accepted! Live battle started.")

    @app.on_callback_query(filters.regex(r"^pvpdecline:([0-9a-f]+)$"))
    async def decline(_, q):
        cid = q.matches[0].group(1)
        c = await db.db.pvp_challenges.find_one({"challenge_id": cid})
        if not c or q.from_user.id != c["to"]:
            await q.answer("Invalid challenge.", show_alert=True)
            return
        await db.db.pvp_challenges.update_one(
            {"challenge_id": cid},
            {"$set": {"status": "declined"}},
        )
        await q.message.edit_text("🏳️ <b>Duel declined.</b>")
        await q.answer()

    @app.on_callback_query(
        filters.regex(r"^pvpact:([0-9a-f]+):(strike|heavy|defend|dodge|heal|surrender)$")
    )
    async def act(_, q):
        fid = q.matches[0].group(1)
        action = q.matches[0].group(2)
        lock = _lock_for(fid)

        async with lock:
            f = await db.db.pvp_fights.find_one({"fight_id": fid})

            if not f or f.get("status") != "active":
                await q.answer("Duel is over.", show_alert=True)
                return

            uid = q.from_user.id
            if uid not in (f["a"], f["b"]):
                await q.answer("This duel is not yours.", show_alert=True)
                return
            if uid != f["turn"]:
                await q.answer("Wait for your turn.", show_alert=True)
                return

            now = int(time.time())
            if now >= int(f.get("expires_at", 0)):
                a = await db.get_player(f["a"])
                b = await db.get_player(f["b"])
                winner = b if f["turn"] == a["user_id"] else a
                loser = a if winner["user_id"] == b["user_id"] else b
                text = await finish(app, db, f, winner, loser, "duel expired")
                if text:
                    await q.message.edit_text(text, reply_markup=None)
                await q.answer("Duel expired.", show_alert=True)
                return

            if now >= int(f.get("turn_expires_at", 0)):
                a = await db.get_player(f["a"])
                b = await db.get_player(f["b"])
                winner = b if f["turn"] == a["user_id"] else a
                loser = a if winner["user_id"] == b["user_id"] else b
                text = await finish(app, db, f, winner, loser, "turn timeout")
                if text:
                    await q.message.edit_text(text, reply_markup=None)
                await q.answer("Turn timed out.", show_alert=True)
                return

            a = await db.get_player(f["a"])
            b = await db.get_player(f["b"])
            ap = a if uid == a["user_id"] else b
            dp = b if uid == a["user_id"] else a

            if action == "surrender":
                text = await finish(app, db, f, dp, ap, "surrender")
                if text:
                    await q.message.edit_text(text, reply_markup=None)
                await q.answer("You surrendered the duel.", show_alert=True)
                return

            result = action_result(f, uid, dp["user_id"], action, ap, dp)
            if result is None:
                await q.answer("That action cannot be used now.", show_alert=True)
                return

            f["log"] = (f.get("log") or [])[-5:] + [result]

            if combat_hp(f, dp["user_id"]) <= 0:
                # Persist the knockout state before awarding rewards.
                await db.db.pvp_fights.replace_one({"fight_id": fid}, f)
                text = await finish(app, db, f, ap, dp, "knockout")
                if text:
                    await q.message.edit_text(text, reply_markup=None)
                await q.answer("☠️ Knockout!", show_alert=True)
                return

            f["turn"] = dp["user_id"]
            f["round"] = int(f.get("round", 1)) + 1
            f["turn_expires_at"] = int(time.time()) + TURN_TTL

            await db.db.pvp_fights.replace_one({"fight_id": fid}, f)
            await q.message.edit_text(
                render(f, a, b, result),
                reply_markup=fight_kb(fid),
            )

            next_player = b if f["turn"] == b["user_id"] else a
            await _send_turn_notice(app, db, f, next_player)

            await db.db.pvp_fights.update_one(
                {"fight_id": fid, "status": "active"},
                {
                    "$set": {
                        "turn_notice_message_id": f.get("turn_notice_message_id"),
                        "turn_notice_chat_id": f.get("turn_notice_chat_id"),
                    }
                },
            )

            _schedule_turn_timeout(app, db, f)
            await q.answer("Move registered!")

    app._zombie_restore_pvp = lambda: restore_fights(app, db)

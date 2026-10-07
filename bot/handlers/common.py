from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

try:
    from pyrogram.enums import ButtonStyle
except Exception:
    ButtonStyle = None


def kb(rows):
    return InlineKeyboardMarkup(rows)


def _style_from_text(text):
    if ButtonStyle is None:
        return None
    if text.startswith("🔴"):
        return ButtonStyle.DANGER
    if text.startswith("🟢"):
        return ButtonStyle.SUCCESS
    if text.startswith("🔵"):
        return ButtonStyle.PRIMARY
    # Neutral actions use the primary style so the whole UI remains consistent.
    return ButtonStyle.PRIMARY


def btn(text, data, style=None):
    kwargs = {"text": text, "callback_data": data}
    resolved = style or _style_from_text(text)
    if resolved is not None:
        kwargs["style"] = resolved
    return InlineKeyboardButton(**kwargs)


def home_kb():
    return kb([
        [btn("🔵 🎮 Play", "home:play"), btn("🔵 👤 Profile", "home:profile")],
        [btn("🟢 🎒 Inventory", "home:inventory"), btn("🟢 🏪 Shop", "home:shop")],
        [btn("🟢 🎯 Missions", "home:missions"), btn("🔵 🗺️ Explore", "home:explore")],
        [btn("🟢 🏆 Leaderboard", "home:leaderboard"), btn("🔵 🎁 Daily", "home:daily")],
        [btn("🔴 ❓ Help", "home:help")],
    ])


def back_home():
    return kb([[btn("🔵 🏠 Home", "home")]])


def back_to(section):
    return kb([[btn("🔵 ⬅️ Back", section), btn("🔵 🏠 Home", "home")]])


def safe_name(user):
    return (user.first_name or "Survivor").replace("<", "").replace(">", "")[:32]

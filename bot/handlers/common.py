from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
try:
    from pyrogram.enums import ButtonStyle
except Exception:
    ButtonStyle=None

def kb(rows): return InlineKeyboardMarkup(rows)
def _style(text):
    if ButtonStyle is None: return None
    if text.startswith("🔴"): return ButtonStyle.DANGER
    if text.startswith("🟢"): return ButtonStyle.SUCCESS
    return ButtonStyle.PRIMARY

def btn(text,data,style=None):
    kw={"text":text,"callback_data":data}; s=style or _style(text)
    if s is not None: kw["style"]=s
    return InlineKeyboardButton(**kw)

def home_kb():
    return kb([
      [btn("🔵 🎮 Play","home:play"),btn("🔵 👤 Profile","home:profile")],
      [btn("🟢 ⚔️ PvP","home:pvp"),btn("🔴 ☠️ Wanted","home:wanted")],
      [btn("🟢 🎒 Inventory","home:inventory"),btn("🟢 🏪 Shop","home:shop")],
      [btn("🟢 🎯 Missions","home:missions"),btn("🔵 🗺️ Explore","home:explore")],
      [btn("🟢 👑 Clan","home:clan"),btn("🔵 🌑 Events","home:event")],
      [btn("🟢 🏆 Leaderboard","home:leaderboard"),btn("🔵 🎁 Daily","home:daily")],
      [btn("🔴 ❓ Help","home:help")],
    ])
def back_home(): return kb([[btn("🔵 🏠 Home","home")]])
def back_to(section): return kb([[btn("🔵 ⬅️ Back",section),btn("🔵 🏠 Home","home")]])
def safe_name(user): return (user.first_name or "Survivor").replace("<","").replace(">","")[:32]

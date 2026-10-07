# 🧟 Zombie Survival RPG — V2 Apocalypse PvP

Telegram group + private RPG built with Python, Kurigram, MongoDB and Render.

## V2 gameplay

- 🧟 20 zombie types, hunting and exploration
- 🔫 30 weapons + 🛡️ 20 armor pieces
- ⬆️ Real weapon/armor upgrades
- 🎒 Inventory, medical items and economy
- ⭐ XP, levels, missions and daily rewards
- ⚔️ **Turn-based PvP duels** with Strike, Heavy, Defend, Dodge, Heal and Surrender
- 📺 **Live group PvP:** one shared battle message updates every move, with a single rotating `YOUR TURN` alert and a live-battle jump button
- ☠️ **Bounties / Most Wanted**
- 🔥 PvP streaks, reputation and rivalries
- 👑 **Clans** with members and clan bank
- 🏰 **Territory capture**
- ⚔️ **Clan wars** with attack buttons and victory rewards
- 🌑 Rotating six-hour apocalypse events
- ☣️ Group Horde raids with persistent state and restart recovery
- 🏆 Global + group leaderboards
- 🛡️ Owner/admin controls
- 💾 MongoDB persistence
- 🗄️ Telegram disaster-recovery backups including V2 collections
- 🚀 Render health endpoint and deployment config

## Commands

- `/start` or `/menu` — main menu
- `/help` — complete help
- `/duel` — reply to a player to challenge them
- `/bounty AMOUNT` — reply to a player to place a bounty
- `/clan create NAME`
- `/clan join CLAN_ID`
- `/clan donate AMOUNT`
- `/clan leave`
- `/clanwar CLAN_ID`
- `/clanwarattack`
- `/raid` — group Horde raid
- `/backup` — owner manual backup
- `/backupstatus` — owner backup status
- `/stats`, `/givecoins`, `/setlevel`, `/heal` — owner tools

## Environment

Required:

```text
BOT_TOKEN=
API_ID=
API_HASH=
MONGO_URI=
```

Optional:

```text
MONGO_DB=zombie_survival
OWNER_IDS=123456789
BACKUP_CHAT_ID=-1001234567890
BACKUP_INTERVAL_SECONDS=900
BACKUP_KEEP=12
AUTO_RESTORE=true
```

## Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Render

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
python main.py
```

The included `render.yaml` configures the web health endpoint.

## Safety / game design

PvP is fictional in-game combat. It uses bounded virtual coin/loot stakes only; there are no real-money wagers. The goal is high-stakes competition without making real-world harm or gambling part of the game.

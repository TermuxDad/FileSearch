# 🧟 Zombie Survival — Telegram Game Bot V1

Python + Kurigram + MongoDB. Designed for Render Web Service deployment.

## V1 Features
- Player profile, XP, levels, HP and energy
- Zombie hunting with turn-based combat
- 20 zombie types
- 30 weapons and 20 armor items, all accessible through paginated shop pages
- Inventory and equipment
- Shop and upgrades
- Exploration across 8 locations
- Random loot
- Daily rewards
- Daily/weekly missions
- Global leaderboard
- Group leaderboard
- Multiplayer group Horde Raid
- Admin controls
- MongoDB persistence
- Inline button UI with action emojis

## Environment variables
Copy `.env.example` to `.env` locally, or add the same variables in Render.

Required:
BOT_TOKEN
API_ID
API_HASH
MONGO_URI

Optional:
MONGO_DB (default: zombie_survival)
OWNER_IDS (comma-separated Telegram numeric IDs)

## Render
Create a Web Service from this repository.
Build:
`pip install -r requirements.txt`
Start:
`python main.py`

The included `render.yaml` can be used as a Blueprint.

## Button styles
The bot requests Telegram/Kurigram Primary, Success and Danger inline-button styles where the installed client/library supports them. It also keeps clear action emojis so the UI remains understandable on clients that render styles differently.

## Local
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```


## Final V1 fixes
- Native Telegram button styles: Primary (blue), Success (green), Danger (red), when supported by the installed Kurigram/Telegram client.
- Combat state is persisted in MongoDB and survives bot restarts for up to 30 minutes.
- Active raid timers are restored after bot restarts.
- The 5,000 Coins mission now tracks real earned coins.
- Raid and daily rewards update earned-coin progress.
- Mission XP now uses the normal level-up system.
- Group leaderboard is shown when the leaderboard is opened from a group.
- `/help` command is available.

## Disaster-recovery backups
MongoDB remains the live database. The bot can periodically create a compact gzip snapshot and upload it to a private Telegram group/channel. The latest verified snapshot is automatically restored **only when all game collections are empty**, preventing accidental overwrites of live data.

Required for backups:
- `BACKUP_CHAT_ID`: private group/channel ID where the bot can send documents
- `BACKUP_INTERVAL_SECONDS`: default 900 (15 minutes)
- `BACKUP_KEEP`: number of backup metadata records kept in MongoDB (default 12)
- `AUTO_RESTORE`: default `true`

Owner commands in private chat:
- `/backup` — create an immediate snapshot
- `/backupstatus` — show backup health and latest snapshot

The bot also performs a best-effort final snapshot during a clean shutdown/redeploy.

Keep the backup chat private and give the bot permission to send documents. Backups are compressed and SHA-256 verified before automatic restore.

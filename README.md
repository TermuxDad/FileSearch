# Veyro

Veyro is a Telegram group-management bot built with Python 3, Kurigram/Pyrogram-compatible APIs and MongoDB.

## Render Deployment

Veyro is prepared as a Render Web Service. It binds to `0.0.0.0:$PORT` and exposes `/health`. The health endpoint checks MongoDB before returning healthy.

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python main.py
```

Set the required environment variables from `.env.example`. MongoDB must be external because a Render service filesystem is not a database.

## Commands

**Every Veyro command uses `/` only.** `.` and `!` prefixes are not supported, and `@admin` / `@all` are not command aliases.

### Tagging
`/gmtag` `/gntag` `/tagall` `/vctag` `/admin` `/all` `/stop` `/pause` `/resume`

### Moderation
`/warn` `/unwarn` `/warns` `/mute` `/unmute` `/ban` `/unban` `/kick` `/dmute` `/smute` `/dban` `/sban` `/skick` `/pin` `/unpin` `/d`

### Admin
`/res` `/add` `/remove` `/promote` `/demote` `/demote_all` `/title`

### Notes
`/save` `/get` `/notes` `/delnote` `/clear_notes`

### Owner
`/broadcast` `/stats` `/update`

### Whisper
Use Veyro inline as `@VeyroBot @username message`. Whisper text is limited to 180 characters so Telegram's callback alert can display it safely.

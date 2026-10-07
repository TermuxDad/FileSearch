import os


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "").strip()
    MONGO_URI = os.getenv("MONGO_URI", "").strip()
    MONGO_DB = os.getenv("MONGO_DB", "zombie_survival").strip()

    raw_backup_chat_id = os.getenv("BACKUP_CHAT_ID", "").strip()

    if raw_backup_chat_id and raw_backup_chat_id.lstrip("-").isdigit():
        BACKUP_CHAT_ID = -abs(int(raw_backup_chat_id))
    else:
        BACKUP_CHAT_ID = raw_backup_chat_id

    BACKUP_INTERVAL_SECONDS = int(
        os.getenv("BACKUP_INTERVAL_SECONDS", "900")
    )

    BACKUP_KEEP = int(
        os.getenv("BACKUP_KEEP", "12")
    )

    AUTO_RESTORE = os.getenv(
        "AUTO_RESTORE", "true"
    ).strip().lower() in {"1", "true", "yes", "on"}

    OWNER_IDS = {
        int(x.strip())
        for x in os.getenv("OWNER_IDS", "").split(",")
        if x.strip().isdigit()
    }

    @classmethod
    def validate(cls):
        missing = []

        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")

        if not cls.API_ID:
            missing.append("API_ID")

        if not cls.API_HASH:
            missing.append("API_HASH")

        if not cls.MONGO_URI:
            missing.append("MONGO_URI")

        if missing:
            raise RuntimeError(
                "Missing environment variables: " + ", ".join(missing)
            )

import os
from dotenv import load_dotenv

load_dotenv()

def env_int(name, default=None):
    value = os.getenv(name)
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default

API_ID = env_int("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_DB = os.getenv("MONGO_DB")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "Veyro")
OWNER_ID = env_int("OWNER_ID")
LOGGER_GROUP = env_int("LOGGER_GROUP")
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@").strip()
PORT = env_int("PORT", 10000)
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
RENDER_DEPLOY_HOOK = os.getenv("RENDER_DEPLOY_HOOK", "")

missing = [name for name, value in {
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "BOT_TOKEN": BOT_TOKEN,
    "MONGO_DB": MONGO_DB,
    "OWNER_ID": OWNER_ID,
}.items() if not value]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REQUIRED_CHANNEL_USERNAME = os.getenv("REQUIRED_CHANNEL_USERNAME", "")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "")

ADMIN_IDS: list[int] = []
_admin_raw = os.getenv("ADMIN_IDS", "")
if _admin_raw.strip():
    ADMIN_IDS = [int(x.strip()) for x in _admin_raw.split(",") if x.strip()]

DATABASE_URL = "sqlite+aiosqlite:///bot_database.db"

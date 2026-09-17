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

WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")

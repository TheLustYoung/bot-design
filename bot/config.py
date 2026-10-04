import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID") or 0)
STAFF_CHAT_ID = int(os.getenv("STAFF_CHAT_ID") or 0)         # may also be set later with /setstaff inside the staff group
STORAGE = ROOT / "storage"
STORAGE.mkdir(exist_ok=True)
DB_PATH = Path(os.getenv("DB_PATH") or (STORAGE / "leads.db"))

# facts about the shop (address, phone, hours...) live in shop.json so the shop can correct them without touching code
SHOP = json.loads((ROOT / "shop.json").read_text(encoding="utf-8"))

# anti-abuse
MAX_LEADS_PER_DAY = 6          # finished requests per client per day
MAX_FILES_PER_LEAD = 15
RATE_LIMIT = (25, 60)          # at most 25 messages in 60 seconds per user

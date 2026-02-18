import logging
import os
from dotenv import load_dotenv

import constants

load_dotenv(".env")

def _required(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise SystemExit(f"Missing .env var: {name}")
    return v

SESSION_NAME = os.getenv("SESSION_NAME", "account")

API_ID = int(_required("API_ID"))
API_HASH = _required("API_HASH")

# Comma-separated tokens
BOT_TOKENS = [t.strip() for t in os.getenv("BOT_TOKENS", "").split(",") if t.strip()]

CHECK_INTERVAL = float(os.getenv("CHECK_INTERVAL", "1"))
CHECK_UPGRADES_PER_CYCLE = int(os.getenv("CHECK_UPGRADES_PER_CYCLE", "2"))

# Where state is stored
DATA_FILEPATH = constants.DATA_FILEPATH
DATA_SAVER_DELAY = float(os.getenv("DATA_SAVER_DELAY", "2"))

NOTIFY_CHAT_ID = int(_required("NOTIFY_CHAT_ID"))

_notify_upg = (os.getenv("NOTIFY_UPGRADES_CHAT_ID") or "").strip()
NOTIFY_UPGRADES_CHAT_ID = int(_notify_upg) if _notify_upg else None

NOTIFY_AFTER_STICKER_DELAY = float(os.getenv("NOTIFY_AFTER_STICKER_DELAY", "1"))
NOTIFY_AFTER_TEXT_DELAY = float(os.getenv("NOTIFY_AFTER_TEXT_DELAY", "2"))

TIMEZONE = os.getenv("TIMEZONE", "UTC")

CONSOLE_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.INFO
HTTP_REQUEST_TIMEOUT = 20.0
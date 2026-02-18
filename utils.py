import logging
import time
from datetime import datetime
from typing import Tuple
from pytz import timezone as _timezone


# =========================
# Logging
# =========================

def get_logger(
    name: str,
    log_filepath,
    console_log_level=logging.INFO,
    file_log_level=logging.INFO
) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
    file_handler.setLevel(file_log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# =========================
# Time helpers
# =========================

def get_current_timestamp() -> int:
    return int(time.time())


def get_current_datetime(tz) -> str:
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


# =========================
# Formatting helpers
# =========================

def pretty_int(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def pretty_float(value: float, get_is_same: bool = False) -> Tuple[str, bool] | str:
    rounded = round(value, 2)
    formatted = f"{rounded:.2f}"

    if get_is_same:
        return formatted, rounded == value

    return formatted


def format_seconds_to_human_readable(seconds: int) -> str:
    if seconds <= 0:
        return "0s"

    days = seconds // 86400
    seconds %= 86400

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60
    seconds %= 60

    parts = []

    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")

    return " ".join(parts)

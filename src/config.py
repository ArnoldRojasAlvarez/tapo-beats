"""Configuration loader — reads credentials and settings from .env file."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def get_tapo_credentials() -> tuple[str, str]:
    """Return (username, password) for TP-Link cloud auth."""
    username = os.getenv("TAPO_USERNAME")
    password = os.getenv("TAPO_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "TAPO_USERNAME and TAPO_PASSWORD must be set in .env file. "
            "See .env.example for reference."
        )
    return username, password


def get_bulb_ips() -> list[str] | None:
    """Return static bulb IPs from .env, or None to use discovery."""
    raw = os.getenv("BULB_IPS")
    if not raw:
        return None
    return [ip.strip() for ip in raw.split(",") if ip.strip()]


def get_flask_port() -> int:
    """Return the Flask server port."""
    return int(os.getenv("FLASK_PORT", "5000"))


def get_flask_debug() -> bool:
    """Return whether Flask debug mode is enabled."""
    return os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")

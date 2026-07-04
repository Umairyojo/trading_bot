"""Application configuration for the trading bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

DEFAULT_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = BASE_DIR / "logs" / "trading_bot.log"


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is invalid."""


@dataclass(frozen=True, slots=True)
class TradingBotConfig:
    """Resolved application settings."""

    binance_api_key: str
    binance_secret_key: str
    binance_testnet_base_url: str = DEFAULT_TESTNET_BASE_URL
    log_level: str = DEFAULT_LOG_LEVEL
    log_file: Path = DEFAULT_LOG_FILE


def _load_environment() -> None:
    """Load environment variables from .env if present."""

    load_dotenv(
        dotenv_path=ENV_FILE,
        override=False,
    )


def _required_env(name: str) -> str:
    """Return a required environment variable or raise a configuration error."""

    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def load_config() -> TradingBotConfig:
    """Load and validate the application configuration."""

    _load_environment()

    binance_api_key = _required_env("BINANCE_API_KEY")
    binance_secret_key = _required_env("BINANCE_SECRET_KEY")

    base_url = os.getenv(
        "BINANCE_TESTNET_BASE_URL",
        DEFAULT_TESTNET_BASE_URL,
    ).strip()
    log_level = (
        os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
        or DEFAULT_LOG_LEVEL
    )
    log_file = Path(os.getenv("LOG_FILE", str(DEFAULT_LOG_FILE))).expanduser()

    return TradingBotConfig(
        binance_api_key=binance_api_key,
        binance_secret_key=binance_secret_key,
        binance_testnet_base_url=base_url,
        log_level=log_level,
        log_file=log_file,
    )

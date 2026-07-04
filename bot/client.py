"""Reusable Binance Futures client wrapper."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

from bot.config import ConfigurationError, TradingBotConfig, load_config
from bot.logging_config import get_logger

T = TypeVar("T")


class TradingBotClientError(RuntimeError):
    """Base exception for Binance client wrapper failures."""


class TradingBotConnectivityError(TradingBotClientError):
    """Raised when the Binance Futures API is not reachable."""


class TradingBotAPIError(TradingBotClientError):
    """Raised when Binance returns an API-level error."""


class TradingBotRequestError(TradingBotClientError):
    """Raised when the underlying request fails."""


class TradingBotInitializationError(TradingBotClientError):
    """Raised when the authenticated client cannot be created."""


class BinanceFuturesClient:
    """Thin wrapper around the authenticated python-binance client."""

    def __init__(
        self,
        config: TradingBotConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or get_logger(self.__class__.__name__)

        try:
            self._config = config or load_config()
        except ConfigurationError as exc:
            self._logger.exception("Configuration loading failed.")
            raise TradingBotInitializationError(str(exc)) from exc

        try:
            self._client = self._create_client()
        except Exception as exc:  # pragma: no cover - defensive wrapper
            self._logger.exception("Failed to initialize Binance client.")
            raise TradingBotInitializationError(
                "Unable to initialize Binance Futures client."
            ) from exc

        self._logger.info("Binance Futures client initialized.")

    @property
    def config(self) -> TradingBotConfig:
        """Return the resolved application configuration."""

        return self._config

    @property
    def client(self) -> Client:
        """Expose the underlying python-binance client for advanced use cases."""

        return self._client

    @property
    def _futures_url(self) -> str:
        """Return the configured Binance Futures REST base URL."""

        return f"{self._config.binance_testnet_base_url.rstrip('/')}/fapi"

    def _create_client(self) -> Client:
        """Instantiate and configure the authenticated Binance client."""

        client = Client(
            api_key=self._config.binance_api_key,
            api_secret=self._config.binance_secret_key,
        )
        client.FUTURES_URL = self._futures_url
        return client

    def _execute(
        self,
        operation: str,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute a Binance client call with centralized exception handling."""

        try:
            self._logger.info("Executing operation: %s", operation)
            result = func(*args, **kwargs)
            self._logger.info("Operation succeeded: %s", operation)
            return result
        except BinanceAPIException as exc:
            self._logger.exception("Binance API error during %s", operation)
            api_message = getattr(exc, "message", str(exc))
            raise TradingBotAPIError(
                f"Binance API error during {operation}: {api_message}"
            ) from exc
        except BinanceRequestException as exc:
            self._logger.exception("Binance request error during %s", operation)
            raise TradingBotRequestError(
                f"Binance request error during {operation}."
            ) from exc
        except (RequestsTimeout, RequestsConnectionError) as exc:
            self._logger.exception("Network error during %s", operation)
            raise TradingBotConnectivityError(
                f"Network error during {operation}."
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive wrapper
            self._logger.exception("Unexpected error during %s", operation)
            raise TradingBotClientError(
                f"Unexpected error during {operation}."
            ) from exc

    def connectivity_check(self) -> bool:
        """Verify that the Futures endpoint is reachable."""

        self._execute("connectivity check", self._client.futures_ping)
        return True

    def get_server_time(self) -> dict[str, Any]:
        """Fetch server time from Binance Futures."""

        return self._execute("fetch server time", self._client.futures_time)

    def get_exchange_info(self) -> dict[str, Any]:
        """Fetch exchange metadata from Binance Futures."""

        return self._execute("fetch exchange info", self._client.futures_exchange_info)

    def get_symbol_info(self, symbol: str) -> dict[str, Any] | None:
        """Return metadata for a specific symbol if it exists."""

        exchange_info = self.get_exchange_info()
        symbols = exchange_info.get("symbols", [])
        for item in symbols:
            if item.get("symbol") == symbol:
                return item
        return None

    def place_order(self, **order_params: Any) -> dict[str, Any]:
        """Place a futures order using the authenticated client."""

        return self._execute(
            "place order",
            self._client.futures_create_order,
            **order_params,
        )

    def close(self) -> None:
        """Close the underlying HTTP session if supported by the client."""

        close_connection = getattr(self._client, "close_connection", None)
        if callable(close_connection):
            close_connection()
            self._logger.info("Binance Futures client connection closed.")

    def __enter__(self) -> "BinanceFuturesClient":
        return self

    def __exit__(self, exc_type: object, exc: object, exc_tb: object) -> None:
        self.close()

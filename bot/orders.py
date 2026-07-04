"""Order placement services for Binance Futures."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from bot.client import (
    BinanceFuturesClient,
    TradingBotClientError,
    TradingBotInitializationError,
)
from bot.logging_config import get_logger
from bot.validators import ValidatedOrderRequest, validate_order_request


class OrderServiceError(RuntimeError):
    """Base exception for order service failures."""


class OrderPlacementError(OrderServiceError):
    """Raised when an order cannot be placed successfully."""


class OrderFormattingError(OrderServiceError):
    """Raised when a Binance response cannot be normalized."""


@dataclass(frozen=True, slots=True)
class OrderResult:
    """Formatted order response suitable for terminal output."""

    order_id: str
    status: str
    executed_quantity: str
    average_price: str
    timestamp: str
    success: bool
    raw_response: dict[str, Any]


class OrderService:
    """High-level order service for placing Binance Futures orders."""

    def __init__(
        self,
        client: BinanceFuturesClient | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or get_logger(self.__class__.__name__)

        try:
            self._client = client or BinanceFuturesClient(logger=self._logger)
        except TradingBotInitializationError as exc:
            self._logger.exception("Order service initialization failed.")
            raise OrderServiceError(str(exc)) from exc

    def _log_order_request(self, payload: Mapping[str, Any]) -> None:
        """Log a normalized order request payload."""

        self._logger.info("Order request: %s", dict(payload))

    def _log_order_response(self, payload: Mapping[str, Any]) -> None:
        """Log a formatted order response payload."""

        self._logger.info("Order response: %s", dict(payload))

    def _format_timestamp(self, value: object) -> str:
        """Convert a Binance millisecond timestamp to a readable string."""

        if value in (None, "", 0):
            return "N/A"

        try:
            timestamp_ms = int(float(value))
            return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        except (TypeError, ValueError, OSError):
            return "N/A"

    def _format_response(self, response: Mapping[str, Any]) -> OrderResult:
        """Normalize a raw Binance order response."""

        try:
            order_id = response.get("orderId")
            status = str(response.get("status", "UNKNOWN")).upper()
            executed_quantity = response.get("executedQty", 0)
            average_price = response.get("avgPrice") or response.get("averagePrice")
            timestamp = (
                response.get("updateTime")
                or response.get("transactTime")
                or response.get("time")
            )

            formatted = OrderResult(
                order_id=str(order_id) if order_id is not None else "N/A",
                status=status,
                executed_quantity=self._format_decimal(executed_quantity),
                average_price=self._format_optional_decimal(average_price),
                timestamp=self._format_timestamp(timestamp),
                success=order_id is not None and status not in {"REJECTED", "EXPIRED"},
                raw_response=dict(response),
            )
            self._log_order_response(self._response_log_payload(formatted))
            return formatted
        except Exception as exc:  # pragma: no cover - defensive wrapper
            self._logger.exception("Failed to format order response.")
            raise OrderFormattingError(
                "Unable to format the Binance order response."
            ) from exc

    @staticmethod
    def _response_log_payload(result: OrderResult) -> dict[str, Any]:
        """Build a compact payload for response logging."""

        return {
            "order_id": result.order_id,
            "status": result.status,
            "executed_quantity": result.executed_quantity,
            "average_price": result.average_price,
            "timestamp": result.timestamp,
            "success": result.success,
        }

    @staticmethod
    def _format_decimal(value: object) -> str:
        """Render a numeric value without trailing zero noise."""

        try:
            number = float(value)
        except (TypeError, ValueError):
            return "0"

        text = f"{number:.16f}".rstrip("0").rstrip(".")
        return text or "0"

    def _format_optional_decimal(self, value: object) -> str:
        """Render a numeric value or return N/A when unavailable."""

        if value in (None, "", 0, "0", "0.0"):
            return "N/A"
        return self._format_decimal(value)

    def _place_order(self, order_request: Mapping[str, Any]) -> OrderResult:
        """Submit an order and return a formatted response."""

        self._log_order_request(order_request)

        try:
            response = self._client.place_order(**dict(order_request))
            return self._format_response(response)
        except TradingBotClientError as exc:
            self._logger.exception("Order placement failed.")
            raise OrderPlacementError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive wrapper
            self._logger.exception("Unexpected error while placing order.")
            raise OrderPlacementError(
                "Unable to place the order due to an unexpected error."
            ) from exc

    def place_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: object,
    ) -> OrderResult:
        """Place a market order and return a formatted response."""

        request = validate_order_request(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
        )

        return self._place_order(self._build_market_order_payload(request))

    def place_limit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: object,
        price: object,
    ) -> OrderResult:
        """Place a limit order and return a formatted response."""

        request = validate_order_request(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
        )

        return self._place_order(self._build_limit_order_payload(request))

    def _build_market_order_payload(
        self,
        request: ValidatedOrderRequest,
    ) -> dict[str, Any]:
        """Build the payload for a market order."""

        return {
            "symbol": request.symbol,
            "side": request.side,
            "type": request.order_type,
            "quantity": self._format_decimal(request.quantity),
            "newOrderRespType": "RESULT",
        }

    def _build_limit_order_payload(
        self,
        request: ValidatedOrderRequest,
    ) -> dict[str, Any]:
        """Build the payload for a limit order."""

        return {
            "symbol": request.symbol,
            "side": request.side,
            "type": request.order_type,
            "timeInForce": "GTC",
            "quantity": self._format_decimal(request.quantity),
            "price": self._format_decimal(request.price),
            "newOrderRespType": "RESULT",
        }

    def close(self) -> None:
        """Close the underlying client session."""

        self._client.close()

    def __enter__(self) -> "OrderService":
        return self

    def __exit__(self, exc_type: object, exc: object, exc_tb: object) -> None:
        self.close()

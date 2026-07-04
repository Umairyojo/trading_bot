"""Input validation helpers for trading bot order requests."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")
_ALLOWED_SIDES = {"BUY", "SELL"}
_ALLOWED_ORDER_TYPES = {"MARKET", "LIMIT"}
_ALLOWED_SIDES_MESSAGE = "Side must be BUY or SELL."
_ALLOWED_ORDER_TYPES_MESSAGE = "Order type must be MARKET or LIMIT."


class ValidationError(ValueError):
    """Base class for order validation errors."""


class SymbolValidationError(ValidationError):
    """Raised when the trading symbol is invalid."""


class SideValidationError(ValidationError):
    """Raised when the order side is invalid."""


class OrderTypeValidationError(ValidationError):
    """Raised when the order type is invalid."""


class QuantityValidationError(ValidationError):
    """Raised when the quantity is invalid."""


class PriceValidationError(ValidationError):
    """Raised when the limit price is invalid."""


@dataclass(frozen=True, slots=True)
class ValidatedOrderRequest:
    """Normalized validated order request data."""

    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None = None


def _normalize_text(
    value: object,
    *,
    field_name: str,
    error_type: type[ValidationError],
) -> str:
    """Normalize a textual CLI value."""

    if not isinstance(value, str):
        raise error_type(f"{field_name} must be a string.")

    normalized_value = value.strip().upper()
    if not normalized_value:
        raise error_type(f"{field_name} is required.")

    return normalized_value


def _coerce_positive_float(
    value: object,
    *,
    error_type: type[ValidationError],
    field_name: str,
) -> float:
    """Convert a numeric field to a positive float."""

    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise error_type(f"{field_name} must be a number.") from exc

    if numeric_value <= 0:
        raise error_type(f"{field_name} must be greater than 0.")

    return numeric_value


def validate_symbol(symbol: str) -> str:
    """Validate and normalize a Binance futures symbol."""

    normalized_symbol = _normalize_text(
        symbol,
        field_name="Symbol",
        error_type=SymbolValidationError,
    )

    if not _SYMBOL_PATTERN.fullmatch(normalized_symbol):
        raise SymbolValidationError(
            "Symbol must contain only uppercase letters and numbers, "
            "for example BTCUSDT."
        )

    return normalized_symbol


def validate_side(side: str) -> str:
    """Validate and normalize the order side."""

    normalized_side = _normalize_text(
        side,
        field_name="Side",
        error_type=SideValidationError,
    )

    if normalized_side not in _ALLOWED_SIDES:
        raise SideValidationError(_ALLOWED_SIDES_MESSAGE)

    return normalized_side


def validate_order_type(order_type: str) -> str:
    """Validate and normalize the order type."""

    normalized_order_type = _normalize_text(
        order_type,
        field_name="Order type",
        error_type=OrderTypeValidationError,
    )

    if normalized_order_type not in _ALLOWED_ORDER_TYPES:
        raise OrderTypeValidationError(_ALLOWED_ORDER_TYPES_MESSAGE)

    return normalized_order_type


def validate_quantity(quantity: object) -> float:
    """Validate the order quantity."""

    return _coerce_positive_float(
        quantity,
        error_type=QuantityValidationError,
        field_name="Quantity",
    )


def validate_limit_price(price: object | None) -> float:
    """Validate the limit order price."""

    if price is None:
        raise PriceValidationError("Price is required for LIMIT orders.")

    return _coerce_positive_float(
        price,
        error_type=PriceValidationError,
        field_name="Price",
    )


def validate_order_request(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: object,
    price: object | None = None,
) -> ValidatedOrderRequest:
    """Validate a complete order request and return normalized values."""

    normalized_symbol = validate_symbol(symbol)
    normalized_side = validate_side(side)
    normalized_order_type = validate_order_type(order_type)
    normalized_quantity = validate_quantity(quantity)

    normalized_price = None
    if normalized_order_type == "LIMIT":
        normalized_price = validate_limit_price(price)
    elif price is not None:
        # Validate stray price input for consistency even though it is not used.
        normalized_price = validate_limit_price(price)

    return ValidatedOrderRequest(
        symbol=normalized_symbol,
        side=normalized_side,
        order_type=normalized_order_type,
        quantity=normalized_quantity,
        price=normalized_price,
    )

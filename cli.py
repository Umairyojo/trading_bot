"""Command line interface for the Binance Futures trading bot."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from bot.logging_config import get_logger
from bot.orders import OrderPlacementError, OrderService, OrderServiceError
from bot.validators import (
    ValidationError,
    validate_limit_price,
    validate_order_type,
    validate_quantity,
    validate_side,
    validate_symbol,
)

LOGGER = get_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the trading bot CLI."""

    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Place Binance Futures testnet orders.",
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading symbol, for example BTCUSDT.",
    )
    parser.add_argument(
        "--side",
        required=True,
        help="Order side: BUY or SELL.",
    )
    parser.add_argument(
        "--type",
        required=True,
        dest="order_type",
        help="Order type: MARKET or LIMIT.",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        help="Order quantity.",
    )
    parser.add_argument(
        "--price",
        help="Limit price. Required for LIMIT orders only.",
    )
    return parser


def _print_header(title: str) -> None:
    """Print a consistent section header."""

    print("=" * 32)
    print(title)
    print("=" * 32)


def print_request_summary(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
) -> None:
    """Display the submitted request in a readable format."""

    _print_header("ORDER REQUEST")
    print(f"Symbol: {symbol}")
    print(f"Side: {side}")
    print(f"Order Type: {order_type}")
    print(f"Quantity: {quantity}")
    print(f"Price: {price if price is not None else 'N/A'}")
    print("=" * 32)


def print_response_summary(result: object) -> None:
    """Display the formatted order response."""

    _print_header("ORDER RESPONSE")
    print(f"Order ID: {getattr(result, 'order_id', 'N/A')}")
    print(f"Status: {getattr(result, 'status', 'N/A')}")
    print(f"Executed Quantity: {getattr(result, 'executed_quantity', 'N/A')}")
    print(f"Average Price: {getattr(result, 'average_price', 'N/A')}")
    print(f"Timestamp: {getattr(result, 'timestamp', 'N/A')}")
    print(f"Success: {'YES' if getattr(result, 'success', False) else 'NO'}")
    print("=" * 32)


def _validate_inputs(args: argparse.Namespace) -> tuple[str, str, str, float, float | None]:
    """Validate and normalize CLI arguments."""

    symbol = validate_symbol(args.symbol)
    side = validate_side(args.side)
    order_type = validate_order_type(args.order_type)
    quantity = validate_quantity(args.quantity)

    price: float | None = None
    if order_type == "LIMIT":
        price = validate_limit_price(args.price)
    elif args.price is not None:
        raise PriceValidationError("Price is only allowed for LIMIT orders.")

    return symbol, side, order_type, quantity, price


def _execute_order(
    *,
    service: OrderService,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
) -> object:
    """Route the validated request to the correct order method."""

    if order_type == "MARKET":
        return service.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
        )
    return service.place_limit_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
    )


def _log_and_print_error(message: str, *, level: int = logging.ERROR) -> None:
    """Log an error and present the same message to the user."""

    LOGGER.log(level, message)
    print(message)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        symbol, side, order_type, quantity, price = _validate_inputs(args)
        print_request_summary(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=str(quantity),
            price=str(price) if price is not None else None,
        )

        with OrderService() as service:
            result = _execute_order(
                service=service,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
            )
        print_response_summary(result)
        return 0
    except ValidationError as exc:
        _log_and_print_error(f"Input error: {exc}")
        return 2
    except OrderPlacementError as exc:
        _log_and_print_error(f"Order error: {exc}")
        return 1
    except OrderServiceError as exc:
        _log_and_print_error(f"Service error: {exc}")
        return 1
    except KeyboardInterrupt:
        LOGGER.info("Operation cancelled by user.")
        print("\nOperation cancelled by user.")
        return 130
    except Exception:
        LOGGER.exception("Unexpected error occurred while processing the order.")
        print("Unexpected error occurred while processing the order.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

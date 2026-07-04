# Binance Futures Trading Bot

## Overview

This project is a Python 3.11+ command-line trading bot for Binance Futures Testnet (USDT-M). It supports authenticated market and limit orders, request validation, structured logging, and clean terminal output.

## Architecture

- `cli.py` handles argument parsing, validation, and terminal output.
- `bot/config.py` loads environment variables and validates credentials.
- `bot/validators.py` normalizes and validates user input.
- `bot/client.py` wraps the authenticated Binance Futures client.
- `bot/orders.py` places orders and formats API responses.
- `bot/logging_config.py` configures rotating application logs.

## Installation

### Virtual Environment

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a local `.env` file in the project root using `.env.example` as the template:

```env
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log
```

## Running Examples

### Market Order Example

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Limit Order Example

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 108000
```

## Logs

Application logs are written to `logs/trading_bot.log` using a rotating file handler. Logs include request details, responses, API failures, network errors, and unexpected exceptions.

## Troubleshooting

- Ensure `.env` exists and contains valid Binance Futures Testnet credentials.
- Confirm `BINANCE_API_KEY` and `BINANCE_SECRET_KEY` are set and not blank.
- Use uppercase symbols such as `BTCUSDT`.
- `LIMIT` orders require `--price`.
- Verify the Binance Futures Testnet endpoint if connectivity errors occur.

## Project Structure

```text
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── config.py
│   ├── logging_config.py
│   ├── orders.py
│   └── validators.py
├── logs/
├── cli.py
├── .env.example
├── .gitignore
└── requirements.txt
```

## Assumptions

- Binance Futures Testnet is used only for order submission and connectivity checks.
- Market orders do not require a price.
- Limit orders require a positive price.
- Logging is stored locally and not shipped to an external observability system.

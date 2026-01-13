# Alpaca Daily Trading Bot

![Python](https://img.shields.io/badge/python-100%25-blue)
![Status](https://img.shields.io/badge/status-active-success)

A daily trading bot leveraging Alpaca's API for **paper trading** and **daily profit analysis**, integrated with GitHub Actions for pipeline automation and logging. This bot skips trading on weekends, market holidays, or days when the market is closed.

---

## Table of Contents
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Logging and Reports](#logging-and-reports)
- [Contributing](#contributing)
- [License](#license)

---

## Features
Alpaca Daily Trading Bot" implements a structured daily trading logic using Alpaca’s API. Here's a brief overview based on the retrieved code:

Configuration and Initialization:

The bot uses a Config class to read API keys, trading symbols, and other settings from environment variables.
Supports both live trading and "dry-run" (simulation/testing mode).
Uses IEX data feed for compatibility with free Alpaca paper trading accounts.
Daily Trading Procedure:

Trades are only attempted on weekdays and skipped on public holidays or market-closed days using Alpaca's market clock.
The DailyTradingBot initialization prepares Alpaca clients for data and trading.
Signal Generation:

The generate_signals method analyzes pre-configured trading symbols for buy/sell signals. Placeholder logic hints at using technical indicators, volume analysis, and price patterns in its full implementation.
Trade Execution:

If signals exist, trades are executed sequentially, adhering to rate-limiting policies.
Includes implementation of place_buy_order and place_sell_order with error handling.
Handles insufficient buying power, missing positions, or other unexpected conditions gracefully.
GitHub Actions Integration:

The bot is integrated with CI/CD pipelines for automation, logging, and better operational reliability.
Logs and JSON reports of trading activity (trading_report_YYYYMMDD.json) are generated.
Logging and Error Reporting:

Logs include account equity, buying power, trading signals, and runtime errors.
Failures trigger GitHub issues to notify.

---

## Setup

### Prerequisites
- Python 3.8 or later
- `pip` (Python package manager)
- Alpaca account for obtaining API keys

### Dependencies
Install required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Configuration
Set up environment variables as described in the [Environment Variables](#environment-variables) section below.

You can verify your configuration is correct by running:
```bash
python verify_config.py
```

For detailed setup instructions, see [CONFIGURATION.md](CONFIGURATION.md).

---

## Usage

### Running the Bot
```bash
python main.py
```

### Running in Dry-Run Mode
Set the `DRY_RUN` environment variable:
```bash
export DRY_RUN=true
python main.py
```

### GitHub Actions
The bot auto-adjusts logging and execution policies when `GITHUB_ACTIONS=true`.

---

## Environment Variables
To configure the bot, export the following variables:

### Required Variables
| Variable              | Description                           | Example Value   |
|-----------------------|---------------------------------------|-----------------|
| `ALPACA_API_KEY`      | Alpaca API Key ID                    | `your_api_key`  |
| `ALPACA_API_SECRET`   | Alpaca API Secret Key                | `your_secret`   |

### Optional Variables
| Variable              | Description                           | Default Value   |
|-----------------------|---------------------------------------|-----------------|
| `TRADING_SYMBOLS`     | Symbols to trade (comma-separated)   | `AAPL,GOOG,TSLA`|
| `APCA_PAPER`          | Use paper trading (true/false)       | `true`          |
| `DRY_RUN`             | Dry-run mode for simulation          | `false`         |
| `CI_CD_ACTIONS`       | CI/CD indicator                      | `false`         |
| `LOG_LEVEL`           | Logging level                        | `INFO`          |
| `RUN_ENV`             | Runtime environment                  | `local`         |

**Note:** The configuration supports both naming conventions:
- `APCA_API_KEY_ID` or `ALPACA_API_KEY`
- `APCA_API_SECRET_KEY` or `ALPACA_SECRET`

---

## Logging and Reports
Logs are saved in the **logs/** directory, and JSON reports are stored as `trading_report_<YYYYMMDD>.json`.

---

## Contributing
Contributions are welcome! Open an issue or submit a pull request to suggest changes.

---

## License
This project is licensed under the [MIT License](LICENSE).

---

## Disclaimer
**Use this bot at your own risk.** It is intended solely for educational purposes with paper trading. Losses may occur in live trading.

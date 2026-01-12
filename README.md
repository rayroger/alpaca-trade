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
- **Daily Market Check**: Automatically skips weekends and public holidays.
- **Signal Generation**: Analyzes buy/sell signals for each symbol based on pre-configured logic.
- **Trade Execution**:
  - Executes trades sequentially with API rate-limiting.
  - Dry-run option for testing without real trade placements.
- **GitHub Actions Integration**:
  - Detects CI/CD environments and adapts behavior (e.g., saving logs).
- **Logging and Report Generation**:
  - Detailed JSON reports for executed trades and runtime logs.

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
| `APCA_API_KEY_ID`     | Alpaca API Key ID                    | `your_api_key`  |
| `APCA_API_SECRET_KEY` | Alpaca API Secret Key                | `your_secret`   |

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

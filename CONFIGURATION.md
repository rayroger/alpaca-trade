# Environment Variables Configuration Guide

This document provides a comprehensive guide to configuring the Alpaca Trading Bot.

## Required GitHub Secrets

The following secrets must be configured in your GitHub repository settings (Settings → Secrets and variables → Actions → Secrets):

| Secret Name           | Description                    | How to Obtain                                  |
|-----------------------|--------------------------------|------------------------------------------------|
| `APCA_API_KEY_ID`     | Alpaca API Key ID             | From your Alpaca account dashboard             |
| `APCA_API_SECRET_KEY` | Alpaca API Secret Key         | From your Alpaca account dashboard             |

## Required GitHub Variables

The following variables should be configured in your GitHub repository settings (Settings → Secrets and variables → Actions → Variables):

| Variable Name     | Description                           | Example Value   | Default          |
|-------------------|---------------------------------------|-----------------|------------------|
| `TRADING_SYMBOLS` | Symbols to trade (comma-separated)   | `AAPL,GOOG,TSLA`| `AAPL,GOOG,TSLA` |

## Environment Variables Set in Workflow

The following environment variables are automatically set by the GitHub Actions workflow:

| Variable Name     | Description                    | Value in Workflow | Source                    |
|-------------------|--------------------------------|-------------------|---------------------------|
| `APCA_PAPER`      | Use paper trading mode        | `true`            | Hardcoded in workflow     |
| `CI_CD_ACTIONS`   | Indicates running in CI/CD    | `true`            | Hardcoded in workflow     |
| `RUN_ENV`         | Runtime environment           | `github`          | Hardcoded in workflow     |
| `LOG_LEVEL`       | Logging level                 | `INFO` (default)  | Workflow dispatch input   |
| `DRY_RUN`         | Dry-run mode (no real trades) | `false` (default) | Workflow dispatch input   |

## Local Development

When running the bot locally, you can use a `.env` file or export environment variables:

### Using a .env file

Create a `.env` file in the project root:

```bash
# Required
APCA_API_KEY_ID=your_api_key_here
APCA_API_SECRET_KEY=your_secret_key_here

# Optional
TRADING_SYMBOLS=AAPL,GOOG,TSLA
APCA_PAPER=true
DRY_RUN=true
LOG_LEVEL=INFO
```

### Using export commands

```bash
export APCA_API_KEY_ID=your_api_key_here
export APCA_API_SECRET_KEY=your_secret_key_here
export TRADING_SYMBOLS=AAPL,GOOG,TSLA
export APCA_PAPER=true
export DRY_RUN=true
```

## Backward Compatibility

The configuration supports both naming conventions for API credentials:

- **New naming (recommended)**: `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`
- **Old naming (supported)**: `ALPACA_API_KEY`, `ALPACA_SECRET`

The `config.py` will automatically use whichever is available.

## Configuration Validation

The bot validates that all required environment variables are present on startup. If any required variables are missing, the bot will exit with a clear error message indicating what needs to be configured.

## How to Set Up GitHub Secrets and Variables

### Setting up Secrets:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each required secret:
   - Name: `APCA_API_KEY_ID`, Value: Your Alpaca API Key
   - Name: `APCA_API_SECRET_KEY`, Value: Your Alpaca Secret Key

### Setting up Variables:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
3. Click **New repository variable**
4. Add:
   - Name: `TRADING_SYMBOLS`, Value: `AAPL,GOOG,TSLA` (or your preferred symbols)

## Verification

After setting up the configuration, you can verify it works by:

1. Running the workflow manually (Actions → Daily Trading Bot → Run workflow)
2. Check the logs to ensure the bot initialized correctly
3. Verify that all environment variables are loaded in the logs

## Data Feed Configuration

The bot is configured to use the **IEX (Investor's Exchange)** data feed, which is available for free Alpaca paper trading accounts. 

**Important Notes:**
- Free/paper Alpaca accounts do not have access to the SIP (Securities Information Processor) data feed
- The bot automatically uses `feed='iex'` in all data requests to ensure compatibility with free accounts
- If you upgrade to a paid subscription with SIP access, you can modify the `feed` parameter in `bot.py` if desired
- IEX data is sufficient for most trading strategies and provides real-time market data

If you encounter errors like `"subscription does not permit querying recent SIP data"`, verify that:
1. You're using a paper trading account (`APCA_PAPER=true`)
2. The bot code includes `feed='iex'` in data requests (already configured)

## Security Notes

- Never commit API keys or secrets to the repository
- Use GitHub Secrets for sensitive data (API keys)
- Use GitHub Variables for non-sensitive configuration (trading symbols)
- The bot includes a `.gitignore` file to prevent accidental commits of `.env` files

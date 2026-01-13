# Daily Status Reports and Dynamic Stock Selection

## Overview

This document describes the new features added to the Alpaca Trading Bot:
1. **Daily Status Reports with Tables and Graphs**
2. **Dynamic Stock Selection**

## Feature 1: Daily Status Reports

### What's New

The bot now automatically generates comprehensive visual reports that include:

#### Report Types Generated

1. **HTML Reports** (`reports/daily_report_YYYYMMDD.html`)
   - Professional, web-based daily status reports
   - Interactive charts and visualizations
   - Color-coded tables for easy reading
   - Includes:
     - Account summary (equity, buying power, cash)
     - Trading activity statistics
     - Symbol analysis table with buy/sell indicators
     - Equity history chart (last 30 days)
     - Buy vs Sell signals chart over time
     - Recent trading history table

2. **Markdown Summaries** (`daily_summary_YYYYMMDD.md`)
   - Quick-view text summary
   - Perfect for viewing in GitHub or text editors
   - Contains key metrics and symbol analysis

3. **JSON Reports** (existing, enhanced)
   - `daily_report_YYYYMMDD.json` - Detailed structured data
   - `trading_report_YYYYMMDD.json` - Legacy format (maintained for compatibility)

### Using the Reports

#### Accessing Reports in GitHub Actions

After each workflow run:
1. Go to the Actions tab in GitHub
2. Click on the completed workflow run
3. Scroll down to "Artifacts"
4. Download "trading-logs" artifact
5. Extract the zip file to view HTML reports

#### Local Development

When running locally, reports are automatically generated in:
- `reports/` directory (HTML files)
- Root directory (JSON and Markdown files)

Simply open the HTML file in any web browser to view the visual report.

### Report Features

#### Account Summary
- Current equity value with historical trend
- Buying power available
- Cash balance

#### Trading Analysis
- Number of symbols analyzed
- Total buy/sell signals generated
- Actual trades executed
- Signal distribution by symbol

#### Visual Charts
- **Equity Chart**: Shows account equity over the last 30 days with bar chart visualization
- **Signals Chart**: Displays buy vs sell signals over time with color-coded bars (green for buy, red for sell)

#### Symbol Performance Table
- Shows each symbol analyzed
- Action taken (BUY, SELL, HOLD)
- Number of buy indicators
- Number of sell indicators
- Color-coded actions for easy identification

## Feature 2: Dynamic Stock Selection

### What's New

Instead of using a static predefined list of stocks, the bot can now dynamically select stocks based on various criteria.

### Selection Methods

#### 1. Diversified Selection (`diversified`)
**Default method** - Selects stocks across multiple sectors for diversification

```bash
export USE_DYNAMIC_STOCK_SELECTION=true
export STOCK_SELECTION_METHOD=diversified
export STOCK_SELECTION_LIMIT=10
```

Features:
- Automatically spreads selections across 8 sectors
- Ensures portfolio diversification
- Configurable stocks per sector

Sectors covered:
- Technology (AAPL, MSFT, GOOGL, META, NVDA, etc.)
- Financial (JPM, BAC, WFC, GS, MS, etc.)
- Healthcare (JNJ, UNH, PFE, ABBV, TMO, etc.)
- Consumer (AMZN, TSLA, WMT, HD, NKE, etc.)
- Energy (XOM, CVX, COP, SLB, EOG, etc.)
- Industrial (BA, CAT, GE, HON, UPS, etc.)
- Communication (DIS, CMCSA, NFLX, T, VZ, etc.)
- Materials (LIN, APD, ECL, SHW, DD, etc.)

#### 2. High Volume Selection (`high_volume`)
Selects stocks with the highest trading volume

```bash
export STOCK_SELECTION_METHOD=high_volume
```

Features:
- Focuses on liquid, actively traded stocks
- Minimum volume threshold: 5,000,000 shares/day
- Ideal for ensuring easy entry/exit

#### 3. Top Gainers (`top_gainers`)
Identifies stocks with highest recent price increases

```bash
export STOCK_SELECTION_METHOD=top_gainers
```

Features:
- Analyzes price movements over the last day
- Identifies momentum opportunities
- Great for riding trends

#### 4. Top Losers (`top_losers`)
Identifies stocks with highest recent price decreases

```bash
export STOCK_SELECTION_METHOD=top_losers
```

Features:
- Finds potential rebound opportunities
- Analyzes oversold conditions
- Useful for contrarian strategies

#### 5. Mixed Approach (`mixed`)
Combines diversified and high-volume selection

```bash
export STOCK_SELECTION_METHOD=mixed
```

Features:
- Best of both worlds
- Ensures diversification AND liquidity
- Balanced approach

#### 6. Broker Universe (`broker_all`) - NEW!
Retrieves all tradable stocks directly from Alpaca broker

```bash
export STOCK_SELECTION_METHOD=broker_all
export STOCK_SELECTION_LIMIT=50
```

Features:
- Dynamically retrieves tradable stocks from Alpaca API
- Always up-to-date with broker's available assets
- Filters for tradable, fractionable, and shortable stocks
- Can return hundreds or thousands of symbols
- No need to maintain hardcoded lists

### Broker-Retrieved Stock Universe - NEW!

**You can now retrieve the stock universe from the broker instead of using the predefined list!**

Set `USE_BROKER_STOCK_UNIVERSE=true` to retrieve tradable stocks from Alpaca's API:

```bash
export USE_DYNAMIC_STOCK_SELECTION=true
export USE_BROKER_STOCK_UNIVERSE=true
export STOCK_SELECTION_METHOD=top_gainers
export STOCK_SELECTION_LIMIT=10
```

This will:
1. Query Alpaca API for all tradable US equity stocks
2. Apply your selection method (e.g., top_gainers) to the broker-retrieved universe
3. Return the top 10 gainers from ALL tradable stocks (not just the predefined 80)

#### Filter by Exchange (Performance Optimization) - NEW!

**Limit the broker universe to specific exchanges to reduce count and improve performance:**

```bash
export USE_DYNAMIC_STOCK_SELECTION=true
export USE_BROKER_STOCK_UNIVERSE=true
export BROKER_EXCHANGES=NYSE,NASDAQ  # Only NYSE and NASDAQ
export STOCK_SELECTION_METHOD=top_gainers
export STOCK_SELECTION_LIMIT=10
```

This addresses the concern about retrieving too many stocks:
- **Without filter**: Retrieves all tradable stocks (could be thousands)
- **With NYSE,NASDAQ filter**: Retrieves only stocks from major exchanges (typically 3,000-5,000)
- **Performance**: Faster execution by focusing on liquid, well-known stocks

**Supported exchanges:**
- NYSE - New York Stock Exchange
- NASDAQ - NASDAQ Stock Market
- AMEX - American Stock Exchange
- ARCA - NYSE Arca (ETFs)
- BATS - BATS Exchange
- And more...

**Benefits:**
- Always up-to-date with broker's available stocks
- No manual maintenance of stock lists
- Access to the full market, not just 80 stocks
- Automatic filtering for tradable, liquid stocks
- **NEW: Control universe size with exchange filters**

**Note:** The predefined 80-stock universe is still the default (faster, API-friendly). Enable broker retrieval when you want access to the full market.

### Stock Universe

The bot can select from a universe of **80 major stocks** across 8 sectors:
- 10 stocks per sector
- All highly liquid, major companies
- Regularly traded on major exchanges

### Configuration

#### Environment Variables

```bash
# Enable dynamic selection
USE_DYNAMIC_STOCK_SELECTION=true

# Choose selection method
STOCK_SELECTION_METHOD=diversified  # or high_volume, top_gainers, top_losers, mixed

# Set maximum number of stocks
STOCK_SELECTION_LIMIT=10

# For predefined list (traditional approach)
USE_DYNAMIC_STOCK_SELECTION=false
TRADING_SYMBOLS=AAPL,MSFT,TSLA
```

#### GitHub Actions Workflow

The workflow now includes options for dynamic stock selection:

1. Go to Actions tab
2. Select "Daily Trading Bot"
3. Click "Run workflow"
4. Choose options:
   - **use-dynamic-selection**: true/false
   - **selection-method**: Choose from dropdown
     - diversified
     - high_volume
     - top_gainers
     - top_losers
     - mixed

### Benefits of Dynamic Selection

1. **Automatic Diversification**: No need to manually select stocks from different sectors
2. **Market Responsive**: Can adapt to current market conditions
3. **Reduced Maintenance**: No need to update stock lists manually
4. **Opportunity Discovery**: Automatically finds top performers or potential rebounds
5. **Risk Management**: Spreads risk across sectors and companies

### Example Workflows

#### Conservative Approach
```bash
export USE_DYNAMIC_STOCK_SELECTION=true
export STOCK_SELECTION_METHOD=diversified
export STOCK_SELECTION_LIMIT=8
```
Result: 8 stocks across multiple sectors for balanced diversification

#### Aggressive/Momentum Approach
```bash
export USE_DYNAMIC_STOCK_SELECTION=true
export STOCK_SELECTION_METHOD=top_gainers
export STOCK_SELECTION_LIMIT=5
```
Result: 5 top performing stocks with strong momentum

#### Contrarian Approach
```bash
export USE_DYNAMIC_STOCK_SELECTION=true
export STOCK_SELECTION_METHOD=top_losers
export STOCK_SELECTION_LIMIT=5
```
Result: 5 stocks that have dropped, potential for rebound

## Testing

### Running Tests

All features include comprehensive test coverage:

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test suites
python -m unittest tests/test_report_generator.py -v
python -m unittest tests/test_stock_selector.py -v
```

### Demo Script

Run the demonstration to see all features in action:

```bash
python demo.py
```

This will:
1. Generate sample trading data for 10 days
2. Create HTML and Markdown reports
3. Demonstrate all stock selection methods
4. Show usage examples

## Integration with Existing Features

### Backward Compatibility

All new features are **fully backward compatible**:
- Default behavior uses predefined stock list (existing functionality)
- Existing reports continue to be generated
- No breaking changes to the API or configuration

### GitHub Actions Integration

Reports are automatically uploaded as artifacts:
- Download from workflow run artifacts
- Retained for 7 days
- Includes all report types

## Technical Details

### Report Generator Architecture

```
report_generator.py
├── DailyReportGenerator class
│   ├── load_daily_reports() - Load historical reports
│   ├── load_trading_logs() - Parse log files
│   ├── generate_summary_table() - Create HTML summary table
│   ├── generate_symbol_performance_table() - Symbol analysis table
│   ├── generate_equity_chart_data() - Equity visualization
│   ├── generate_signals_chart() - Signals visualization
│   ├── generate_html_report() - Complete HTML report
│   ├── generate_markdown_summary() - Quick text summary
│   └── save_html_report() - Save to file
```

### Stock Selector Architecture

```
stock_selector.py
├── DynamicStockSelector class
│   ├── STOCK_UNIVERSE - 80 stocks across 8 sectors
│   ├── get_all_symbols() - All available symbols
│   ├── get_high_volume_stocks() - Volume-based selection
│   ├── get_diversified_stocks() - Sector-based selection
│   ├── get_top_movers() - Price movement based selection
│   ├── select_stocks() - Main selection method
│   └── get_selection_info() - Selection statistics
```

## Best Practices

1. **Start with Diversified Selection**: Good for most use cases
2. **Use High Volume**: Ensure liquidity for easy trading
3. **Monitor Reports**: Review HTML reports regularly
4. **Adjust Limits**: Start with 5-10 stocks, adjust based on results
5. **Test in Dry-Run**: Always test new configurations with DRY_RUN=true

## Troubleshooting

### Reports Not Generating

- Check that the `reports/` directory exists (auto-created)
- Verify sufficient disk space
- Check logs for errors

### Dynamic Selection Returns Empty List

- Ensure Alpaca API credentials are valid
- Check network connectivity
- Verify the selection method is spelled correctly
- Try a different selection method

### HTML Report Won't Open

- Ensure you're opening in a web browser
- Check file permissions
- Verify the file isn't corrupted

## Future Enhancements

Potential improvements for future versions:
- Real-time sentiment analysis integration
- Advanced technical analysis filters
- Custom sector selection
- Machine learning-based stock selection
- Performance backtesting
- Email/Slack report notifications

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review the demo script output
3. Run tests to verify functionality
4. Open a GitHub issue with details

# main.py
import os
import sys
import json
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from bot import DailyTradingBot
from config import Config
from report_generator import DailyReportGenerator
from stock_selector import DynamicStockSelector

def setup_logging():
    """Configure logging for GitHub Actions"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"trading_{timestamp}.log"
    
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    
    try:
        # Check if running in GitHub Actions
        is_github = os.getenv('CI_CD_ACTIONS') == 'true'
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        logger.info(f"Starting trading bot - GitHub: {is_github}, Dry Run: {dry_run}")
        
        # Initialize config and bot
        config = Config()
        config.DRY_RUN = dry_run
        
        bot = DailyTradingBot(config)
        
        # Check if we should run today
        if not bot.should_run_today():
            logger.info("Skipping run - market closed or holiday")
            return
            
        # Run pre-market analysis
        account_info = bot.get_account_info()
        logger.info(f"Account Equity: ${account_info['equity']:,.2f}")
        logger.info(f"Buying Power: ${account_info['buying_power']:,.2f}")
        
        # Dynamic stock selection (if enabled)
        use_dynamic_selection = os.getenv('USE_DYNAMIC_STOCK_SELECTION', 'false').lower() == 'true'
        selection_method = os.getenv('STOCK_SELECTION_METHOD', 'diversified')
        use_broker_universe = os.getenv('USE_BROKER_STOCK_UNIVERSE', 'false').lower() == 'true'
        
        # Parse broker exchanges filter (comma-separated list)
        broker_exchanges_str = os.getenv('BROKER_EXCHANGES', '')
        broker_exchanges = [ex.strip().upper() for ex in broker_exchanges_str.split(',') if ex.strip()] if broker_exchanges_str else None
        
        if use_dynamic_selection:
            logger.info(f"Using dynamic stock selection with method: {selection_method}")
            stock_selector = DynamicStockSelector(bot.data_client, bot.trading_client)
            
            # Select stocks based on method
            selected_stocks = stock_selector.select_stocks(
                method=selection_method,
                limit=int(os.getenv('STOCK_SELECTION_LIMIT', '10')),
                use_broker_universe=use_broker_universe,
                broker_exchanges=broker_exchanges
            )
            
            if use_broker_universe:
                if broker_exchanges:
                    logger.info(f"Using broker-retrieved stock universe from exchanges: {', '.join(broker_exchanges)}")
                else:
                    logger.info(f"Using broker-retrieved stock universe (all exchanges)")
            
            # Get selection info
            selection_info = stock_selector.get_selection_info(selected_stocks)
            logger.info(f"Dynamic selection: {selection_info['total_stocks']} stocks from {selection_info['sectors_represented']} sectors")
            logger.info(f"Sector distribution: {selection_info['sector_distribution']}")
            
            # Override config symbols with dynamically selected stocks
            trading_symbols = selected_stocks
        else:
            logger.info(f"Using predefined stock list: {', '.join(config.TRADING_SYMBOLS)}")
            trading_symbols = config.TRADING_SYMBOLS
        
        # Generate and execute signals
        trades_executed = []
        symbols_analyzed = {}
        all_signals = []
        
        for symbol in trading_symbols:
            signals, metadata = bot.generate_signals_with_metadata(symbol)
            symbols_analyzed[symbol] = metadata
            
            if signals:
                all_signals.extend(signals)
                logger.info(f"{symbol} signals: {signals}")
                
                if not dry_run:
                    trades = bot.execute_trades(symbol, signals)
                    trades_executed.extend(trades)
                else:
                    logger.info(f"[DRY RUN] Would execute trades for {symbol}")
        
        # Generate comprehensive daily report
        daily_report = bot.generate_daily_report(
            symbols_analyzed=symbols_analyzed,
            all_signals=all_signals,
            trades_executed=trades_executed
        )
        
        # Generate legacy report (for compatibility)
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "environment": "github_actions",
            "dry_run": dry_run,
            "account_equity": account_info['equity'],
            "trades_executed": trades_executed,
            "signals_generated": len(all_signals)
        }
        
        # Save both reports
        report_file = f"trading_report_{datetime.now().strftime('%Y%m%d')}.json"
        daily_report_file = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        with open(daily_report_file, 'w') as f:
            json.dump(daily_report, f, indent=2)
        
        # Generate HTML report with charts and tables
        logger.info("Generating visual HTML report...")
        report_gen = DailyReportGenerator()
        html_report_path = report_gen.save_html_report(daily_report)
        logger.info(f"HTML report saved to {html_report_path}")
        
        # Generate markdown summary
        md_summary = report_gen.generate_markdown_summary(daily_report)
        md_file = f"daily_summary_{datetime.now().strftime('%Y%m%d')}.md"
        with open(md_file, 'w') as f:
            f.write(md_summary)
        logger.info(f"Markdown summary saved to {md_file}")
            
        logger.info(f"Trading bot completed successfully.")
        logger.info(f"Report saved to {report_file}")
        logger.info(f"Daily report saved to {daily_report_file}")
        
        # Log summary
        logger.info(f"Summary: {len(all_signals)} signals generated, {len(trades_executed)} trades executed")
        logger.info(f"Symbols analyzed: {len(symbols_analyzed)}, Symbols with signals: {daily_report['analysis']['symbols_with_signals']}")
        
        # Print dynamic stock selection info if enabled
        if use_dynamic_selection:
            logger.info(f"Dynamic stock selection method: {selection_method}")
            logger.info(f"Stocks selected: {', '.join(trading_symbols)}")
        
    except Exception as e:
        logger.error(f"Trading bot failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

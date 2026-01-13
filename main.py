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
        
        # Generate and execute signals
        trades_executed = []
        symbols_analyzed = {}
        all_signals = []
        
        for symbol in config.TRADING_SYMBOLS:
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
            
        logger.info(f"Trading bot completed successfully.")
        logger.info(f"Report saved to {report_file}")
        logger.info(f"Daily report saved to {daily_report_file}")
        
        # Log summary
        logger.info(f"Summary: {len(all_signals)} signals generated, {len(trades_executed)} trades executed")
        logger.info(f"Symbols analyzed: {len(symbols_analyzed)}, Symbols with signals: {daily_report['analysis']['symbols_with_signals']}")
        
    except Exception as e:
        logger.error(f"Trading bot failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

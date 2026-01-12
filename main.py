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
        is_github = os.getenv('GITHUB_ACTIONS') == 'true'
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
        for symbol in config.TRADING_SYMBOLS:
            signals = bot.generate_signals(symbol)
            if signals:
                logger.info(f"{symbol} signals: {signals}")
                
                if not dry_run:
                    trades = bot.execute_trades(symbol, signals)
                    trades_executed.extend(trades)
                else:
                    logger.info(f"[DRY RUN] Would execute trades for {symbol}")
        
        # Generate report
        report = {
            "run_timestamp": datetime.now().isoformat(),
            "environment": "github_actions",
            "dry_run": dry_run,
            "account_equity": account_info['equity'],
            "trades_executed": trades_executed,
            "signals_generated": len([s for s in [bot.generate_signals(sym) for sym in config.TRADING_SYMBOLS] if s])
        }
        
        # Save report
        report_file = f"trading_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Trading bot completed successfully. Report saved to {report_file}")
        
    except Exception as e:
        logger.error(f"Trading bot failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

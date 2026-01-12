# config.py
import os
from typing import List


class Config:
    """Configuration class for the trading bot"""
    
    def __init__(self):
        # Alpaca API credentials
        # Support both naming conventions: ALPACA_* and APCA_*
        self.ALPACA_API_KEY = os.getenv('ALPACA_API_KEY') or os.getenv('APCA_API_KEY_ID')
        self.ALPACA_SECRET = os.getenv('ALPACA_SECRET') or os.getenv('APCA_API_SECRET_KEY')
        
        # Trading symbols - comma-separated list
        symbols_str = os.getenv('TRADING_SYMBOLS', 'AAPL,GOOG,TSLA')
        self.TRADING_SYMBOLS: List[str] = [s.strip() for s in symbols_str.split(',')]
        
        # Paper trading mode
        self.APCA_PAPER = os.getenv('APCA_PAPER', 'true').lower() == 'true'
        
        # Dry run mode (no actual trades)
        self.DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        # CI/CD environment indicator
        self.CI_CD_ACTIONS = os.getenv('CI_CD_ACTIONS', 'false').lower() == 'true'
        
        # Runtime environment
        self.RUN_ENV = os.getenv('RUN_ENV', 'local')
        
        # Log level
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Validate required configuration
        self._validate()
    
    def _validate(self):
        """Validate that required configuration is present"""
        errors = []
        
        if not self.ALPACA_API_KEY:
            errors.append("ALPACA_API_KEY or APCA_API_KEY_ID is required")
        
        if not self.ALPACA_SECRET:
            errors.append("ALPACA_SECRET or APCA_API_SECRET_KEY is required")
        
        if not self.TRADING_SYMBOLS:
            errors.append("TRADING_SYMBOLS is required")
        
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    def __repr__(self):
        """String representation (hiding sensitive data)"""
        return (
            f"Config(\n"
            f"  ALPACA_API_KEY={'*' * 8 if self.ALPACA_API_KEY else 'NOT SET'},\n"
            f"  ALPACA_SECRET={'*' * 8 if self.ALPACA_SECRET else 'NOT SET'},\n"
            f"  TRADING_SYMBOLS={self.TRADING_SYMBOLS},\n"
            f"  APCA_PAPER={self.APCA_PAPER},\n"
            f"  DRY_RUN={self.DRY_RUN},\n"
            f"  CI_CD_ACTIONS={self.CI_CD_ACTIONS},\n"
            f"  RUN_ENV={self.RUN_ENV},\n"
            f"  LOG_LEVEL={self.LOG_LEVEL}\n"
            f")"
        )

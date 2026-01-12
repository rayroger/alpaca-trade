# bot.py
import os
import logging
import pytz
from datetime import datetime, time
import holidays
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest


class DailyTradingBot:
    """Daily trading bot for Alpaca API"""
    
    def __init__(self, config):
        """Initialize the trading bot with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET,
            paper=config.APCA_PAPER
        )
        
        self.data_client = StockHistoricalDataClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET
        )
        
        self.logger.info(f"Initialized DailyTradingBot - Paper: {config.APCA_PAPER}, DryRun: {config.DRY_RUN}")
    
    def should_run_today(self):
        """Check if bot should run today (GitHub Actions aware)"""
        # Get current time in ET
        et = pytz.timezone('US/Eastern')
        now_et = datetime.now(pytz.UTC).astimezone(et)
        
        # Skip weekends
        if now_et.weekday() >= 5:
            self.logger.info(f"Skipping - Weekend (day {now_et.weekday()})")
            return False
            
        # Skip US holidays
        us_holidays = holidays.US(years=now_et.year)
        if now_et.date() in us_holidays:
            self.logger.info(f"Skipping - US Holiday: {us_holidays.get(now_et.date())}")
            return False
            
        # Check if market is open via Alpaca
        try:
            clock = self.trading_client.get_clock()
            if not clock.is_open:
                self.logger.info(f"Skipping - Market is closed")
            return clock.is_open
        except Exception as e:
            self.logger.warning(f"Could not check market status: {e}")
            # If we can't check, assume market is open if weekday
            # and within market hours
            market_open = time(9, 30)
            market_close = time(16, 0)
            current_time = now_et.time()
            
            is_open = market_open <= current_time <= market_close
            self.logger.info(f"Assuming market is {'open' if is_open else 'closed'} based on time")
            return is_open
    
    def get_account_info(self):
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            return {
                'equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value)
            }
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            raise
    
    def get_current_price(self, symbol):
        """Get current price for a symbol"""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(request)
            
            if symbol in quote:
                return float(quote[symbol].ask_price)
            else:
                raise ValueError(f"No quote data for {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def generate_signals(self, symbol):
        """Generate trading signals for a symbol"""
        # Placeholder logic - in real implementation, this would analyze market data
        # For now, return empty signals
        self.logger.info(f"Generating signals for {symbol}")
        
        # This is a placeholder - implement your actual signal logic here
        # For example, you might check technical indicators, news sentiment, etc.
        
        return []  # Return empty list for now - no trades
    
    def execute_trades(self, symbol, signals):
        """Execute trades with rate limiting for GitHub Actions"""
        trades = []
        
        for signal_type, reason in signals:
            try:
                if signal_type == 'BUY':
                    trade = self.place_buy_order(symbol, reason)
                elif signal_type == 'SELL':
                    trade = self.place_sell_order(symbol, reason)
                else:
                    continue
                    
                trades.append(trade)
                
                # Rate limiting: wait 1 second between trades
                # to avoid hitting API limits
                import time
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Failed to execute {signal_type} for {symbol}: {e}")
                
        return trades
    
    def place_buy_order(self, symbol, reason):
        """Place buy order with proper error handling"""
        try:
            # Calculate position size
            account = self.get_account_info()
            max_position_size = account['buying_power'] * 0.2  # 20% max per position
            
            # Get current price
            current_price = self.get_current_price(symbol)
            
            # Calculate shares (min 1 share)
            shares = max(1, int(max_position_size / current_price))
            
            if self.config.DRY_RUN:
                self.logger.info(f"[DRY RUN] Would BUY {shares} shares of {symbol} at ${current_price:.2f}")
                return {
                    'symbol': symbol,
                    'action': 'BUY',
                    'reason': reason,
                    'shares': shares,
                    'price': current_price,
                    'status': 'DRY_RUN'
                }
            
            # Place order
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(market_order_data)
            
            self.logger.info(f"Submitted BUY order for {shares} shares of {symbol}")
            
            return {
                'symbol': symbol,
                'action': 'BUY',
                'reason': reason,
                'shares': shares,
                'price': current_price,
                'order_id': str(order.id),
                'status': 'SUBMITTED'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to place buy order for {symbol}: {e}")
            raise
    
    def place_sell_order(self, symbol, reason):
        """Place sell order with proper error handling"""
        try:
            # Get current position
            try:
                position = self.trading_client.get_open_position(symbol)
                shares = int(position.qty)
            except Exception:
                self.logger.warning(f"No position found for {symbol}")
                return None
            
            if shares <= 0:
                self.logger.warning(f"No shares to sell for {symbol}")
                return None
            
            # Get current price
            current_price = self.get_current_price(symbol)
            
            if self.config.DRY_RUN:
                self.logger.info(f"[DRY RUN] Would SELL {shares} shares of {symbol} at ${current_price:.2f}")
                return {
                    'symbol': symbol,
                    'action': 'SELL',
                    'reason': reason,
                    'shares': shares,
                    'price': current_price,
                    'status': 'DRY_RUN'
                }
            
            # Place order
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(market_order_data)
            
            self.logger.info(f"Submitted SELL order for {shares} shares of {symbol}")
            
            return {
                'symbol': symbol,
                'action': 'SELL',
                'reason': reason,
                'shares': shares,
                'price': current_price,
                'order_id': str(order.id),
                'status': 'SUBMITTED'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to place sell order for {symbol}: {e}")
            raise

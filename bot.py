# bot.py (updated for GitHub Actions)
import pytz
from datetime import datetime, time
import holidays

class DailyTradingBot:
    # ... existing code ...
    
    def should_run_today(self):
        """Check if bot should run today (GitHub Actions aware)"""
        # Get current time in ET
        et = pytz.timezone('US/Eastern')
        now_et = datetime.now(pytz.UTC).astimezone(et)
        
        # Skip weekends
        if now_et.weekday() >= 5:
            return False
            
        # Skip US holidays
        us_holidays = holidays.US(years=now_et.year)
        if now_et.date() in us_holidays:
            return False
            
        # Check if market is open via Alpaca
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception:
            # If we can't check, assume market is open if weekday
            # and within market hours
            market_open = time(9, 30)
            market_close = time(16, 0)
            current_time = now_et.time()
            
            return market_open <= current_time <= market_close
    
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
            
            return {
                'symbol': symbol,
                'action': 'BUY',
                'reason': reason,
                'shares': shares,
                'price': current_price,
                'order_id': order.id,
                'status': 'SUBMITTED'
            }
            
        except Exception as e:
            self.logger.error(f"Error placing buy order for {symbol}: {e}")
            raise

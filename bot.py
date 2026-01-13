# bot.py
import os
import logging
import time
import pytz
from datetime import datetime, time as datetime_time, timedelta
import holidays
import pandas as pd
import numpy as np
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame


class DailyTradingBot:
    """Daily trading bot for Alpaca API"""
    
    def __init__(self, config):
        """Initialize the trading bot with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Market hours constants (Eastern Time)
        self.MARKET_OPEN_TIME = datetime_time(9, 30)
        self.MARKET_CLOSE_TIME = datetime_time(16, 0)
        
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
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
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
            current_time = now_et.time()
            
            is_open = self.MARKET_OPEN_TIME <= current_time <= self.MARKET_CLOSE_TIME
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
            request = StockLatestQuoteRequest(
                symbol_or_symbols=symbol,
                feed='iex'  # Use IEX feed for free/paper accounts instead of SIP
            )
            quote = self.data_client.get_stock_latest_quote(request)
            
            if symbol in quote:
                return float(quote[symbol].ask_price)
            else:
                raise ValueError(f"No quote data for {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol, days=60):
        """Get historical price data for technical analysis"""
        try:
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=days)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date,
                feed='iex'  # Use IEX feed for free/paper accounts instead of SIP
            )
            
            bars = self.data_client.get_stock_bars(request)
            
            if symbol not in bars.data:
                self.logger.warning(f"No historical data for {symbol}")
                return None
            
            # Convert to pandas DataFrame
            df = pd.DataFrame([{
                'timestamp': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume)
            } for bar in bars.data[symbol]])
            
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators for signal generation"""
        if df is None or len(df) < 30:
            return None
        
        try:
            # RSI (Relative Strength Index)
            rsi_indicator = RSIIndicator(close=df['close'], window=14)
            df['rsi'] = rsi_indicator.rsi()
            
            # MACD (Moving Average Convergence Divergence)
            macd_indicator = MACD(
                close=df['close'],
                window_slow=26,
                window_fast=12,
                window_sign=9
            )
            df['macd'] = macd_indicator.macd()
            df['macd_signal'] = macd_indicator.macd_signal()
            df['macd_diff'] = macd_indicator.macd_diff()
            
            # Moving Averages
            sma_20 = SMAIndicator(close=df['close'], window=20)
            sma_50 = SMAIndicator(close=df['close'], window=50)
            ema_12 = EMAIndicator(close=df['close'], window=12)
            
            df['sma_20'] = sma_20.sma_indicator()
            df['sma_50'] = sma_50.sma_indicator()
            df['ema_12'] = ema_12.ema_indicator()
            
            # Volume analysis
            df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma_20']
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to calculate technical indicators: {e}")
            return None
    
    def analyze_volume(self, df):
        """Analyze volume patterns for signals"""
        if df is None or len(df) < 2:
            return None, None
        
        try:
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # High volume breakout
            if latest['volume_ratio'] > 1.5:
                if latest['close'] > previous['close']:
                    return 'BULLISH', f"High volume breakout (ratio: {latest['volume_ratio']:.2f})"
                else:
                    return 'BEARISH', f"High volume selling (ratio: {latest['volume_ratio']:.2f})"
            
            # Low volume - caution
            if latest['volume_ratio'] < 0.5:
                return 'NEUTRAL', f"Low volume (ratio: {latest['volume_ratio']:.2f})"
            
            return 'NEUTRAL', "Normal volume"
            
        except Exception as e:
            self.logger.error(f"Failed to analyze volume: {e}")
            return None, None
    
    def detect_price_patterns(self, df):
        """Detect common price patterns"""
        if df is None or len(df) < 10:
            return None, None
        
        try:
            recent_data = df.tail(10)
            latest = df.iloc[-1]
            
            # Double top pattern (bearish)
            highs = recent_data['high'].values
            if len(highs) >= 5:
                # Find local maxima
                peaks = []
                for i in range(1, len(highs)-1):
                    if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                        peaks.append(highs[i])
                
                # Check for double top
                if len(peaks) >= 2:
                    if abs(peaks[-1] - peaks[-2]) / peaks[-1] < 0.02:  # Within 2%
                        if latest['close'] < min(highs[-3:]):
                            return 'BEARISH', "Double top pattern detected"
            
            # Double bottom pattern (bullish)
            lows = recent_data['low'].values
            if len(lows) >= 5:
                # Find local minima
                troughs = []
                for i in range(1, len(lows)-1):
                    if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                        troughs.append(lows[i])
                
                # Check for double bottom
                if len(troughs) >= 2:
                    if abs(troughs[-1] - troughs[-2]) / troughs[-1] < 0.02:  # Within 2%
                        if latest['close'] > max(lows[-3:]):
                            return 'BULLISH', "Double bottom pattern detected"
            
            # Simple trend detection
            if latest['close'] > recent_data['close'].mean() * 1.05:
                return 'BULLISH', "Strong upward trend"
            elif latest['close'] < recent_data['close'].mean() * 0.95:
                return 'BEARISH', "Strong downward trend"
            
            return 'NEUTRAL', "No clear pattern"
            
        except Exception as e:
            self.logger.error(f"Failed to detect price patterns: {e}")
            return None, None
    
    def analyze_sentiment(self, symbol):
        """Simple sentiment analysis based on symbol name
        
        In production, this would integrate with news APIs like NewsAPI, 
        Alpha Vantage, or Finnhub to get actual news articles.
        For this implementation, we'll use a simplified approach.
        """
        try:
            # Placeholder sentiment - in production, fetch real news
            # For now, return neutral sentiment
            # You would integrate with NewsAPI or similar service here
            
            # Example of how sentiment would work with real news:
            # news_items = fetch_news(symbol)  # Would fetch from API
            # sentiments = [self.sentiment_analyzer.polarity_scores(item['headline']) for item in news_items]
            # avg_sentiment = np.mean([s['compound'] for s in sentiments])
            
            # For this implementation, we return neutral
            sentiment_score = 0.0  # Neutral
            
            if sentiment_score > 0.3:
                return 'POSITIVE', f"Positive news sentiment (score: {sentiment_score:.2f})"
            elif sentiment_score < -0.3:
                return 'NEGATIVE', f"Negative news sentiment (score: {sentiment_score:.2f})"
            else:
                return 'NEUTRAL', f"Neutral news sentiment (score: {sentiment_score:.2f})"
                
        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment: {e}")
            return 'NEUTRAL', "Sentiment analysis unavailable"
    
    def generate_signals_with_metadata(self, symbol):
        """Generate trading signals with detailed metadata for reporting
        
        Returns:
            Tuple of (signals, metadata) where:
            - signals: List of tuples (action, reason)
            - metadata: Dict with analysis details
        """
        signals = self.generate_signals(symbol)
        
        # Generate metadata by re-running analysis (lightweight)
        metadata = {
            'symbol': symbol,
            'signals': signals,
            'buy_count': 0,
            'sell_count': 0,
            'factors': []
        }
        
        try:
            df = self.get_historical_data(symbol)
            if df is not None and len(df) >= 30:
                df = self.calculate_technical_indicators(df)
                if df is not None:
                    latest = df.iloc[-1]
                    previous = df.iloc[-2] if len(df) > 1 else latest
                    
                    # Count signals
                    buy_signals = 0
                    sell_signals = 0
                    factors = []
                    
                    # RSI
                    if not pd.isna(latest['rsi']):
                        if latest['rsi'] < 30:
                            buy_signals += 1
                            factors.append(f"RSI oversold ({latest['rsi']:.2f})")
                        elif latest['rsi'] > 70:
                            sell_signals += 1
                            factors.append(f"RSI overbought ({latest['rsi']:.2f})")
                    
                    # MACD
                    if (not pd.isna(latest['macd']) and not pd.isna(previous['macd']) and
                        not pd.isna(latest['macd_signal']) and not pd.isna(previous['macd_signal'])):
                        if previous['macd'] < previous['macd_signal'] and latest['macd'] > latest['macd_signal']:
                            buy_signals += 1
                            factors.append("MACD bullish crossover")
                        elif previous['macd'] > previous['macd_signal'] and latest['macd'] < latest['macd_signal']:
                            sell_signals += 1
                            factors.append("MACD bearish crossover")
                    
                    # Moving averages
                    if (not pd.isna(latest['sma_20']) and not pd.isna(latest['sma_50']) and
                        not pd.isna(previous['sma_20']) and not pd.isna(previous['sma_50'])):
                        if previous['sma_20'] < previous['sma_50'] and latest['sma_20'] > latest['sma_50']:
                            buy_signals += 1
                            factors.append("Golden cross")
                        elif previous['sma_20'] > previous['sma_50'] and latest['sma_20'] < latest['sma_50']:
                            sell_signals += 1
                            factors.append("Death cross")
                        
                        if latest['close'] > latest['sma_20'] > latest['sma_50']:
                            buy_signals += 1
                            factors.append("Price above rising MAs")
                        elif latest['close'] < latest['sma_20'] < latest['sma_50']:
                            sell_signals += 1
                            factors.append("Price below falling MAs")
                    
                    # Volume, patterns, sentiment
                    volume_signal, volume_reason = self.analyze_volume(df)
                    pattern_signal, pattern_reason = self.detect_price_patterns(df)
                    sentiment_signal, sentiment_reason = self.analyze_sentiment(symbol)
                    
                    if volume_signal == 'BULLISH':
                        buy_signals += 1
                        factors.append(volume_reason)
                    elif volume_signal == 'BEARISH':
                        sell_signals += 1
                        factors.append(volume_reason)
                    
                    if pattern_signal == 'BULLISH':
                        buy_signals += 1
                        factors.append(pattern_reason)
                    elif pattern_signal == 'BEARISH':
                        sell_signals += 1
                        factors.append(pattern_reason)
                    
                    if sentiment_signal == 'POSITIVE':
                        buy_signals += 1
                        factors.append(sentiment_reason)
                    elif sentiment_signal == 'NEGATIVE':
                        sell_signals += 1
                        factors.append(sentiment_reason)
                    
                    metadata['buy_count'] = buy_signals
                    metadata['sell_count'] = sell_signals
                    metadata['factors'] = factors
        
        except Exception as e:
            self.logger.error(f"Error generating metadata for {symbol}: {e}")
        
        return signals, metadata
    
    def generate_signals(self, symbol):
        """Generate trading signals for a symbol
        
        Analyzes multiple factors to generate actionable buy/sell signals:
        - Technical indicators (RSI, MACD, moving averages)
        - Volume analysis
        - Price patterns
        - News sentiment
        
        Returns:
            List of tuples (action, reason) where action is 'BUY' or 'SELL'
        """
        self.logger.info(f"Generating signals for {symbol}")
        signals = []
        
        try:
            # Get historical data
            df = self.get_historical_data(symbol)
            if df is None or len(df) < 30:
                self.logger.warning(f"Insufficient data for {symbol}")
                return []
            
            # Calculate technical indicators
            df = self.calculate_technical_indicators(df)
            if df is None:
                self.logger.warning(f"Failed to calculate indicators for {symbol}")
                return []
            
            # Get latest values
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            
            # Analyze different factors
            volume_signal, volume_reason = self.analyze_volume(df)
            pattern_signal, pattern_reason = self.detect_price_patterns(df)
            sentiment_signal, sentiment_reason = self.analyze_sentiment(symbol)
            
            # Technical Indicator Analysis
            buy_signals = 0
            sell_signals = 0
            reasons = []
            
            # RSI Analysis
            if not pd.isna(latest['rsi']):
                if latest['rsi'] < 30:
                    buy_signals += 1
                    reasons.append(f"RSI oversold ({latest['rsi']:.2f})")
                elif latest['rsi'] > 70:
                    sell_signals += 1
                    reasons.append(f"RSI overbought ({latest['rsi']:.2f})")
            
            # MACD Analysis
            if (not pd.isna(latest['macd']) and not pd.isna(previous['macd']) and
                not pd.isna(latest['macd_signal']) and not pd.isna(previous['macd_signal'])):
                # MACD crossover
                if previous['macd'] < previous['macd_signal'] and latest['macd'] > latest['macd_signal']:
                    buy_signals += 1
                    reasons.append("MACD bullish crossover")
                elif previous['macd'] > previous['macd_signal'] and latest['macd'] < latest['macd_signal']:
                    sell_signals += 1
                    reasons.append("MACD bearish crossover")
            
            # Moving Average Analysis
            if (not pd.isna(latest['sma_20']) and not pd.isna(latest['sma_50']) and
                not pd.isna(previous['sma_20']) and not pd.isna(previous['sma_50'])):
                # Golden cross / Death cross
                if previous['sma_20'] < previous['sma_50'] and latest['sma_20'] > latest['sma_50']:
                    buy_signals += 1
                    reasons.append("Golden cross (SMA 20 > SMA 50)")
                elif previous['sma_20'] > previous['sma_50'] and latest['sma_20'] < latest['sma_50']:
                    sell_signals += 1
                    reasons.append("Death cross (SMA 20 < SMA 50)")
                
                # Price vs SMA
                if latest['close'] > latest['sma_20'] > latest['sma_50']:
                    buy_signals += 1
                    reasons.append("Price above rising moving averages")
                elif latest['close'] < latest['sma_20'] < latest['sma_50']:
                    sell_signals += 1
                    reasons.append("Price below falling moving averages")
            
            # Volume Analysis
            if volume_signal == 'BULLISH':
                buy_signals += 1
                reasons.append(volume_reason)
            elif volume_signal == 'BEARISH':
                sell_signals += 1
                reasons.append(volume_reason)
            
            # Price Pattern Analysis
            if pattern_signal == 'BULLISH':
                buy_signals += 1
                reasons.append(pattern_reason)
            elif pattern_signal == 'BEARISH':
                sell_signals += 1
                reasons.append(pattern_reason)
            
            # Sentiment Analysis
            if sentiment_signal == 'POSITIVE':
                buy_signals += 1
                reasons.append(sentiment_reason)
            elif sentiment_signal == 'NEGATIVE':
                sell_signals += 1
                reasons.append(sentiment_reason)
            
            # Generate final signals based on majority
            if buy_signals >= 3:  # At least 3 buy signals
                signal_reason = "BUY: " + ", ".join(reasons)
                signals.append(('BUY', signal_reason))
                self.logger.info(f"{symbol}: {signal_reason}")
            elif sell_signals >= 3:  # At least 3 sell signals
                signal_reason = "SELL: " + ", ".join(reasons)
                signals.append(('SELL', signal_reason))
                self.logger.info(f"{symbol}: {signal_reason}")
            else:
                self.logger.info(f"{symbol}: No strong signal (Buy: {buy_signals}, Sell: {sell_signals})")
                if reasons:
                    self.logger.info(f"{symbol}: Factors considered: {', '.join(reasons)}")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol}: {e}")
            return []
    
    def generate_daily_report(self, symbols_analyzed, all_signals, trades_executed=None):
        """Generate comprehensive daily trading report
        
        Args:
            symbols_analyzed: Dict mapping symbol to analysis data
                {symbol: {'signals': [...], 'buy_count': int, 'sell_count': int, 'factors': [...]}}
            all_signals: List of all signals generated across symbols
            trades_executed: List of trades executed (optional)
            
        Returns:
            Dict containing daily report data
        """
        try:
            from datetime import datetime
            
            # Get account info
            try:
                account_info = self.get_account_info()
            except Exception as e:
                self.logger.warning(f"Could not fetch account info: {e}")
                account_info = {'equity': 0, 'buying_power': 0, 'cash': 0}
            
            # Calculate statistics
            total_symbols = len(symbols_analyzed)
            symbols_with_signals = sum(1 for s in symbols_analyzed.values() if s.get('signals'))
            total_buy_signals = sum(s.get('buy_count', 0) for s in symbols_analyzed.values())
            total_sell_signals = sum(s.get('sell_count', 0) for s in symbols_analyzed.values())
            
            # Prepare symbol details
            symbol_details = []
            for symbol, data in symbols_analyzed.items():
                signals = data.get('signals', [])
                symbol_details.append({
                    'symbol': symbol,
                    'action': signals[0][0] if signals else 'HOLD',
                    'reason': signals[0][1] if signals else 'No strong signal',
                    'buy_indicators': data.get('buy_count', 0),
                    'sell_indicators': data.get('sell_count', 0),
                    'factors': data.get('factors', [])
                })
            
            # Build report
            report = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'account': {
                    'equity': account_info.get('equity', 0),
                    'buying_power': account_info.get('buying_power', 0),
                    'cash': account_info.get('cash', 0)
                },
                'analysis': {
                    'symbols_analyzed': total_symbols,
                    'symbols_with_signals': symbols_with_signals,
                    'total_buy_signals': total_buy_signals,
                    'total_sell_signals': total_sell_signals,
                    'signals_generated': len(all_signals)
                },
                'symbols': symbol_details,
                'trades': trades_executed if trades_executed else [],
                'summary': {
                    'trades_executed': len(trades_executed) if trades_executed else 0,
                    'expected_daily_trades': '0-3 (conservative)',
                    'signal_threshold': '≥3 indicators required'
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            return {
                'error': str(e),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat()
            }
    
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

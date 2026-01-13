# tests/test_bot.py
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot import DailyTradingBot
from config import Config


class TestGenerateSignals(unittest.TestCase):
    """Test suite for the generate_signals method and related helper methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock config
        self.mock_config = Mock(spec=Config)
        self.mock_config.ALPACA_API_KEY = "test_key"
        self.mock_config.ALPACA_SECRET = "test_secret"
        self.mock_config.APCA_PAPER = True
        self.mock_config.DRY_RUN = True
        self.mock_config.TRADING_SYMBOLS = ['AAPL', 'GOOG']
        
        # Create sample historical data
        dates = pd.date_range(end=datetime.now(pytz.UTC), periods=60, freq='D')
        self.sample_data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 60),
            'high': np.random.uniform(110, 115, 60),
            'low': np.random.uniform(95, 100, 60),
            'close': np.random.uniform(100, 110, 60),
            'volume': np.random.uniform(1000000, 5000000, 60)
        }, index=dates)
        
        # Create bullish trend data
        self.bullish_data = self.sample_data.copy()
        for i in range(len(self.bullish_data)):
            self.bullish_data.iloc[i, self.bullish_data.columns.get_loc('close')] = 100 + i * 0.5
        
        # Create bearish trend data
        self.bearish_data = self.sample_data.copy()
        for i in range(len(self.bearish_data)):
            self.bearish_data.iloc[i, self.bearish_data.columns.get_loc('close')] = 130 - i * 0.5
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_bot_initialization(self, mock_data_client, mock_trading_client):
        """Test that bot initializes correctly with sentiment analyzer"""
        bot = DailyTradingBot(self.mock_config)
        
        # Check that sentiment analyzer is initialized
        self.assertIsNotNone(bot.sentiment_analyzer)
        self.assertTrue(hasattr(bot, 'sentiment_analyzer'))
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_calculate_technical_indicators(self, mock_data_client, mock_trading_client):
        """Test that technical indicators are calculated correctly"""
        bot = DailyTradingBot(self.mock_config)
        
        df = bot.calculate_technical_indicators(self.sample_data.copy())
        
        # Check that all indicators are present
        self.assertIsNotNone(df)
        self.assertIn('rsi', df.columns)
        self.assertIn('macd', df.columns)
        self.assertIn('macd_signal', df.columns)
        self.assertIn('macd_diff', df.columns)
        self.assertIn('sma_20', df.columns)
        self.assertIn('sma_50', df.columns)
        self.assertIn('ema_12', df.columns)
        self.assertIn('volume_sma_20', df.columns)
        self.assertIn('volume_ratio', df.columns)
        
        # Check that RSI is in valid range (0-100)
        valid_rsi = df['rsi'].dropna()
        self.assertTrue(all(valid_rsi >= 0))
        self.assertTrue(all(valid_rsi <= 100))
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_calculate_technical_indicators_insufficient_data(self, mock_data_client, mock_trading_client):
        """Test that technical indicators return None with insufficient data"""
        bot = DailyTradingBot(self.mock_config)
        
        # Create data with only 10 rows (insufficient)
        small_df = self.sample_data.head(10)
        df = bot.calculate_technical_indicators(small_df)
        
        # Should return None for insufficient data
        self.assertIsNone(df)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_analyze_volume_high_bullish(self, mock_data_client, mock_trading_client):
        """Test volume analysis detects high volume bullish signal"""
        bot = DailyTradingBot(self.mock_config)
        
        # Create data with high volume spike and price increase
        df = self.sample_data.copy()
        df = bot.calculate_technical_indicators(df)
        
        # Manually set high volume ratio for latest row
        df.iloc[-1, df.columns.get_loc('volume_ratio')] = 2.0
        df.iloc[-1, df.columns.get_loc('close')] = df.iloc[-2]['close'] * 1.05
        
        signal, reason = bot.analyze_volume(df)
        
        self.assertEqual(signal, 'BULLISH')
        self.assertIn('High volume breakout', reason)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_analyze_volume_high_bearish(self, mock_data_client, mock_trading_client):
        """Test volume analysis detects high volume bearish signal"""
        bot = DailyTradingBot(self.mock_config)
        
        # Create data with high volume spike and price decrease
        df = self.sample_data.copy()
        df = bot.calculate_technical_indicators(df)
        
        # Manually set high volume ratio for latest row with price drop
        df.iloc[-1, df.columns.get_loc('volume_ratio')] = 2.0
        df.iloc[-1, df.columns.get_loc('close')] = df.iloc[-2]['close'] * 0.95
        
        signal, reason = bot.analyze_volume(df)
        
        self.assertEqual(signal, 'BEARISH')
        self.assertIn('High volume selling', reason)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_analyze_volume_low(self, mock_data_client, mock_trading_client):
        """Test volume analysis detects low volume"""
        bot = DailyTradingBot(self.mock_config)
        
        # Create data with low volume
        df = self.sample_data.copy()
        df = bot.calculate_technical_indicators(df)
        
        # Manually set low volume ratio
        df.iloc[-1, df.columns.get_loc('volume_ratio')] = 0.3
        
        signal, reason = bot.analyze_volume(df)
        
        self.assertEqual(signal, 'NEUTRAL')
        self.assertIn('Low volume', reason)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_detect_price_patterns_uptrend(self, mock_data_client, mock_trading_client):
        """Test price pattern detection for uptrend"""
        bot = DailyTradingBot(self.mock_config)
        
        # Use bullish trend data
        df = self.bullish_data.copy()
        
        signal, reason = bot.detect_price_patterns(df)
        
        # Should detect bullish pattern or neutral (uptrend might not exceed threshold)
        self.assertIn(signal, ['BULLISH', 'NEUTRAL'])
        self.assertIsNotNone(reason)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_detect_price_patterns_downtrend(self, mock_data_client, mock_trading_client):
        """Test price pattern detection for downtrend"""
        bot = DailyTradingBot(self.mock_config)
        
        # Use bearish trend data
        df = self.bearish_data.copy()
        
        signal, reason = bot.detect_price_patterns(df)
        
        # Should detect bearish pattern or neutral (downtrend might not exceed threshold)
        self.assertIn(signal, ['BEARISH', 'NEUTRAL'])
        self.assertIsNotNone(reason)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_analyze_sentiment(self, mock_data_client, mock_trading_client):
        """Test sentiment analysis returns a valid sentiment"""
        bot = DailyTradingBot(self.mock_config)
        
        signal, reason = bot.analyze_sentiment('AAPL')
        
        # Should return one of the valid sentiment signals
        self.assertIn(signal, ['POSITIVE', 'NEGATIVE', 'NEUTRAL'])
        self.assertIsNotNone(reason)
        self.assertIsInstance(reason, str)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_generate_signals_with_mock_data(self, mock_data_client, mock_trading_client):
        """Test generate_signals with mocked historical data"""
        bot = DailyTradingBot(self.mock_config)
        
        # Mock get_historical_data to return our sample data
        with patch.object(bot, 'get_historical_data', return_value=self.sample_data.copy()):
            signals = bot.generate_signals('AAPL')
        
        # Should return a list
        self.assertIsInstance(signals, list)
        
        # Each signal should be a tuple of (action, reason)
        for signal in signals:
            self.assertIsInstance(signal, tuple)
            self.assertEqual(len(signal), 2)
            action, reason = signal
            self.assertIn(action, ['BUY', 'SELL'])
            self.assertIsInstance(reason, str)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_generate_signals_bullish_scenario(self, mock_data_client, mock_trading_client):
        """Test generate_signals with strong bullish indicators"""
        bot = DailyTradingBot(self.mock_config)
        
        # Create strong bullish data
        df = self.bullish_data.copy()
        df = bot.calculate_technical_indicators(df)
        
        # Set RSI to oversold
        df.iloc[-1, df.columns.get_loc('rsi')] = 25
        
        # Mock get_historical_data to return our bullish data
        with patch.object(bot, 'get_historical_data', return_value=df):
            signals = bot.generate_signals('AAPL')
        
        # With strong bullish indicators, should generate buy signal
        if signals:
            self.assertEqual(signals[0][0], 'BUY')
            self.assertIn('BUY:', signals[0][1])
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_generate_signals_bearish_scenario(self, mock_data_client, mock_trading_client):
        """Test generate_signals with strong bearish indicators"""
        bot = DailyTradingBot(self.mock_config)
        
        # Create strong bearish data
        df = self.bearish_data.copy()
        df = bot.calculate_technical_indicators(df)
        
        # Set RSI to overbought
        df.iloc[-1, df.columns.get_loc('rsi')] = 75
        
        # Mock get_historical_data to return our bearish data
        with patch.object(bot, 'get_historical_data', return_value=df):
            signals = bot.generate_signals('AAPL')
        
        # With strong bearish indicators, should generate sell signal
        if signals:
            self.assertEqual(signals[0][0], 'SELL')
            self.assertIn('SELL:', signals[0][1])
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_generate_signals_insufficient_data(self, mock_data_client, mock_trading_client):
        """Test generate_signals handles insufficient data gracefully"""
        bot = DailyTradingBot(self.mock_config)
        
        # Mock get_historical_data to return insufficient data
        small_df = self.sample_data.head(10)
        with patch.object(bot, 'get_historical_data', return_value=small_df):
            signals = bot.generate_signals('AAPL')
        
        # Should return empty list for insufficient data
        self.assertEqual(signals, [])
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_generate_signals_no_data(self, mock_data_client, mock_trading_client):
        """Test generate_signals handles no data gracefully"""
        bot = DailyTradingBot(self.mock_config)
        
        # Mock get_historical_data to return None
        with patch.object(bot, 'get_historical_data', return_value=None):
            signals = bot.generate_signals('AAPL')
        
        # Should return empty list when no data available
        self.assertEqual(signals, [])
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_generate_signals_logs_reasoning(self, mock_data_client, mock_trading_client):
        """Test that generate_signals logs the reasoning for signals"""
        bot = DailyTradingBot(self.mock_config)
        
        # Mock get_historical_data
        with patch.object(bot, 'get_historical_data', return_value=self.sample_data.copy()):
            # Capture log messages
            with self.assertLogs(bot.logger, level='INFO') as cm:
                signals = bot.generate_signals('AAPL')
        
        # Should have logged something about signal generation
        log_output = '\n'.join(cm.output)
        self.assertIn('AAPL', log_output)
        self.assertIn('Generating signals', log_output)


class TestTechnicalIndicatorEdgeCases(unittest.TestCase):
    """Test edge cases for technical indicator calculations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock(spec=Config)
        self.mock_config.ALPACA_API_KEY = "test_key"
        self.mock_config.ALPACA_SECRET = "test_secret"
        self.mock_config.APCA_PAPER = True
        self.mock_config.DRY_RUN = True
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_calculate_indicators_with_none(self, mock_data_client, mock_trading_client):
        """Test that calculate_technical_indicators handles None input"""
        bot = DailyTradingBot(self.mock_config)
        
        result = bot.calculate_technical_indicators(None)
        
        self.assertIsNone(result)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_analyze_volume_with_none(self, mock_data_client, mock_trading_client):
        """Test that analyze_volume handles None input"""
        bot = DailyTradingBot(self.mock_config)
        
        signal, reason = bot.analyze_volume(None)
        
        self.assertIsNone(signal)
        self.assertIsNone(reason)
    
    @patch('bot.TradingClient')
    @patch('bot.StockHistoricalDataClient')
    def test_detect_price_patterns_with_none(self, mock_data_client, mock_trading_client):
        """Test that detect_price_patterns handles None input"""
        bot = DailyTradingBot(self.mock_config)
        
        signal, reason = bot.detect_price_patterns(None)
        
        self.assertIsNone(signal)
        self.assertIsNone(reason)


if __name__ == '__main__':
    unittest.main()

# tests/test_stock_selector.py
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stock_selector import DynamicStockSelector


class TestDynamicStockSelector(unittest.TestCase):
    """Test suite for DynamicStockSelector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_client = Mock()
        self.selector = DynamicStockSelector(self.mock_data_client)
    
    def test_get_all_symbols(self):
        """Test getting all symbols from stock universe"""
        symbols = self.selector.get_all_symbols()
        
        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0)
        
        # Check that common stocks are in the list
        self.assertIn('AAPL', symbols)
        self.assertIn('MSFT', symbols)
        
        # Check for no duplicates
        self.assertEqual(len(symbols), len(set(symbols)))
    
    def test_get_diversified_stocks(self):
        """Test diversified stock selection"""
        stocks = self.selector.get_diversified_stocks(stocks_per_sector=2, sectors=None)
        
        self.assertIsInstance(stocks, list)
        self.assertGreater(len(stocks), 0)
        
        # With 2 stocks per sector and 8 sectors, should get 16 stocks
        self.assertLessEqual(len(stocks), 16)
    
    def test_get_diversified_stocks_specific_sectors(self):
        """Test diversified selection with specific sectors"""
        sectors = ['Technology', 'Financial']
        stocks = self.selector.get_diversified_stocks(stocks_per_sector=2, sectors=sectors)
        
        self.assertIsInstance(stocks, list)
        
        # Should get 4 stocks (2 from each sector)
        self.assertEqual(len(stocks), 4)
    
    def test_select_stocks_diversified(self):
        """Test stock selection with diversified method"""
        stocks = self.selector.select_stocks(method='diversified', limit=10)
        
        self.assertIsInstance(stocks, list)
        self.assertLessEqual(len(stocks), 10)
    
    def test_select_stocks_unknown_method(self):
        """Test stock selection with unknown method defaults to diversified"""
        stocks = self.selector.select_stocks(method='unknown_method', limit=5)
        
        self.assertIsInstance(stocks, list)
        # Should still return stocks (fallback to diversified)
        self.assertGreater(len(stocks), 0)
    
    def test_get_selection_info(self):
        """Test getting selection info"""
        symbols = ['AAPL', 'MSFT', 'JPM', 'BAC']
        info = self.selector.get_selection_info(symbols)
        
        self.assertIsInstance(info, dict)
        self.assertIn('total_stocks', info)
        self.assertIn('sectors_represented', info)
        self.assertIn('sector_distribution', info)
        self.assertIn('symbols', info)
        
        self.assertEqual(info['total_stocks'], 4)
        self.assertEqual(info['symbols'], symbols)
        
        # Should have Technology and Financial sectors
        self.assertIn('Technology', info['sector_distribution'])
        self.assertIn('Financial', info['sector_distribution'])
    
    def test_get_tradable_stocks_from_broker_no_client(self):
        """Test broker retrieval without trading client"""
        # Selector without trading client
        selector = DynamicStockSelector(self.mock_data_client, None)
        stocks = selector.get_tradable_stocks_from_broker()
        
        # Should return empty list
        self.assertEqual(stocks, [])
    
    def test_get_tradable_stocks_from_broker_with_client(self):
        """Test broker retrieval with trading client"""
        # Mock trading client
        mock_trading_client = Mock()
        
        # Mock assets
        mock_asset1 = Mock()
        mock_asset1.symbol = 'AAPL'
        mock_asset1.tradable = True
        mock_asset1.fractionable = True
        mock_asset1.shortable = True
        
        mock_asset2 = Mock()
        mock_asset2.symbol = 'MSFT'
        mock_asset2.tradable = True
        mock_asset2.fractionable = True
        mock_asset2.shortable = True
        
        mock_asset3 = Mock()
        mock_asset3.symbol = 'UNTRADABLE'
        mock_asset3.tradable = False
        mock_asset3.fractionable = False
        mock_asset3.shortable = False
        
        mock_trading_client.get_all_assets.return_value = [mock_asset1, mock_asset2, mock_asset3]
        
        selector = DynamicStockSelector(self.mock_data_client, mock_trading_client)
        stocks = selector.get_tradable_stocks_from_broker()
        
        # Should return only tradable stocks
        self.assertIn('AAPL', stocks)
        self.assertIn('MSFT', stocks)
        self.assertNotIn('UNTRADABLE', stocks)
        self.assertEqual(len(stocks), 2)
    
    def test_broker_universe_caching(self):
        """Test that broker universe results are cached"""
        mock_trading_client = Mock()
        mock_asset = Mock()
        mock_asset.symbol = 'AAPL'
        mock_asset.tradable = True
        mock_asset.fractionable = True
        mock_asset.shortable = True
        
        mock_trading_client.get_all_assets.return_value = [mock_asset]
        
        selector = DynamicStockSelector(self.mock_data_client, mock_trading_client)
        
        # First call
        stocks1 = selector.get_tradable_stocks_from_broker()
        
        # Second call with cache
        stocks2 = selector.get_tradable_stocks_from_broker(use_cache=True)
        
        # Should only call API once due to caching
        self.assertEqual(mock_trading_client.get_all_assets.call_count, 1)
        self.assertEqual(stocks1, stocks2)
    
    def test_get_tradable_stocks_from_broker_with_exchange_filter(self):
        """Test broker retrieval with exchange filtering"""
        mock_trading_client = Mock()
        
        # Mock assets from different exchanges
        mock_asset_nyse = Mock()
        mock_asset_nyse.symbol = 'NYSE_STOCK'
        mock_asset_nyse.tradable = True
        mock_asset_nyse.fractionable = True
        mock_asset_nyse.shortable = True
        mock_asset_nyse.exchange = 'AssetExchange.NYSE'
        
        mock_asset_nasdaq = Mock()
        mock_asset_nasdaq.symbol = 'NASDAQ_STOCK'
        mock_asset_nasdaq.tradable = True
        mock_asset_nasdaq.fractionable = True
        mock_asset_nasdaq.shortable = True
        mock_asset_nasdaq.exchange = 'AssetExchange.NASDAQ'
        
        mock_asset_amex = Mock()
        mock_asset_amex.symbol = 'AMEX_STOCK'
        mock_asset_amex.tradable = True
        mock_asset_amex.fractionable = True
        mock_asset_amex.shortable = True
        mock_asset_amex.exchange = 'AssetExchange.AMEX'
        
        mock_trading_client.get_all_assets.return_value = [mock_asset_nyse, mock_asset_nasdaq, mock_asset_amex]
        
        selector = DynamicStockSelector(self.mock_data_client, mock_trading_client)
        
        # Test filtering to NYSE and NASDAQ only
        stocks = selector.get_tradable_stocks_from_broker(exchanges=['NYSE', 'NASDAQ'])
        
        # Should include NYSE and NASDAQ stocks only
        self.assertIn('NYSE_STOCK', stocks)
        self.assertIn('NASDAQ_STOCK', stocks)
        self.assertNotIn('AMEX_STOCK', stocks)
        self.assertEqual(len(stocks), 2)
    
    def test_exchange_filter_cache_key(self):
        """Test that exchange filters use different cache keys"""
        mock_trading_client = Mock()
        
        mock_asset = Mock()
        mock_asset.symbol = 'TEST'
        mock_asset.tradable = True
        mock_asset.fractionable = True
        mock_asset.shortable = True
        mock_asset.exchange = 'AssetExchange.NYSE'
        
        mock_trading_client.get_all_assets.return_value = [mock_asset]
        
        selector = DynamicStockSelector(self.mock_data_client, mock_trading_client)
        
        # First call with NYSE filter
        stocks1 = selector.get_tradable_stocks_from_broker(exchanges=['NYSE'])
        
        # Second call with different filter should not use cache
        stocks2 = selector.get_tradable_stocks_from_broker(exchanges=['NASDAQ'])
        
        # Should call API twice due to different cache keys
        self.assertEqual(mock_trading_client.get_all_assets.call_count, 2)
    
    def test_stock_universe_structure(self):
        """Test that stock universe has expected structure"""
        self.assertIsInstance(self.selector.STOCK_UNIVERSE, dict)
        
        # Check for expected sectors
        expected_sectors = ['Technology', 'Financial', 'Healthcare', 'Consumer', 'Energy']
        for sector in expected_sectors:
            self.assertIn(sector, self.selector.STOCK_UNIVERSE)
            self.assertIsInstance(self.selector.STOCK_UNIVERSE[sector], list)
            self.assertGreater(len(self.selector.STOCK_UNIVERSE[sector]), 0)



if __name__ == '__main__':
    unittest.main()

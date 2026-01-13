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

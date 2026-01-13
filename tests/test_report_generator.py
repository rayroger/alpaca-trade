# tests/test_report_generator.py
import unittest
from unittest.mock import Mock, patch
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from report_generator import DailyReportGenerator


class TestDailyReportGenerator(unittest.TestCase):
    """Test suite for DailyReportGenerator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = DailyReportGenerator()
        
        # Sample report data
        self.sample_report = {
            'date': '2026-01-13',
            'timestamp': '2026-01-13T15:30:00',
            'account': {
                'equity': 10000.0,
                'buying_power': 5000.0,
                'cash': 2000.0
            },
            'analysis': {
                'symbols_analyzed': 3,
                'symbols_with_signals': 1,
                'total_buy_signals': 4,
                'total_sell_signals': 1,
                'signals_generated': 1
            },
            'symbols': [
                {
                    'symbol': 'AAPL',
                    'action': 'BUY',
                    'buy_indicators': 4,
                    'sell_indicators': 0,
                    'factors': ['RSI oversold', 'MACD bullish crossover']
                },
                {
                    'symbol': 'GOOG',
                    'action': 'HOLD',
                    'buy_indicators': 2,
                    'sell_indicators': 1,
                    'factors': ['Normal volume']
                }
            ],
            'trades': [
                {
                    'symbol': 'AAPL',
                    'action': 'BUY',
                    'shares': 10,
                    'price': 150.0
                }
            ],
            'summary': {
                'trades_executed': 1
            }
        }
    
    def test_generate_summary_table(self):
        """Test summary table generation"""
        reports = [self.sample_report]
        html = self.generator.generate_summary_table(reports)
        
        self.assertIsInstance(html, str)
        self.assertIn('summary-table', html)
        self.assertIn('2026-01-13', html)
        self.assertIn('$10,000.00', html)
    
    def test_generate_summary_table_empty(self):
        """Test summary table with no data"""
        html = self.generator.generate_summary_table([])
        
        self.assertIn('No recent trading data', html)
    
    def test_generate_symbol_performance_table(self):
        """Test symbol performance table generation"""
        html = self.generator.generate_symbol_performance_table(self.sample_report)
        
        self.assertIsInstance(html, str)
        self.assertIn('symbol-table', html)
        self.assertIn('AAPL', html)
        self.assertIn('BUY', html)
        self.assertIn('HOLD', html)
    
    def test_generate_symbol_performance_table_empty(self):
        """Test symbol performance table with no symbols"""
        report = {'symbols': []}
        html = self.generator.generate_symbol_performance_table(report)
        
        self.assertIn('No symbol data', html)
    
    def test_generate_equity_chart_data(self):
        """Test equity chart generation"""
        reports = [self.sample_report]
        html = self.generator.generate_equity_chart_data(reports)
        
        self.assertIsInstance(html, str)
        self.assertIn('chart-container', html)
        self.assertIn('Account Equity', html)
        self.assertIn('$10,000.00', html)
    
    def test_generate_equity_chart_data_empty(self):
        """Test equity chart with no data"""
        html = self.generator.generate_equity_chart_data([])
        
        self.assertIn('No data available', html)
    
    def test_generate_signals_chart(self):
        """Test signals chart generation"""
        reports = [self.sample_report]
        html = self.generator.generate_signals_chart(reports)
        
        self.assertIsInstance(html, str)
        self.assertIn('signals-chart', html)
        self.assertIn('Buy vs Sell', html)
    
    def test_generate_html_report(self):
        """Test complete HTML report generation"""
        html = self.generator.generate_html_report(self.sample_report, [])
        
        self.assertIsInstance(html, str)
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Daily Trading Report', html)
        self.assertIn('2026-01-13', html)
        self.assertIn('$10,000.00', html)
        self.assertIn('AAPL', html)
    
    def test_generate_markdown_summary(self):
        """Test markdown summary generation"""
        md = self.generator.generate_markdown_summary(self.sample_report)
        
        self.assertIsInstance(md, str)
        self.assertIn('# Daily Trading Report', md)
        self.assertIn('2026-01-13', md)
        self.assertIn('## Account Summary', md)
        self.assertIn('## Symbol Analysis', md)
        self.assertIn('AAPL', md)
        self.assertIn('BUY', md)
    
    def test_save_html_report(self):
        """Test saving HTML report to file"""
        from unittest.mock import mock_open
        
        # Mock both the load_daily_reports method and file write
        with patch.object(self.generator, 'load_daily_reports', return_value=[]):
            with patch('builtins.open', mock_open()) as mock_file:
                path = self.generator.save_html_report(self.sample_report)
                
                self.assertIsInstance(path, str)
                self.assertIn('daily_report_', path)
                self.assertIn('.html', path)
                
                # Verify file was opened for writing (check that it was called)
                self.assertTrue(mock_file.called)


if __name__ == '__main__':
    unittest.main()

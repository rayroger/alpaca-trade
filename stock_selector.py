# stock_selector.py
"""
Dynamic stock selection module for the trading bot.
Selects stocks based on market cap, volume, sector diversity, and market movements.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import pytz
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame


class DynamicStockSelector:
    """Dynamically select stocks for trading based on various criteria"""
    
    # Major liquid stocks across different sectors
    STOCK_UNIVERSE = {
        'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO', 'ORCL', 'CRM'],
        'Financial': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'USB'],
        'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'DHR', 'BMY', 'LLY'],
        'Consumer': ['AMZN', 'TSLA', 'WMT', 'HD', 'NKE', 'MCD', 'SBUX', 'TGT', 'LOW', 'CVS'],
        'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL'],
        'Industrial': ['BA', 'CAT', 'GE', 'HON', 'UPS', 'RTX', 'LMT', 'MMM', 'DE', 'EMR'],
        'Communication': ['DIS', 'CMCSA', 'NFLX', 'T', 'VZ', 'TMUS', 'CHTR', 'EA', 'ATVI', 'TTWO'],
        'Materials': ['LIN', 'APD', 'ECL', 'SHW', 'DD', 'NEM', 'FCX', 'NUE', 'VMC', 'MLM']
    }
    
    def __init__(self, data_client: StockHistoricalDataClient):
        """
        Initialize the stock selector
        
        Args:
            data_client: Alpaca data client for fetching market data
        """
        self.data_client = data_client
        self.logger = logging.getLogger(__name__)
    
    def get_all_symbols(self) -> List[str]:
        """Get all symbols from the stock universe"""
        all_symbols = []
        for sector_stocks in self.STOCK_UNIVERSE.values():
            all_symbols.extend(sector_stocks)
        return list(set(all_symbols))  # Remove duplicates
    
    def get_high_volume_stocks(self, min_volume: int = 5000000, limit: int = 20) -> List[str]:
        """
        Select stocks with high trading volume
        
        Args:
            min_volume: Minimum average daily volume
            limit: Maximum number of stocks to return
            
        Returns:
            List of stock symbols with high volume
        """
        self.logger.info(f"Selecting high volume stocks (min volume: {min_volume:,})")
        
        symbols = self.get_all_symbols()
        high_volume_stocks = []
        
        try:
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=7)  # Last week
            
            for symbol in symbols:
                try:
                    request = StockBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=TimeFrame.Day,
                        start=start_date,
                        end=end_date,
                        feed='iex'
                    )
                    
                    bars = self.data_client.get_stock_bars(request)
                    
                    if symbol in bars.data:
                        volumes = [float(bar.volume) for bar in bars.data[symbol]]
                        avg_volume = sum(volumes) / len(volumes) if volumes else 0
                        
                        if avg_volume >= min_volume:
                            high_volume_stocks.append({
                                'symbol': symbol,
                                'avg_volume': avg_volume
                            })
                except Exception as e:
                    self.logger.debug(f"Could not fetch volume for {symbol}: {e}")
                    continue
            
            # Sort by volume and return top stocks
            high_volume_stocks.sort(key=lambda x: x['avg_volume'], reverse=True)
            selected = [s['symbol'] for s in high_volume_stocks[:limit]]
            
            self.logger.info(f"Selected {len(selected)} high volume stocks: {', '.join(selected)}")
            return selected
            
        except Exception as e:
            self.logger.error(f"Error selecting high volume stocks: {e}")
            return []
    
    def get_diversified_stocks(self, stocks_per_sector: int = 2, sectors: Optional[List[str]] = None) -> List[str]:
        """
        Select stocks diversified across sectors
        
        Args:
            stocks_per_sector: Number of stocks to select from each sector
            sectors: List of sectors to include (None = all sectors)
            
        Returns:
            List of diversified stock symbols
        """
        self.logger.info(f"Selecting diversified stocks ({stocks_per_sector} per sector)")
        
        if sectors is None:
            sectors = list(self.STOCK_UNIVERSE.keys())
        
        selected_stocks = []
        
        for sector in sectors:
            if sector in self.STOCK_UNIVERSE:
                sector_stocks = self.STOCK_UNIVERSE[sector][:stocks_per_sector]
                selected_stocks.extend(sector_stocks)
                self.logger.debug(f"Selected from {sector}: {', '.join(sector_stocks)}")
        
        self.logger.info(f"Selected {len(selected_stocks)} diversified stocks across {len(sectors)} sectors")
        return selected_stocks
    
    def get_top_movers(self, period_days: int = 1, limit: int = 10, direction: str = 'both') -> Dict[str, List[str]]:
        """
        Get top gaining and/or losing stocks
        
        Args:
            period_days: Number of days to look back
            limit: Number of top movers to return
            direction: 'gainers', 'losers', or 'both'
            
        Returns:
            Dictionary with 'gainers' and/or 'losers' keys containing stock symbols
        """
        self.logger.info(f"Finding top movers (period: {period_days} days, direction: {direction})")
        
        symbols = self.get_all_symbols()
        movers = []
        
        try:
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=period_days + 5)  # Extra days for data
            
            for symbol in symbols:
                try:
                    request = StockBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=TimeFrame.Day,
                        start=start_date,
                        end=end_date,
                        feed='iex'
                    )
                    
                    bars = self.data_client.get_stock_bars(request)
                    
                    if symbol in bars.data and len(bars.data[symbol]) > period_days:
                        bar_list = bars.data[symbol]
                        start_price = float(bar_list[-period_days - 1].close)
                        end_price = float(bar_list[-1].close)
                        
                        if start_price > 0:
                            pct_change = ((end_price - start_price) / start_price) * 100
                            movers.append({
                                'symbol': symbol,
                                'pct_change': pct_change,
                                'start_price': start_price,
                                'end_price': end_price
                            })
                except Exception as e:
                    self.logger.debug(f"Could not analyze {symbol}: {e}")
                    continue
            
            # Sort by percentage change
            movers.sort(key=lambda x: x['pct_change'], reverse=True)
            
            result = {}
            
            if direction in ['gainers', 'both']:
                gainers = [m['symbol'] for m in movers[:limit]]
                result['gainers'] = gainers
                self.logger.info(f"Top {len(gainers)} gainers: {', '.join(gainers)}")
            
            if direction in ['losers', 'both']:
                losers = [m['symbol'] for m in reversed(movers[-limit:])]
                result['losers'] = losers
                self.logger.info(f"Top {len(losers)} losers: {', '.join(losers)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error finding top movers: {e}")
            return {'gainers': [], 'losers': []}
    
    def select_stocks(
        self,
        method: str = 'diversified',
        limit: int = 10,
        **kwargs
    ) -> List[str]:
        """
        Select stocks using the specified method
        
        Args:
            method: Selection method - 'diversified', 'high_volume', 'top_gainers', 'top_losers', 'mixed'
            limit: Maximum number of stocks to return
            **kwargs: Additional arguments for specific methods
            
        Returns:
            List of selected stock symbols
        """
        self.logger.info(f"Selecting stocks using method: {method}")
        
        if method == 'diversified':
            stocks_per_sector = kwargs.get('stocks_per_sector', 2)
            sectors = kwargs.get('sectors', None)
            stocks = self.get_diversified_stocks(stocks_per_sector, sectors)
            
        elif method == 'high_volume':
            min_volume = kwargs.get('min_volume', 5000000)
            stocks = self.get_high_volume_stocks(min_volume, limit)
            
        elif method == 'top_gainers':
            period_days = kwargs.get('period_days', 1)
            movers = self.get_top_movers(period_days, limit, direction='gainers')
            stocks = movers.get('gainers', [])
            
        elif method == 'top_losers':
            period_days = kwargs.get('period_days', 1)
            movers = self.get_top_movers(period_days, limit, direction='losers')
            stocks = movers.get('losers', [])
            
        elif method == 'mixed':
            # Combine multiple selection methods
            diversified = self.get_diversified_stocks(1, None)[:limit//2]
            high_volume = self.get_high_volume_stocks(limit=limit//2)
            stocks = list(set(diversified + high_volume))[:limit]
            
        else:
            self.logger.warning(f"Unknown selection method: {method}, using diversified")
            stocks = self.get_diversified_stocks(2, None)
        
        # Ensure we don't exceed the limit
        stocks = stocks[:limit]
        
        self.logger.info(f"Selected {len(stocks)} stocks: {', '.join(stocks)}")
        return stocks
    
    def get_selection_info(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get information about the selected stocks
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary with selection statistics
        """
        # Count stocks by sector
        sector_counts = {}
        for sector, stocks in self.STOCK_UNIVERSE.items():
            count = sum(1 for s in symbols if s in stocks)
            if count > 0:
                sector_counts[sector] = count
        
        return {
            'total_stocks': len(symbols),
            'sectors_represented': len(sector_counts),
            'sector_distribution': sector_counts,
            'symbols': symbols
        }

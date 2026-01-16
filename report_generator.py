# report_generator.py
"""
Module for generating visual daily status reports from trading logs and data.
Creates HTML reports with tables and charts showing trading performance.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional


class DailyReportGenerator:
    """Generates visual daily status reports with tables and charts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reports_dir = Path("reports")
        
        # Ensure reports directory exists
        try:
            self.reports_dir.mkdir(exist_ok=True)
            self.logger.info(f"Reports directory initialized: {self.reports_dir.absolute()}")
        except Exception as e:
            self.logger.error(f"Failed to create reports directory: {str(e)}", exc_info=True)
            raise
    
    def load_daily_reports(self, days: int = 30) -> List[Dict[str, Any]]:
        """Load daily reports from the last N days"""
        reports = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y%m%d')
            report_file = f"daily_report_{date_str}.json"
            
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r') as f:
                        report = json.load(f)
                        reports.append(report)
                except Exception as e:
                    self.logger.warning(f"Could not load {report_file}: {e}")
        
        return reports
    
    def load_trading_logs(self, log_dir: str = "logs") -> pd.DataFrame:
        """Load and parse trading logs into a DataFrame"""
        log_path = Path(log_dir)
        if not log_path.exists():
            self.logger.warning(f"Log directory {log_dir} does not exist")
            return pd.DataFrame()
        
        log_data = []
        for log_file in sorted(log_path.glob("trading_*.log")):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        # Parse log lines for trading information
                        if " - INFO - " in line or " - WARNING - " in line or " - ERROR - " in line:
                            parts = line.split(" - ", 3)
                            if len(parts) >= 4:
                                timestamp_str = parts[0]
                                level = parts[2]
                                message = parts[3].strip()
                                
                                try:
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                except (ValueError, TypeError):
                                    continue
                                
                                log_data.append({
                                    'timestamp': timestamp,
                                    'level': level,
                                    'message': message,
                                    'file': log_file.name
                                })
            except Exception as e:
                self.logger.warning(f"Could not parse {log_file}: {e}")
        
        return pd.DataFrame(log_data)
    
    def generate_summary_table(self, reports: List[Dict[str, Any]]) -> str:
        """Generate HTML table summarizing recent trading activity"""
        if not reports:
            return "<p>No recent trading data available.</p>"
        
        # Create DataFrame from reports
        data = []
        for report in reports:
            data.append({
                'Date': report.get('date', 'Unknown'),
                'Equity': f"${report.get('account', {}).get('equity', 0):,.2f}",
                'Buying Power': f"${report.get('account', {}).get('buying_power', 0):,.2f}",
                'Symbols Analyzed': report.get('analysis', {}).get('symbols_analyzed', 0),
                'Signals': report.get('analysis', {}).get('signals_generated', 0),
                'Trades': report.get('summary', {}).get('trades_executed', 0)
            })
        
        df = pd.DataFrame(data)
        
        # Generate HTML table with styling
        html = """
        <style>
            .summary-table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-family: Arial, sans-serif;
            }
            .summary-table th {
                background-color: #2c3e50;
                color: white;
                padding: 12px;
                text-align: left;
                border: 1px solid #ddd;
            }
            .summary-table td {
                padding: 10px;
                border: 1px solid #ddd;
            }
            .summary-table tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .summary-table tr:hover {
                background-color: #e8f4f8;
            }
        </style>
        """
        
        html += df.to_html(classes='summary-table', index=False, escape=False)
        return html
    
    def generate_symbol_performance_table(self, report: Dict[str, Any]) -> str:
        """Generate HTML table showing performance by symbol"""
        symbols = report.get('symbols', [])
        if not symbols:
            return "<p>No symbol data available for today.</p>"
        
        # Create DataFrame
        df = pd.DataFrame(symbols)
        
        # Rename columns for display
        display_df = df[['symbol', 'action', 'buy_indicators', 'sell_indicators']].copy()
        display_df.columns = ['Symbol', 'Action', 'Buy Signals', 'Sell Signals']
        
        # Generate HTML table with styling
        html = """
        <style>
            .symbol-table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-family: Arial, sans-serif;
            }
            .symbol-table th {
                background-color: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
                border: 1px solid #ddd;
            }
            .symbol-table td {
                padding: 10px;
                border: 1px solid #ddd;
            }
            .symbol-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .symbol-table tr:hover {
                background-color: #e8f4f8;
            }
            .action-buy {
                color: #27ae60;
                font-weight: bold;
            }
            .action-sell {
                color: #e74c3c;
                font-weight: bold;
            }
            .action-hold {
                color: #7f8c8d;
            }
        </style>
        """
        
        # Add color coding for actions
        html_table = display_df.to_html(classes='symbol-table', index=False, escape=False)
        html_table = html_table.replace('>BUY<', ' class="action-buy">BUY<')
        html_table = html_table.replace('>SELL<', ' class="action-sell">SELL<')
        html_table = html_table.replace('>HOLD<', ' class="action-hold">HOLD<')
        
        html += html_table
        return html
    
    def generate_equity_chart_data(self, reports: List[Dict[str, Any]]) -> str:
        """Generate chart data for equity over time (simple text-based chart)"""
        if not reports:
            return "<p>No data available for chart.</p>"
        
        # Extract equity data
        dates = []
        equity_values = []
        
        for report in reversed(reports):  # Oldest first
            dates.append(report.get('date', 'Unknown'))
            equity = report.get('account', {}).get('equity', 0)
            equity_values.append(equity)
        
        if not equity_values:
            return "<p>No equity data available.</p>"
        
        # Generate simple ASCII chart
        max_equity = max(equity_values)
        min_equity = min(equity_values)
        range_equity = max_equity - min_equity if max_equity != min_equity else 1
        
        chart_html = """
        <style>
            .chart-container {
                background-color: #f9f9f9;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                font-family: monospace;
            }
            .chart-title {
                font-family: Arial, sans-serif;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #2c3e50;
            }
            .chart-bar {
                display: flex;
                align-items: center;
                margin: 5px 0;
            }
            .chart-label {
                width: 100px;
                text-align: right;
                padding-right: 10px;
                font-size: 12px;
            }
            .chart-value {
                background-color: #3498db;
                height: 20px;
                transition: width 0.3s ease;
            }
            .chart-text {
                margin-left: 10px;
                font-size: 12px;
            }
        </style>
        <div class="chart-container">
            <div class="chart-title">Account Equity Over Time</div>
        """
        
        for date, equity in zip(dates, equity_values):
            width_percent = ((equity - min_equity) / range_equity * 80) if range_equity > 0 else 50
            chart_html += f"""
            <div class="chart-bar">
                <div class="chart-label">{date}</div>
                <div class="chart-value" style="width: {width_percent}%;"></div>
                <div class="chart-text">${equity:,.2f}</div>
            </div>
            """
        
        chart_html += "</div>"
        return chart_html
    
    def generate_signals_chart(self, reports: List[Dict[str, Any]]) -> str:
        """Generate chart showing buy/sell signals over time"""
        if not reports:
            return "<p>No data available for signals chart.</p>"
        
        # Extract signal data
        dates = []
        buy_signals = []
        sell_signals = []
        
        for report in reversed(reports):  # Oldest first
            dates.append(report.get('date', 'Unknown'))
            buy_signals.append(report.get('analysis', {}).get('total_buy_signals', 0))
            sell_signals.append(report.get('analysis', {}).get('total_sell_signals', 0))
        
        max_signals = max(max(buy_signals) if buy_signals else 0, max(sell_signals) if sell_signals else 0)
        if max_signals == 0:
            max_signals = 1
        
        chart_html = """
        <style>
            .signals-chart {
                background-color: #f9f9f9;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }
            .signals-row {
                display: flex;
                align-items: center;
                margin: 8px 0;
            }
            .signals-label {
                width: 100px;
                text-align: right;
                padding-right: 10px;
                font-size: 12px;
                font-family: monospace;
            }
            .signals-bars {
                flex: 1;
                display: flex;
                gap: 5px;
            }
            .buy-bar {
                background-color: #27ae60;
                height: 20px;
                transition: width 0.3s ease;
            }
            .sell-bar {
                background-color: #e74c3c;
                height: 20px;
                transition: width 0.3s ease;
            }
            .signals-text {
                width: 150px;
                margin-left: 10px;
                font-size: 12px;
                font-family: monospace;
            }
        </style>
        <div class="signals-chart">
            <div class="chart-title">Buy vs Sell Signals Over Time</div>
        """
        
        for date, buy, sell in zip(dates, buy_signals, sell_signals):
            buy_width = (buy / max_signals * 35) if max_signals > 0 else 0
            sell_width = (sell / max_signals * 35) if max_signals > 0 else 0
            
            chart_html += f"""
            <div class="signals-row">
                <div class="signals-label">{date}</div>
                <div class="signals-bars">
                    <div class="buy-bar" style="width: {buy_width}%;"></div>
                    <div class="sell-bar" style="width: {sell_width}%;"></div>
                </div>
                <div class="signals-text">Buy: {buy} | Sell: {sell}</div>
            </div>
            """
        
        chart_html += "</div>"
        return chart_html
    
    def generate_html_report(self, report: Dict[str, Any], historical_reports: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate complete HTML report"""
        try:
            # Validate input - report must be a non-None dictionary
            if report is None:
                self.logger.error("Cannot generate HTML report: report is None")
                raise ValueError("Report data cannot be None")
            
            if not isinstance(report, dict):
                self.logger.error(f"Cannot generate HTML report: report must be a dictionary, got {type(report)}")
                raise ValueError("Report data must be a dictionary")
            
            if historical_reports is None:
                self.logger.debug("Loading historical reports for context")
                historical_reports = self.load_daily_reports(30)
            
            # Ensure current report is in the list (use set for deduplication by date)
            report_date = report.get('date')
            seen_dates = {report_date}
            all_reports = [report]
            
            for r in historical_reports:
                r_date = r.get('date')
                if r_date not in seen_dates:
                    all_reports.append(r)
                    seen_dates.add(r_date)
            
            # Sort and limit
            all_reports = sorted(all_reports, key=lambda x: x.get('date', ''), reverse=True)[:30]
            
            date = report.get('date', 'Unknown')
            timestamp = report.get('timestamp', 'Unknown')
            
            html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Trading Report - {date}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #ecf0f1;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                    border-bottom: 2px solid #bdc3c7;
                    padding-bottom: 5px;
                }}
                .header-info {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .stat-box {{
                    display: inline-block;
                    margin: 10px 20px 10px 0;
                }}
                .stat-label {{
                    font-weight: bold;
                    color: #7f8c8d;
                }}
                .stat-value {{
                    font-size: 18px;
                    color: #2c3e50;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Daily Trading Report</h1>
                
                <div class="header-info">
                    <div class="stat-box">
                        <span class="stat-label">Date:</span>
                        <span class="stat-value">{date}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Generated:</span>
                        <span class="stat-value">{timestamp}</span>
                    </div>
                </div>
                
                <h2>📈 Account Summary</h2>
                <div class="header-info">
                    <div class="stat-box">
                        <span class="stat-label">Equity:</span>
                        <span class="stat-value">${report.get('account', {}).get('equity', 0):,.2f}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Buying Power:</span>
                        <span class="stat-value">${report.get('account', {}).get('buying_power', 0):,.2f}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Cash:</span>
                        <span class="stat-value">${report.get('account', {}).get('cash', 0):,.2f}</span>
                    </div>
                </div>
                
                <h2>📊 Trading Activity</h2>
                <div class="header-info">
                    <div class="stat-box">
                        <span class="stat-label">Symbols Analyzed:</span>
                        <span class="stat-value">{report.get('analysis', {}).get('symbols_analyzed', 0)}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Signals Generated:</span>
                        <span class="stat-value">{report.get('analysis', {}).get('signals_generated', 0)}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Trades Executed:</span>
                        <span class="stat-value">{report.get('summary', {}).get('trades_executed', 0)}</span>
                    </div>
                </div>
                
                <h2>🎯 Today's Symbol Analysis</h2>
                {self.generate_symbol_performance_table(report)}
                
                <h2>📈 Equity History (Last 30 Days)</h2>
                {self.generate_equity_chart_data(all_reports)}
                
                <h2>🔔 Signals History (Last 30 Days)</h2>
                {self.generate_signals_chart(all_reports)}
                
                <h2>📋 Recent Trading History</h2>
                {self.generate_summary_table(all_reports[:10])}
                
                <div class="footer">
                    <p>Generated by Alpaca Daily Trading Bot</p>
                    <p>This is an automated report for paper trading analysis only.</p>
                </div>
            </div>
        </body>
        </html>
        """
            
            self.logger.info(f"Successfully generated HTML report for date: {report.get('date', 'Unknown')}")
            return html
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {str(e)}", exc_info=True)
            raise
    
    def save_html_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Generate and save HTML report to file"""
        try:
            # Validate input - report must be a non-None dictionary
            if report is None:
                self.logger.error("Cannot save HTML report: report is None")
                raise ValueError("Report data cannot be None")
            
            if not isinstance(report, dict):
                self.logger.error(f"Cannot save HTML report: report must be a dictionary, got {type(report)}")
                raise ValueError("Report data must be a dictionary")
            
            # Ensure reports directory exists
            if not self.reports_dir.exists():
                self.logger.warning(f"Reports directory {self.reports_dir} does not exist, creating it")
                self.reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            if filename is None:
                date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
                filename = f"daily_report_{date.replace('-', '')}.html"
            
            report_path = self.reports_dir / filename
            self.logger.debug(f"Saving HTML report to: {report_path}")
            
            # Generate HTML
            html = self.generate_html_report(report)
            
            # Save to file
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Verify file was created
            if not report_path.exists():
                self.logger.error(f"HTML report file was not created at {report_path}")
                raise IOError(f"Failed to create HTML report file at {report_path}")
            
            file_size = report_path.stat().st_size
            self.logger.info(f"HTML report saved successfully to {report_path} ({file_size} bytes)")
            return str(report_path)
        
        except Exception as e:
            self.logger.error(f"Failed to save HTML report: {str(e)}", exc_info=True)
            raise
    
    def generate_markdown_summary(self, report: Dict[str, Any]) -> str:
        """Generate a markdown summary for quick viewing"""
        date = report.get('date', 'Unknown')
        
        md = f"# Daily Trading Report - {date}\n\n"
        
        # Account Summary
        md += "## Account Summary\n\n"
        md += f"- **Equity**: ${report.get('account', {}).get('equity', 0):,.2f}\n"
        md += f"- **Buying Power**: ${report.get('account', {}).get('buying_power', 0):,.2f}\n"
        md += f"- **Cash**: ${report.get('account', {}).get('cash', 0):,.2f}\n\n"
        
        # Analysis Summary
        md += "## Trading Activity\n\n"
        md += f"- **Symbols Analyzed**: {report.get('analysis', {}).get('symbols_analyzed', 0)}\n"
        md += f"- **Buy Signals**: {report.get('analysis', {}).get('total_buy_signals', 0)}\n"
        md += f"- **Sell Signals**: {report.get('analysis', {}).get('total_sell_signals', 0)}\n"
        md += f"- **Signals Generated**: {report.get('analysis', {}).get('signals_generated', 0)}\n"
        md += f"- **Trades Executed**: {report.get('summary', {}).get('trades_executed', 0)}\n\n"
        
        # Symbol Details
        md += "## Symbol Analysis\n\n"
        md += "| Symbol | Action | Buy Indicators | Sell Indicators |\n"
        md += "|--------|--------|----------------|------------------|\n"
        
        for symbol in report.get('symbols', []):
            md += f"| {symbol['symbol']} | {symbol['action']} | {symbol['buy_indicators']} | {symbol['sell_indicators']} |\n"
        
        md += "\n"
        
        # Trades
        if report.get('trades'):
            md += "## Trades Executed\n\n"
            for trade in report.get('trades', []):
                md += f"- **{trade.get('action')}** {trade.get('shares', 0)} shares of {trade.get('symbol')} at ${trade.get('price', 0):.2f}\n"
        
        return md

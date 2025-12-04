"""
Configuration settings for the trading algorithm
All constants and parameters are defined here for easy modification
"""

# DATA CONFIGURATION
TICKER_FILE = 'data/qqq_holdings.txt'    # File containing stock symbols to analyze
INTERVAL = '1d'                      # Data interval: daily candles
LOOKBACK_PERIOD = '5y'               # Fetches 5 years of historical data
SMA_PERIOD = 20                      # 20-day moving average period

# POSITION SIZING CONFIGURATION
PORTFOLIO_SIZE = 10000               # Total portfolio value in dollars
MAX_POSITION_PCT = 0.10              # Maximum 10% of portfolio per stock
RISK_PER_TRADE_PCT = 0.02            # Risk 2% of portfolio per trade

# STOP-LOSS CONFIGURATION
STOP_LOSS_PCT = 0.05                 # Exit if price drops 5% below entry
USE_STOP_LOSS = True                 # Toggle stop-loss on/off for comparison

# OUTPUT CONFIGURATION
REPORTS_DIR = 'output/trade_reports'        # Directory for text reports
DASHBOARD_DIR = 'output/dashboard_data'     # Directory for JSON data files

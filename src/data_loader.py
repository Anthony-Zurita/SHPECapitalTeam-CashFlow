"""
Data loading functionality
Handles reading ticker files and fetching market data from Yahoo Finance
"""

import yfinance as yf
from .config import TICKER_FILE, LOOKBACK_PERIOD, INTERVAL


def load_tickers(filename=TICKER_FILE):
    """
    Reads stock ticker symbols from text file.
    File format: One ticker per line, lines starting with # are ignored
    
    Args:
        filename (str): Path to ticker file
        
    Returns:
        list: List of ticker symbols
    """
    tickers = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    tickers.append(line)
        print(f"✅ Loaded {len(tickers)} tickers from {filename}")
        return tickers
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found")
        return []


def fetch_stock_data(ticker, period=LOOKBACK_PERIOD, interval=INTERVAL):
    """
    Fetch historical stock price data using yfinance.
    
    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period to fetch (e.g., '1y', '5y')
        interval (str): Data interval (e.g., '1d', '1h')
        
    Returns:
        DataFrame: OHLCV data, or None if error occurs
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            print(f"⚠️  No data for {ticker}")
            return None
        return df
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None

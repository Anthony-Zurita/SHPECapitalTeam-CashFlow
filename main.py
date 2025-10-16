import yfinance as yf
import pandas as pd


# load all the tickers from a qqq_holdings.txt file

def load_qqq_tickers(filename='qqq_holdings.txt'):
    """Load QQQ ticker symbols from text file"""
    tickers = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                tickers.append(line)
    
    return tickers

# Get stock data
ticker = yf.Ticker("AAPL")
df = ticker.history(period="6mo")  # Get 6 months of data

# Calculate 50-day moving average
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# Simple trading signal
df['Signal'] = df['Close'] > df['SMA_50']  # True when price above MA

print(df.tail())

if __name__ == "__main__":
    tickers = load_qqq_tickers()
    print(f"Loaded {len(tickers)} QQQ holdings")
    print(f"Top 10: {tickers}")
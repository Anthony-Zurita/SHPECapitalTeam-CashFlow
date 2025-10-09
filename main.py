import yfinance as yf
import pandas as pd

# Get stock data
ticker = yf.Ticker("AAPL")
df = ticker.history(period="6mo")  # Get 6 months of data

# Calculate 50-day moving average
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# Simple trading signal
df['Signal'] = df['Close'] > df['SMA_50']  # True when price above MA

print(df.tail())
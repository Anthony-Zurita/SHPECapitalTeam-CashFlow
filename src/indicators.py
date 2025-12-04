"""
Technical indicator calculations
Currently implements Simple Moving Average (SMA)
"""

from .config import SMA_PERIOD


def calculate_sma(df, period=SMA_PERIOD):
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        df (DataFrame): Stock price data with 'Close' column
        period (int): Number of periods for SMA calculation
        
    Returns:
        DataFrame: Original dataframe with added 'SMA' column
    """
    df['SMA'] = df['Close'].rolling(window=period).mean()
    return df

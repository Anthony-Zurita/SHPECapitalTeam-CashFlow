"""
Signal generation and position sizing
Generates BUY/SELL/HOLD signals and calculates position sizes
"""

from datetime import datetime
from .config import PORTFOLIO_SIZE, MAX_POSITION_PCT, RISK_PER_TRADE_PCT, STOP_LOSS_PCT


def calculate_position_size(price, signal_strength, portfolio_size=PORTFOLIO_SIZE):
    """
    Calculate recommended position size based on:
    - Portfolio size
    - Maximum position percentage
    - Signal strength (distance from SMA)
    
    Args:
        price (float): Current stock price
        signal_strength (float): Distance from SMA in percentage
        portfolio_size (float): Total portfolio value
        
    Returns:
        dict: Position details including shares, dollars, stop-loss price
    """
    max_position_dollars = portfolio_size * MAX_POSITION_PCT
    risk_dollars = portfolio_size * RISK_PER_TRADE_PCT
    
    # Adjust position based on signal strength (stronger signal = larger position)
    # But never exceed max position
    if signal_strength > 5:
        position_multiplier = 1.0
    elif signal_strength > 2:
        position_multiplier = 0.75
    elif signal_strength > 0:
        position_multiplier = 0.5
    else:
        position_multiplier = 0.25
    
    position_dollars = min(max_position_dollars * position_multiplier, max_position_dollars)
    shares = int(position_dollars / price)
    actual_dollars = shares * price

    # Calculate stop-loss price
    stop_loss_price = price * (1 - STOP_LOSS_PCT)
    
    return {
        'shares': shares,
        'dollars': round(actual_dollars, 2),
        'position_pct': round((actual_dollars / portfolio_size) * 100, 2),
        'risk_dollars': round(risk_dollars, 2),
        'stop_loss_price': round(stop_loss_price, 2),
        'stop_loss_pct': STOP_LOSS_PCT * 100
    }


def generate_current_signal(df, ticker):
    """
    Generate trading signal for current market conditions.
    
    Args:
        df (DataFrame): Stock price data with SMA calculated
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Signal details including type, price, SMA, position sizing
    """
    current = df.iloc[-1]
    previous = df.iloc[-2]
    
    price = current['Close']
    sma = current['SMA']
    prev_price = previous['Close']
    prev_sma = previous['SMA']
    
    # Calculate distance from SMA
    distance_from_sma = ((price - sma) / sma) * 100
    
    # Detect crossovers
    crossed_above = (prev_price <= prev_sma) and (price > sma)
    crossed_below = (prev_price >= prev_sma) and (price < sma)
    
    # Generate signal
    if crossed_above:
        signal = 'STRONG BUY'
    elif price > sma:
        signal = 'BUY'
    elif crossed_below:
        signal = 'SELL'
    else:
        signal = 'HOLD'
    
    # Calculate position sizing for buy signals
    position = None
    if signal in ['STRONG BUY', 'BUY']:
        position = calculate_position_size(price, distance_from_sma)
    
    return {
        'ticker': ticker,
        'signal': signal,
        'price': round(price, 2),
        'sma': round(sma, 2),
        'distance_pct': round(distance_from_sma, 2),
        'crossed_above': bool(crossed_above),
        'crossed_below': bool(crossed_below),
        'position': position,
        'timestamp': datetime.now().isoformat()
    }

"""
Backtesting engine
Simulates historical trades based on SMA crossover strategy with stop-loss
"""

from .config import USE_STOP_LOSS, STOP_LOSS_PCT


def backtest_strategy(ticker, df):
    """
    Backtest SMA crossover strategy with stop-loss protection.
    
    Walks through historical data day-by-day, simulating trades:
    - BUY when price crosses above SMA
    - SELL when price crosses below SMA OR stop-loss triggered
    
    Args:
        ticker (str): Stock ticker symbol
        df (DataFrame): Historical price data with SMA calculated
        
    Returns:
        dict: Backtest results including all trades and performance metrics
    """
    if df is None or len(df) < 21:
        return None
    
    # Reset index to make datetime a column (matches original merp.py)
    df = df.reset_index()
    
    # Handle both 'Datetime' (intraday) and 'Date' (daily) column names
    if 'Date' in df.columns:
        df = df.rename(columns={'Date': 'Datetime'})
    
    trades = []
    in_position = False
    entry_price = 0
    entry_date = None
    stop_loss_price = 0
    
    # Track exits
    stop_loss_exits = 0
    signal_exits = 0
    
    for i in range(1, len(df)):
        current = df.iloc[i]
        previous = df.iloc[i-1]
        
        price = current['Close']
        low = current['Low']  # Use Low to check if stop-loss was hit intraday
        sma = current['SMA']
        prev_price = previous['Close']
        prev_sma = previous['SMA']
        date = current['Datetime']
        
        # Skip if SMA not yet calculated
        if pd.isna(sma) or pd.isna(prev_sma):
            continue
        
        # Check for entry signal (crossover above SMA)
        crossed_above = (prev_price <= prev_sma) and (price > sma)
        
        # Check for exit signal (crossover below SMA)
        crossed_below = (prev_price >= prev_sma) and (price < sma)
        
        # ENTRY LOGIC
        if not in_position and crossed_above:
            in_position = True
            entry_price = price
            entry_date = date
            stop_loss_price = entry_price * (1 - STOP_LOSS_PCT) if USE_STOP_LOSS else 0
        
        # EXIT LOGIC
        elif in_position:
            exit_triggered = False
            exit_reason = ''
            
            # Check stop-loss first (higher priority)
            # Use Low price to check if stop was hit intraday (more realistic)
            if USE_STOP_LOSS and low <= stop_loss_price:
                exit_triggered = True
                exit_reason = 'stop_loss'
                stop_loss_exits += 1
                # Exit at stop-loss price, not the low (we had a limit order)
                exit_price = stop_loss_price
            
            # Check signal-based exit
            elif crossed_below:
                exit_triggered = True
                exit_reason = 'signal'
                signal_exits += 1
                exit_price = price
            
            if exit_triggered:
                profit = exit_price - entry_price
                profit_pct = ((exit_price - entry_price) / entry_price) * 100
                
                trades.append({
                    'entry_date': entry_date.strftime('%Y-%m-%d') if hasattr(entry_date, 'strftime') else str(entry_date),
                    'entry_price': round(entry_price, 2),
                    'exit_date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date),
                    'exit_price': round(exit_price, 2),
                    'profit': round(profit, 2),
                    'profit_pct': round(profit_pct, 2),
                    'exit_reason': exit_reason
                })
                
                in_position = False
    
    # If still in position at end, close it at last price (matches original merp.py)
    if in_position:
        last = df.iloc[-1]
        exit_price = last['Close']
        profit = exit_price - entry_price
        profit_pct = ((exit_price - entry_price) / entry_price) * 100
        
        trades.append({
            'entry_date': entry_date.strftime('%Y-%m-%d') if hasattr(entry_date, 'strftime') else str(entry_date),
            'entry_price': round(entry_price, 2),
            'exit_date': last['Datetime'].strftime('%Y-%m-%d') if hasattr(last['Datetime'], 'strftime') else str(last['Datetime']),
            'exit_price': round(exit_price, 2),
            'profit': round(profit, 2),
            'profit_pct': round(profit_pct, 2),
            'exit_reason': 'END-OF-DATA'
        })
    
    # Calculate statistics
    if not trades:
        return {
            'ticker': ticker,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'gross_profit': 0,
            'gross_loss': 0,
            'total_profit': 0,
            'avg_profit': 0,
            'avg_profit_pct': 0,
            'stop_loss_exits': 0,
            'signal_exits': 0,
            'trades': []
        }
    
    winning_trades = [t for t in trades if t['profit'] > 0]
    losing_trades = [t for t in trades if t['profit'] <= 0]
    
    gross_profit = sum(t['profit'] for t in winning_trades)
    gross_loss = sum(t['profit'] for t in losing_trades)
    total_profit = gross_profit + gross_loss
    
    avg_profit = total_profit / len(trades) if trades else 0
    avg_profit_pct = sum(t['profit_pct'] for t in trades) / len(trades) if trades else 0
    
    return {
        'ticker': ticker,
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': round((len(winning_trades) / len(trades)) * 100, 2) if trades else 0,
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'total_profit': round(total_profit, 2),
        'avg_profit': round(avg_profit, 2),
        'avg_profit_pct': round(avg_profit_pct, 2),
        'stop_loss_exits': stop_loss_exits,
        'signal_exits': signal_exits,
        'trades': trades
    }


# Import pandas here to avoid circular imports
import pandas as pd

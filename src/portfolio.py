"""
Portfolio analysis and stock processing
Combines signal generation and backtesting for each stock
"""

from .data_loader import fetch_stock_data
from .indicators import calculate_sma
from .signals import generate_current_signal
from .backtester import backtest_strategy


def analyze_stock(ticker):
    """
    Complete analysis pipeline for a single stock:
    1. Fetch historical data
    2. Calculate SMA indicator
    3. Generate current trading signal
    4. Run backtest on historical data
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        tuple: (signal_dict, backtest_dict) or (None, None) if error
    """
    print(f"📊 Analyzing {ticker}...")
    
    # Fetch data
    df = fetch_stock_data(ticker)
    if df is None or len(df) < 25:
        return None, None
    
    # Calculate indicator
    df = calculate_sma(df)
    
    # Generate current signal
    signal = generate_current_signal(df, ticker)
    
    # Run backtest
    backtest = backtest_strategy(ticker, df)
    
    return signal, backtest


def calculate_portfolio_summary(backtest_results):
    """
    Aggregate all individual stock backtests into portfolio-level metrics.
    
    Args:
        backtest_results (list): List of backtest dictionaries from all stocks
        
    Returns:
        dict: Portfolio-wide performance statistics
    """
    # Filter out None results
    valid_results = [r for r in backtest_results if r is not None]
    
    if not valid_results:
        return {
            'total_stocks_analyzed': 0,
            'profitable_stocks': 0,
            'unprofitable_stocks': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'overall_win_rate': 0,
            'gross_profit': 0,
            'gross_loss': 0,
            'net_profit': 0,
            'avg_profit_pct_per_stock': 0,
            'profit_factor': 0,
            'best_performer': {'ticker': 'N/A', 'profit': 0, 'win_rate': 0},
            'worst_performer': {'ticker': 'N/A', 'profit': 0, 'win_rate': 0},
            'is_profitable': 'False',
            'stop_loss_exits': 0,
            'signal_exits': 0,
            'worst_trade_pct': 0,
            'stop_loss_pct': 0,
            'stop_loss_enabled': 'False'
        }
    
    # Calculate aggregates
    total_stocks = len(valid_results)
    profitable_stocks = len([r for r in valid_results if r['total_profit'] > 0])
    unprofitable_stocks = total_stocks - profitable_stocks
    
    total_trades = sum(r['total_trades'] for r in valid_results)
    winning_trades = sum(r['winning_trades'] for r in valid_results)
    losing_trades = sum(r['losing_trades'] for r in valid_results)
    
    gross_profit = sum(r['gross_profit'] for r in valid_results)
    gross_loss = sum(r['gross_loss'] for r in valid_results)
    net_profit = gross_profit + gross_loss
    
    overall_win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    avg_profit_pct = sum(r['avg_profit_pct'] for r in valid_results) / total_stocks
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
    
    # Find best and worst performers
    best = max(valid_results, key=lambda x: x['total_profit'])
    worst = min(valid_results, key=lambda x: x['total_profit'])
    
    # Stop-loss statistics
    stop_loss_exits = sum(r['stop_loss_exits'] for r in valid_results)
    signal_exits = sum(r['signal_exits'] for r in valid_results)
    
    # Find worst trade percentage (should be -5.0% if stop-loss working)
    all_trades = []
    for r in valid_results:
        all_trades.extend(r['trades'])
    worst_trade_pct = min([t['profit_pct'] for t in all_trades]) if all_trades else 0
    
    # Import config here to avoid circular imports
    from .config import STOP_LOSS_PCT, USE_STOP_LOSS
    
    return {
        'total_stocks_analyzed': total_stocks,
        'profitable_stocks': profitable_stocks,
        'unprofitable_stocks': unprofitable_stocks,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'overall_win_rate': round(overall_win_rate, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'net_profit': round(net_profit, 2),
        'avg_profit_pct_per_stock': round(avg_profit_pct, 2),
        'profit_factor': round(profit_factor, 2),
        'best_performer': {
            'ticker': best['ticker'],
            'profit': best['total_profit'],
            'win_rate': best['win_rate']
        },
        'worst_performer': {
            'ticker': worst['ticker'],
            'profit': worst['total_profit'],
            'win_rate': worst['win_rate']
        },
        'is_profitable': 'True' if net_profit > 0 else 'False',
        'stop_loss_exits': stop_loss_exits,
        'signal_exits': signal_exits,
        'worst_trade_pct': round(worst_trade_pct, 2),
        'stop_loss_pct': STOP_LOSS_PCT * 100,
        'stop_loss_enabled': USE_STOP_LOSS
    }


"""
What This Program Does
This is a stock screening and backtesting algorithm that analyzes 100+ stocks from the QQQ ETF (Nasdaq 100) to generate trading signals and test their historical performance. 
It uses a single technical indicator — the 20-day Simple Moving Average (SMA) — to decide when to buy and sell. When a stock's price crosses above its SMA, the algorithm generates 
a BUY signal; when price crosses below, it generates a SELL signal. The program serves two purposes: providing live recommendations for what to trade today, and backtesting 
to show whether this strategy would have made money over the past year.

How the Data Flows
The program starts by loading ticker symbols from a text file, then downloads one year of daily price data for each stock from Yahoo Finance. For each stock, it calculates 
the 20-day SMA by averaging the last 20 closing prices, creating a smoothed line that represents the stock's recent trend. The algorithm then runs two analyses: first, 
it checks today's data to generate a current signal (STRONG BUY, BUY, SELL, or HOLD) with position sizing recommendations; second, it loops through all historical data 
simulating trades — buying when price crosses above the SMA and selling when it crosses below — to calculate performance metrics like win rate, average profit, and total return.

How Backtesting Works
The backtesting engine walks through each day in history, tracking whether we're holding a position or not. When it detects a crossover above the SMA and we don't own 
the stock, it records a buy. When it detects a crossover below and we do own the stock, it records a sell and calculates the profit or loss. Each stock is backtested 
independently, meaning you can hold multiple stocks simultaneously (AAPL, GOOGL, and AMZN all at once), but you cannot buy more of a stock you already own. After 
processing all trades, the engine calculates statistics: win rate, average winner, average loser, gross profit, gross loss, and total profit for that stock.

How Results Are Combined
After all 100 stocks are analyzed individually, the portfolio summary function aggregates everything into one overall picture. It sums up all winning trades and losing 
trades across all stocks, calculates the total gross profit and gross loss, and determines the net profit. The profit factor (gross profit divided by gross loss) tells 
you how many dollars you earn for every dollar you lose — anything above 1.0 means the strategy is profitable. The summary also identifies the best performing stock 
(KLAC at +$318) and worst performing stock (BKNG at -$333), giving you a complete view of how the strategy performed as a whole.

What Gets Output
The program produces two outputs. First, a human-readable text report showing the portfolio summary, current trading signals with position sizing (how many shares 
to buy based on a $10,000 portfolio), and detailed backtest results for the top performers. Second, a JSON file containing all the same data in a structured format 
that your dashboard website can easily read and display. Both files are saved with timestamps, and the JSON is also saved as latest.json so your website always knows 
where to find the most recent data.

Current Limitations
The strategy is profitable but barely — with a profit factor of 1.04x, you're earning just $1.04 for every $1.00 lost. The 26.8% win rate means you 
lose most trades, but winners are significantly larger than losers, which is how trend-following strategies work. The main weakness is that losing trades can run 
too long before the SMA crossover triggers an exit. This is exactly what a stop-loss would fix: instead of waiting for the SMA signal, you'd automatically exit any 
trade that drops more than a set percentage (like 5%) from your entry price, cutting losers short and protecting your profits.


STOCK SCREENER WITH BACKTESTING
Educational project for analyzing stocks using technical indicators

Features:
- 20-period Simple Moving Average (SMA) on daily intervals
- STOP-LOSS protection (exits if trade drops below threshold)
- Full portfolio profit/loss tracking
- Position sizing recommendations
- JSON output for dashboard integration
- Live signals + historical backtesting

Signal Logic: 
- BUY when price crosses above SMA
- SELL when price crosses below SMA OR hits stop-loss

"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json


# ============================================================================
# CONFIGURATION
# ============================================================================

TICKER_FILE = 'qqq_holdings.txt'    # File containing stock symbols to analyze
INTERVAL = '1d'                     # Data interval: daily candles
LOOKBACK_PERIOD = '1y'              # Fetches 1 year of historical data
SMA_PERIOD = 20                     # 20-day moving average period
BACKTEST_DAYS = 100                  # Tests the strategy over x days

# POSITION SIZING CONFIG
PORTFOLIO_SIZE = 10000              # Total portfolio value in dollars
MAX_POSITION_PCT = 0.10             # Maximum 10% of portfolio per stock
RISK_PER_TRADE_PCT = 0.02           # Risk 2% of portfolio per trade

# STOP-LOSS CONFIG
STOP_LOSS_PCT = 0.05                # Exit if price drops 5% below entry
USE_STOP_LOSS = True                # Toggle stop-loss on/off for comparison


# ============================================================================
# DATA LOADING
# ============================================================================

def load_tickers(filename=TICKER_FILE):
    """
    Reads stock ticker symbols from text file.
    File format: One ticker per line, lines starting with # are ignored
    """
    tickers = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    tickers.append(line)
        print(f"✅ Loaded {len(tickers)} tickers from {filename}\n")
        return tickers
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found!")
        return []


def fetch_stock_data(ticker, period=LOOKBACK_PERIOD, interval=INTERVAL):
    """
    Fetch historical stock price data using yfinance.
    Returns: DataFrame with OHLCV (open, high, low, close, volume) data, or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval, prepost=True)
        
        if df.empty or len(df) < SMA_PERIOD:
            return None
            
        return df
    except Exception as e:
        print(f"⚠️ Error fetching {ticker}: {str(e)[:50]}")
        return None


# ============================================================================
# INDICATOR CALCULATION
# ============================================================================

def calculate_sma(df, period=SMA_PERIOD):
    """
    Calculate Simple Moving Average (SMA).
    """
    df['SMA'] = df['Close'].rolling(window=period).mean()
    return df


# ============================================================================
# POSITION SIZING
# ============================================================================

def calculate_position_size(price, signal_strength, portfolio_size=PORTFOLIO_SIZE):
    """
    Calculate recommended position size based on:
    - Portfolio size
    - Maximum position percentage
    - Signal strength (distance from SMA)
    
    Returns: Dictionary with shares to buy and dollar amount
    """
    max_position_dollars = portfolio_size * MAX_POSITION_PCT
    risk_dollars = portfolio_size * RISK_PER_TRADE_PCT
    
    # Adjust position based on signal strength (stronger signal = larger position)
    # But never exceed max position
    if signal_strength > 5:  # Very strong signal (>5% above SMA)
        position_multiplier = 1.0
    elif signal_strength > 2:  # Strong signal
        position_multiplier = 0.75
    elif signal_strength > 0:  # Moderate signal
        position_multiplier = 0.5
    else:  # Weak/no signal
        position_multiplier = 0.25
    
    position_dollars = min(max_position_dollars * position_multiplier, max_position_dollars)
    shares = int(position_dollars / price)
    actual_dollars = shares * price

    # calculate stop-loss price
    stop_loss_price = price * (1 - STOP_LOSS_PCT)
    
    return {
        'shares': shares,
        'dollars': round(actual_dollars, 2),
        'position_pct': round((actual_dollars / portfolio_size) * 100, 2),
        'risk_dollars': round(risk_dollars, 2),
        'stop_loss_price': round(stop_loss_price, 2),
        'stop_loss_pct': STOP_LOSS_PCT * 100
    }


# ============================================================================
# LIVE SIGNAL GENERATION
# ============================================================================

def generate_current_signal(df, ticker):
    """
    Generate trading signal for current market conditions.
    Returns: Dictionary with current signal, metrics, and position sizing
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
        'crossed_above': crossed_above,
        'crossed_below': crossed_below,
        'position': position,
        'timestamp': datetime.now().isoformat()
    }


# ============================================================================
# BACKTESTING ENGINE
# ============================================================================

def backtest_strategy(ticker, df):
    """
    Backtest the SMA crossover strategy on historical data.
    
    Strategy:
    - BUY when price crosses above SMA
    - SELL when:
        1. Price crosses below SMA (trend reversal), OR
        2. Price drops below stop-loss threshold (risk management)
    - Track all trades and calculate performance
    
    Returns: Dictionary with backtest results
    """
    if df is None or len(df) < SMA_PERIOD + 1:
        return None
    
    # Reset index to make datetime a column
    df = df.reset_index()
    
    # Handle both 'Datetime' (intraday) and 'Date' (daily) column names
    if 'Date' in df.columns:
        df = df.rename(columns={'Date': 'Datetime'})
    
    trades = []
    position = None
    
    # Track stop-loss statistics
    stop_loss_exits = 0
    signal_exits = 0
    
    # Loop through data looking for crossovers and stop-loss triggers
    for i in range(1, len(df)):
        current = df.iloc[i]
        previous = df.iloc[i-1]
        
        current_price = current['Close']
        current_low = current['Low']  # Use Low to check if stop-loss was hit
        current_sma = current['SMA']
        prev_price = previous['Close']
        prev_sma = previous['SMA']
        
        # Skip if SMA not yet calculated
        if pd.isna(current_sma) or pd.isna(prev_sma):
            continue
        
        # ================================================================
        # CHECK FOR EXIT SIGNALS (if we have a position)
        # ================================================================
        if position is not None:
            
            # Calculate stop-loss price for this position
            stop_loss_price = position['entry_price'] * (1 - STOP_LOSS_PCT)
            
            # EXIT CONDITION 1: Stop-loss triggered
            # Check if the Low price hit our stop-loss (more realistic)
            if USE_STOP_LOSS and current_low <= stop_loss_price:
                # Exit at the stop-loss price (not the low - we had a limit order)
                exit_price = stop_loss_price
                exit_reason = 'STOP-LOSS'
                stop_loss_exits += 1
                
                profit_loss = exit_price - position['entry_price']
                profit_loss_pct = (profit_loss / position['entry_price']) * 100
                
                trade = {
                    'entry_date': position['entry_date'],
                    'entry_price': position['entry_price'],
                    'exit_date': current['Datetime'],
                    'exit_price': exit_price,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'duration': current['Datetime'] - position['entry_date'],
                    'exit_reason': exit_reason
                }
                trades.append(trade)
                position = None
                continue  # Move to next day, don't check other conditions
            
            # EXIT CONDITION 2: SMA crossover below (original logic)
            elif prev_price >= prev_sma and current_price < current_sma:
                exit_price = current_price
                exit_reason = 'SMA-CROSS'
                signal_exits += 1
                
                profit_loss = exit_price - position['entry_price']
                profit_loss_pct = (profit_loss / position['entry_price']) * 100
                
                trade = {
                    'entry_date': position['entry_date'],
                    'entry_price': position['entry_price'],
                    'exit_date': current['Datetime'],
                    'exit_price': exit_price,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'duration': current['Datetime'] - position['entry_date'],
                    'exit_reason': exit_reason
                }
                trades.append(trade)
                position = None
                continue
        
        # ================================================================
        # CHECK FOR ENTRY SIGNALS (if we don't have a position)
        # ================================================================
        if position is None:
            # ENTRY: Price crosses above SMA
            if prev_price <= prev_sma and current_price > current_sma:
                position = {
                    'entry_date': current['Datetime'],
                    'entry_price': current_price,
                    'entry_sma': current_sma
                }
    
    # If still in position at end, close it at last price
    if position is not None:
        last = df.iloc[-1]
        exit_price = last['Close']
        profit_loss = exit_price - position['entry_price']
        profit_loss_pct = (profit_loss / position['entry_price']) * 100
        
        trade = {
            'entry_date': position['entry_date'],
            'entry_price': position['entry_price'],
            'exit_date': last['Datetime'],
            'exit_price': exit_price,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'duration': last['Datetime'] - position['entry_date'],
            'exit_reason': 'END-OF-DATA'
        }
        trades.append(trade)
    
    # Calculate statistics
    if len(trades) == 0:
        return None
    
    winning_trades = [t for t in trades if t['profit_loss'] > 0]
    losing_trades = [t for t in trades if t['profit_loss'] < 0]
    
    total_trades = len(trades)
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    
    total_profit = sum(t['profit_loss'] for t in trades)
    total_profit_pct = sum(t['profit_loss_pct'] for t in trades)
    avg_profit_pct = total_profit_pct / total_trades
    
    avg_winner = sum(t['profit_loss_pct'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loser = sum(t['profit_loss_pct'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    # Calculate gross profit and gross loss
    gross_profit = sum(t['profit_loss'] for t in winning_trades)
    gross_loss = sum(t['profit_loss'] for t in losing_trades)
    
    # Calculate max loss (worst single trade)
    max_loss_pct = min(t['profit_loss_pct'] for t in trades) if trades else 0
    
    return {
        'ticker': ticker,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': round(win_rate, 2),
        'total_profit': round(total_profit, 2),
        'total_profit_pct': round(total_profit_pct, 2),
        'avg_profit_pct': round(avg_profit_pct, 2),
        'avg_winner_pct': round(avg_winner, 2),
        'avg_loser_pct': round(avg_loser, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'max_loss_pct': round(max_loss_pct, 2),
        'stop_loss_exits': stop_loss_exits,
        'signal_exits': signal_exits,
        'trades': trades
    }


# ============================================================================
# STOCK ANALYSIS
# ============================================================================

def analyze_stock(ticker):
    """
    Analyze a single stock: fetch data, calculate indicators, generate signal.
    """
    df = fetch_stock_data(ticker)
    if df is None:
        return None, None
    
    # Calculate indicators
    df = calculate_sma(df)
    
    # Generate current signal with position sizing
    signal = generate_current_signal(df, ticker)
    
    # Run backtest
    backtest_result = backtest_strategy(ticker, df)
    
    return signal, backtest_result


# ============================================================================
# PORTFOLIO SUMMARY
# ============================================================================

def calculate_portfolio_summary(backtest_results):
    """
    Calculate overall portfolio performance from all backtests.
    
    Returns: Dictionary with portfolio-level metrics
    """
    valid_backtests = [b for b in backtest_results if b is not None]
    
    if not valid_backtests:
        return None
    
    # Aggregate metrics
    total_trades = sum(b['total_trades'] for b in valid_backtests)
    total_wins = sum(b['winning_trades'] for b in valid_backtests)
    total_losses = sum(b['losing_trades'] for b in valid_backtests)
    
    # Dollar-based metrics (per share)
    gross_profit = sum(b['gross_profit'] for b in valid_backtests)
    gross_loss = sum(b['gross_loss'] for b in valid_backtests)
    net_profit = gross_profit + gross_loss
    
    # Percentage-based metrics
    total_profit_pct = sum(b['total_profit_pct'] for b in valid_backtests)
    avg_profit_pct = total_profit_pct / len(valid_backtests)
    
    # Win rate
    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    # Profitable vs unprofitable stocks
    profitable_stocks = [b for b in valid_backtests if b['total_profit'] > 0]
    unprofitable_stocks = [b for b in valid_backtests if b['total_profit'] <= 0]
    
    # Best and worst performers
    sorted_by_profit = sorted(valid_backtests, key=lambda x: x['total_profit'], reverse=True)
    best_stock = sorted_by_profit[0] if sorted_by_profit else None
    worst_stock = sorted_by_profit[-1] if sorted_by_profit else None
    
    # Profit factor
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
    
    # Stop-loss statistics
    total_stop_loss_exits = sum(b['stop_loss_exits'] for b in valid_backtests)
    total_signal_exits = sum(b['signal_exits'] for b in valid_backtests)
    
    # Worst single trade
    worst_trade_pct = min(b['max_loss_pct'] for b in valid_backtests)
    
    return {
        'total_stocks_analyzed': len(valid_backtests),
        'profitable_stocks': len(profitable_stocks),
        'unprofitable_stocks': len(unprofitable_stocks),
        'total_trades': total_trades,
        'winning_trades': total_wins,
        'losing_trades': total_losses,
        'overall_win_rate': round(overall_win_rate, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'net_profit': round(net_profit, 2),
        'avg_profit_pct_per_stock': round(avg_profit_pct, 2),
        'profit_factor': round(profit_factor, 2),
        'best_performer': {
            'ticker': best_stock['ticker'],
            'profit': best_stock['total_profit'],
            'win_rate': best_stock['win_rate']
        } if best_stock else None,
        'worst_performer': {
            'ticker': worst_stock['ticker'],
            'profit': worst_stock['total_profit'],
            'win_rate': worst_stock['win_rate']
        } if worst_stock else None,
        'is_profitable': net_profit > 0,
        # Stop-loss specific stats
        'stop_loss_exits': total_stop_loss_exits,
        'signal_exits': total_signal_exits,
        'worst_trade_pct': round(worst_trade_pct, 2),
        'stop_loss_pct': STOP_LOSS_PCT * 100,
        'stop_loss_enabled': USE_STOP_LOSS
    }


# ============================================================================
# JSON OUTPUT FOR DASHBOARD
# ============================================================================

def generate_dashboard_json(signals, backtest_results, portfolio_summary):
    """
    Generate JSON output for dashboard integration.
    """
    signals_json = []
    for s in signals:
        signal_copy = s.copy()
        signals_json.append(signal_copy)
    
    backtests_json = []
    for b in backtest_results:
        if b is None:
            continue
        backtest_copy = b.copy()
        trades_json = []
        for t in backtest_copy['trades']:
            trade_copy = {
                'entry_date': t['entry_date'].isoformat() if hasattr(t['entry_date'], 'isoformat') else str(t['entry_date']),
                'entry_price': round(t['entry_price'], 2),
                'exit_date': t['exit_date'].isoformat() if hasattr(t['exit_date'], 'isoformat') else str(t['exit_date']),
                'exit_price': round(t['exit_price'], 2),
                'profit_loss': round(t['profit_loss'], 2),
                'profit_loss_pct': round(t['profit_loss_pct'], 2),
                'duration_hours': round(t['duration'].total_seconds() / 3600, 1),
                'exit_reason': t.get('exit_reason', 'UNKNOWN')
            }
            trades_json.append(trade_copy)
        backtest_copy['trades'] = trades_json
        backtests_json.append(backtest_copy)
    
    dashboard_data = {
        'generated_at': datetime.now().isoformat(),
        'config': {
            'sma_period': SMA_PERIOD,
            'interval': INTERVAL,
            'lookback_period': LOOKBACK_PERIOD,
            'portfolio_size': PORTFOLIO_SIZE,
            'max_position_pct': MAX_POSITION_PCT,
            'risk_per_trade_pct': RISK_PER_TRADE_PCT,
            'stop_loss_pct': STOP_LOSS_PCT,
            'stop_loss_enabled': USE_STOP_LOSS
        },
        'portfolio_summary': portfolio_summary,
        'signals': signals_json,
        'backtests': backtests_json
    }
    
    return dashboard_data


def save_dashboard_json(dashboard_data):
    """
    Save dashboard data to JSON file.
    """
    if not os.path.exists('dashboard_data'):
        os.makedirs('dashboard_data')
    
    filename = f"dashboard_data/dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, default=str)
    
    with open('dashboard_data/latest.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, default=str)
    
    return filename


# ============================================================================
# RESULTS & REPORTING
# ============================================================================

def generate_report(signals, backtest_results, portfolio_summary):
    """
    Generate a formatted text report of all results.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = []
    report.append("=" * 80)
    report.append("STOCK SCREENING & BACKTEST REPORT v3.0 (WITH STOP-LOSS)")
    report.append(f"Generated: {timestamp}")
    report.append(f"Strategy: {SMA_PERIOD}-period SMA Crossover on {INTERVAL} intervals")
    report.append(f"Stop-Loss: {STOP_LOSS_PCT*100:.0f}% {'(ENABLED)' if USE_STOP_LOSS else '(DISABLED)'}")
    report.append(f"Lookback Period: {LOOKBACK_PERIOD}")
    report.append(f"Portfolio Size: ${PORTFOLIO_SIZE:,}")
    report.append("=" * 80)
    report.append("")
    
    # =========================================================================
    # PORTFOLIO SUMMARY
    # =========================================================================
    if portfolio_summary:
        report.append("💰 PORTFOLIO SUMMARY")
        report.append("=" * 80)
        report.append("")
        
        if portfolio_summary['is_profitable']:
            report.append("📈 STATUS: PROFITABLE ✅")
        else:
            report.append("📉 STATUS: UNPROFITABLE ❌")
        report.append("")
        
        report.append(f"  Gross Profit:    ${portfolio_summary['gross_profit']:>+10,.2f}")
        report.append(f"  Gross Loss:      ${portfolio_summary['gross_loss']:>+10,.2f}")
        report.append(f"  ─────────────────────────────")
        report.append(f"  NET PROFIT/LOSS: ${portfolio_summary['net_profit']:>+10,.2f}")
        report.append("")
        report.append(f"  Profit Factor:   {portfolio_summary['profit_factor']:.2f}x")
        report.append(f"  (Profit Factor > 1.0 means profitable)")
        report.append("")
        
        report.append("  TRADE STATISTICS:")
        report.append(f"    Total Trades:      {portfolio_summary['total_trades']}")
        report.append(f"    Winning Trades:    {portfolio_summary['winning_trades']}")
        report.append(f"    Losing Trades:     {portfolio_summary['losing_trades']}")
        report.append(f"    Overall Win Rate:  {portfolio_summary['overall_win_rate']:.1f}%")
        report.append("")
        
        # Stop-loss specific stats
        report.append("  🛡️ STOP-LOSS STATISTICS:")
        report.append(f"    Stop-Loss Setting: {portfolio_summary['stop_loss_pct']:.0f}%")
        report.append(f"    Stop-Loss Exits:   {portfolio_summary['stop_loss_exits']}")
        report.append(f"    Signal Exits:      {portfolio_summary['signal_exits']}")
        report.append(f"    Worst Trade:       {portfolio_summary['worst_trade_pct']:.2f}%")
        report.append("")
        
        report.append("  STOCK PERFORMANCE:")
        report.append(f"    Stocks Analyzed:   {portfolio_summary['total_stocks_analyzed']}")
        report.append(f"    Profitable:        {portfolio_summary['profitable_stocks']}")
        report.append(f"    Unprofitable:      {portfolio_summary['unprofitable_stocks']}")
        report.append("")
        
        if portfolio_summary['best_performer']:
            bp = portfolio_summary['best_performer']
            report.append(f"  🏆 Best:  {bp['ticker']} (${bp['profit']:+.2f}, {bp['win_rate']:.0f}% WR)")
        if portfolio_summary['worst_performer']:
            wp = portfolio_summary['worst_performer']
            report.append(f"  💀 Worst: {wp['ticker']} (${wp['profit']:+.2f}, {wp['win_rate']:.0f}% WR)")
        
        report.append("")
        report.append("=" * 80)
        report.append("")
    
    # =========================================================================
    # CURRENT SIGNALS
    # =========================================================================
    strong_buys = [s for s in signals if s['signal'] == 'STRONG BUY']
    buys = [s for s in signals if s['signal'] == 'BUY']
    sells = [s for s in signals if s['signal'] == 'SELL']
    holds = [s for s in signals if s['signal'] == 'HOLD']
    
    report.append("📊 CURRENT MARKET SIGNALS")
    report.append("-" * 80)
    report.append(f"Strong Buys (just crossed above SMA): {len(strong_buys)}")
    report.append(f"Buys (above SMA):                     {len(buys)}")
    report.append(f"Sells (just crossed below SMA):       {len(sells)}")
    report.append(f"Holds (below SMA):                    {len(holds)}")
    report.append(f"Total Analyzed:                       {len(signals)}")
    report.append("")
    
    # =========================================================================
    # STRONG BUY SIGNALS WITH POSITION SIZING
    # =========================================================================
    if strong_buys:
        report.append("")
        report.append("🔥 STRONG BUY SIGNALS (Just Crossed Above SMA)")
        report.append("=" * 80)
        for s in sorted(strong_buys, key=lambda x: x['distance_pct'], reverse=True):
            report.append(f"\n{s['ticker']}")
            report.append(f"  Price: ${s['price']:.2f} | SMA: ${s['sma']:.2f} | Distance: {s['distance_pct']:+.2f}%")
            
            if s['position']:
                p = s['position']
                report.append(f"  📦 POSITION SIZE: {p['shares']} shares (${p['dollars']:,.2f} = {p['position_pct']}% of portfolio)")
                report.append(f"  🛡️ STOP-LOSS: ${p['stop_loss_price']:.2f} (-{p['stop_loss_pct']:.0f}% from entry)")
            
            backtest = next((b for b in backtest_results if b and b['ticker'] == s['ticker']), None)
            if backtest:
                report.append(f"  📈 Backtest: {backtest['total_trades']} trades | "
                            f"Win Rate: {backtest['win_rate']:.1f}% | "
                            f"Avg P/L: {backtest['avg_profit_pct']:+.2f}%")
    
    # =========================================================================
    # BUY SIGNALS
    # =========================================================================
    if buys:
        report.append("")
        report.append("🟢 TOP 10 BUY SIGNALS (Above SMA)")
        report.append("=" * 80)
        for s in sorted(buys, key=lambda x: x['distance_pct'], reverse=True)[:10]:
            report.append(f"\n{s['ticker']}")
            report.append(f"  Price: ${s['price']:.2f} | SMA: ${s['sma']:.2f} | Distance: {s['distance_pct']:+.2f}%")
            
            if s['position']:
                p = s['position']
                report.append(f"  📦 POSITION SIZE: {p['shares']} shares (${p['dollars']:,.2f} = {p['position_pct']}% of portfolio)")
                report.append(f"  🛡️ STOP-LOSS: ${p['stop_loss_price']:.2f} (-{p['stop_loss_pct']:.0f}% from entry)")
            
            backtest = next((b for b in backtest_results if b and b['ticker'] == s['ticker']), None)
            if backtest:
                report.append(f"  📈 Backtest: {backtest['total_trades']} trades | "
                            f"Win Rate: {backtest['win_rate']:.1f}% | "
                            f"Avg P/L: {backtest['avg_profit_pct']:+.2f}%")
        
        if len(buys) > 10:
            report.append(f"\n  ... and {len(buys) - 10} more BUY signals")
    
    # =========================================================================
    # DETAILED BACKTEST RESULTS
    # =========================================================================
    valid_backtests = [b for b in backtest_results if b is not None]
    if valid_backtests:
        report.append("")
        report.append("")
        report.append("=" * 80)
        report.append("DETAILED BACKTEST RESULTS (Top 10 by Profit)")
        report.append("=" * 80)
        
        sorted_backtests = sorted(valid_backtests, key=lambda x: x['total_profit'], reverse=True)
        
        for bt in sorted_backtests[:10]:
            report.append(f"\n{bt['ticker']}")
            report.append("-" * 80)
            report.append(f"Total Trades: {bt['total_trades']} (Stop-Loss: {bt['stop_loss_exits']} | Signal: {bt['signal_exits']})")
            report.append(f"Wins: {bt['winning_trades']} | Losses: {bt['losing_trades']} | Win Rate: {bt['win_rate']:.1f}%")
            report.append(f"Avg Profit/Loss: {bt['avg_profit_pct']:+.2f}%")
            report.append(f"Avg Winner: {bt['avg_winner_pct']:+.2f}% | Avg Loser: {bt['avg_loser_pct']:+.2f}%")
            report.append(f"Max Loss: {bt['max_loss_pct']:.2f}% | Total Profit: ${bt['total_profit']:+.2f}")
    
    # =========================================================================
    # STRATEGY EXPLANATION
    # =========================================================================
    report.append("")
    report.append("=" * 80)
    report.append("STRATEGY EXPLANATION")
    report.append("-" * 80)
    report.append(f"Entry Signal: Price crosses above {SMA_PERIOD}-period SMA")
    report.append(f"Exit Signals:")
    report.append(f"  1. Price crosses below {SMA_PERIOD}-period SMA (trend reversal)")
    report.append(f"  2. Price drops {STOP_LOSS_PCT*100:.0f}% below entry (stop-loss protection)")
    report.append(f"Data: {INTERVAL} intervals")
    report.append("")
    report.append("SIGNAL TYPES:")
    report.append("  STRONG BUY: Stock just crossed above SMA (fresh entry signal)")
    report.append("  BUY: Stock is above SMA (in uptrend)")
    report.append("  SELL: Stock just crossed below SMA (exit signal)")
    report.append("  HOLD: Stock is below SMA (wait for entry)")
    report.append("")
    report.append("RISK MANAGEMENT:")
    report.append(f"  Portfolio Size: ${PORTFOLIO_SIZE:,}")
    report.append(f"  Max Position: {MAX_POSITION_PCT*100:.0f}% per stock (${PORTFOLIO_SIZE * MAX_POSITION_PCT:,.0f})")
    report.append(f"  Stop-Loss: {STOP_LOSS_PCT*100:.0f}% below entry price")
    report.append(f"  Risk Per Trade: {RISK_PER_TRADE_PCT*100:.0f}% of portfolio (${PORTFOLIO_SIZE * RISK_PER_TRADE_PCT:,.0f})")
    report.append("=" * 80)
    
    return "\n".join(report)


def save_report(report_text):
    """
    Save report to a text file in trade_reports directory.
    """
    if not os.path.exists('trade_reports'):
        os.makedirs('trade_reports')
    
    filename = f"trade_reports/screening_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return filename


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main program flow:
    1. Load ticker symbols
    2. Analyze each stock (current signal + backtest)
    3. Calculate portfolio summary
    4. Generate and save reports (text + JSON)
    """
    print("\n" + "=" * 80)
    print("STOCK SCREENER WITH BACKTESTING v3.0 (WITH STOP-LOSS)")
    print("=" * 80)
    print(f"Strategy: {SMA_PERIOD}-period SMA Crossover")
    print(f"Stop-Loss: {STOP_LOSS_PCT*100:.0f}% {'(ENABLED)' if USE_STOP_LOSS else '(DISABLED)'}")
    print(f"Interval: {INTERVAL}")
    print(f"Lookback: {LOOKBACK_PERIOD}")
    print(f"Portfolio: ${PORTFOLIO_SIZE:,}")
    print("=" * 80 + "\n")
    
    # Load tickers
    tickers = load_tickers()
    if not tickers:
        print("❌ No tickers to analyze. Exiting.")
        return
    
    # Analyze stocks
    print(f"Analyzing {len(tickers)} stocks...\n")
    signals = []
    backtest_results = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")
        
        signal, backtest = analyze_stock(ticker)
        
        if signal:
            signals.append(signal)
            backtest_results.append(backtest)
            
            status = f"✓ {signal['signal']}"
            if backtest:
                status += f" | {backtest['total_trades']} trades, {backtest['win_rate']:.0f}% WR"
                if backtest['stop_loss_exits'] > 0:
                    status += f" | {backtest['stop_loss_exits']} SL"
            if signal['position']:
                status += f" | Buy {signal['position']['shares']} shares"
            print(status)
        else:
            print("⚠ Insufficient data")
        
        time.sleep(0.25)
    
    print(f"\n✅ Analysis complete! {len(signals)} stocks analyzed.\n")
    
    # Calculate portfolio summary
    portfolio_summary = calculate_portfolio_summary(backtest_results)
    
    # Generate text report
    report_text = generate_report(signals, backtest_results, portfolio_summary)
    print(report_text)
    
    # Save text report
    report_filename = save_report(report_text)
    print(f"\n💾 Report saved to: {report_filename}")
    
    # Generate and save JSON for dashboard
    dashboard_data = generate_dashboard_json(signals, backtest_results, portfolio_summary)
    json_filename = save_dashboard_json(dashboard_data)
    print(f"📊 Dashboard JSON saved to: {json_filename}")
    print(f"📊 Latest dashboard data: dashboard_data/latest.json")
    
    print("\n" + "=" * 80)
    print("✅ Program complete!")
    print("=" * 80 + "\n")
    
    return dashboard_data


if __name__ == "__main__":
    main()

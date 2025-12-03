"""
STOCK SCREENER WITH BACKTESTING
Educational project for analyzing stocks using technical indicators

Current Indicator: 50-period Simple Moving Average (SMA) on 15-minute intervals
Signal Logic: BUY when price crosses above SMA, SELL when price crosses below SMA

Backtesting: Tests strategy over past 60 days using extended hours data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import os


# ============================================================================
# CONFIGURATION
# ============================================================================

TICKER_FILE = 'qqq_holdings.txt'    # File containing stock symbols to analyze
INTERVAL = '15m'                    # Data interval: 15-minute candles
LOOKBACK_PERIOD = '60d'             # Fetches x days of historical data
SMA_PERIOD = 50                     # Moving average period
BACKTEST_DAYS = 60                  # Tests the strategy over x days


# ============================================================================
# DATA LOADING
# ============================================================================

def load_tickers(filename=TICKER_FILE):
    """
    reads stock ticker symbols from text file, "qqq_holdings.txt"
    
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

    prepost=True, includes extended hours (pre-market and after-hours) data.
    
    Returns: DataFrame with OHLCV data, or None if error

    OHLCV stands for the five key pieces of information captured for each trading period (whether that's 1 minute, 15 minutes, 1 hour, or 1 day):
    The Five Components:

        O - Open: The price at which the stock first traded when that period began
        H - High: The highest price reached during that period
        L - Low: The lowest price reached during that period
        C - Close: The price at which the stock last traded when that period ended
        V - Volume: The total number of shares traded during that period

    Example for a 15-minute interval from 9:45 AM to 10:00 AM:

        Open:   $175.20  (first trade at 9:45 AM)
        High:   $176.50  (highest it reached during those 15 minutes)
        Low:    $174.80  (lowest it dipped during those 15 minutes)
        Close:  $176.10  (last trade at 10:00 AM)
        Volume: 250,000  (total shares traded in that 15-minute window)
    """

    try:
        stock = yf.Ticker(ticker)

        df = stock.history(period=period, interval=interval, prepost=True)
        
        # "df.empty" checks if there is no data returned from yfinance at all -> returns None
        # "len(df) < SMA_PERIOD" ensures there is enough data to calculate the SMA indicator
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
    
    The SMA smooths out price data by calculating the average price
    over a specified period. It's a lagging indicator that helps
    identify trend direction.
    """
    df['SMA'] = df['Close'].rolling(window=period).mean()
    return df


# ============================================================================
# LIVE SIGNAL GENERATION
# ============================================================================

def generate_current_signal(df):
    """
    Generate trading signal for current market conditions.
    
    Returns: Dictionary with current signal and metrics
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
        signal = 'STRONG BUY'  # Just crossed above
    elif price > sma:
        signal = 'BUY'  # Above SMA
    elif crossed_below:
        signal = 'SELL'  # Just crossed below
    else:
        signal = 'HOLD'  # Below SMA
    
    return {
        'signal': signal,
        'price': price,
        'sma': sma,
        'distance_pct': distance_from_sma,
        'crossed_above': crossed_above,
        'crossed_below': crossed_below
    }


# ============================================================================
# BACKTESTING ENGINE
# ============================================================================

def backtest_strategy(ticker, df):
    """
    Backtest the SMA crossover strategy on historical data.
    
    Strategy:
    - BUY when price crosses above SMA
    - SELL when price crosses below SMA
    - Track all trades and calculate performance
    
    Returns: Dictionary with backtest results
    """
    if df is None or len(df) < SMA_PERIOD + 1:
        return None
    
    # Reset index to make datetime a column
    df = df.reset_index()
    
    trades = []
    position = None  # Track if we're in a position
    
    # Loop through data looking for crossovers
    for i in range(1, len(df)):
        current = df.iloc[i]
        previous = df.iloc[i-1]
        
        current_price = current['Close']
        current_sma = current['SMA']
        prev_price = previous['Close']
        prev_sma = previous['SMA']
        
        # Skip if SMA not yet calculated
        if pd.isna(current_sma) or pd.isna(prev_sma):
            continue
        
        # Detect crossover above (BUY signal)
        if prev_price <= prev_sma and current_price > current_sma:
            if position is None:  # Only enter if not already in position
                position = {
                    'entry_date': current['Datetime'],
                    'entry_price': current_price,
                    'entry_sma': current_sma
                }
        
        # Detect crossover below (SELL signal)
        elif prev_price >= prev_sma and current_price < current_sma:
            if position is not None:  # Only exit if we have a position
                exit_price = current_price
                profit_loss = exit_price - position['entry_price']
                profit_loss_pct = (profit_loss / position['entry_price']) * 100
                
                trade = {
                    'entry_date': position['entry_date'],
                    'entry_price': position['entry_price'],
                    'exit_date': current['Datetime'],
                    'exit_price': exit_price,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'duration': current['Datetime'] - position['entry_date']
                }
                trades.append(trade)
                position = None  # Close the position
    
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
            'duration': last['Datetime'] - position['entry_date']
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
    avg_profit_pct = sum(t['profit_loss_pct'] for t in trades) / total_trades
    
    avg_winner = sum(t['profit_loss_pct'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loser = sum(t['profit_loss_pct'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    return {
        'ticker': ticker,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_profit_pct': avg_profit_pct,
        'avg_winner_pct': avg_winner,
        'avg_loser_pct': avg_loser,
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
    
    # Generate current signal
    signal = generate_current_signal(df)
    signal['ticker'] = ticker
    
    # Run backtest
    backtest_result = backtest_strategy(ticker, df)
    
    return signal, backtest_result


# ============================================================================
# RESULTS & REPORTING
# ============================================================================

def generate_report(signals, backtest_results):
    """
    Generate a formatted text report of all results.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = []
    report.append("=" * 80)
    report.append("STOCK SCREENING & BACKTEST REPORT")
    report.append(f"Generated: {timestamp}")
    report.append(f"Strategy: {SMA_PERIOD}-period SMA Crossover on {INTERVAL} intervals")
    report.append(f"Backtest Period: {BACKTEST_DAYS} days (includes extended hours)")
    report.append("=" * 80)
    report.append("")
    
    # Separate signals by type
    strong_buys = [s for s in signals if s['signal'] == 'STRONG BUY']
    buys = [s for s in signals if s['signal'] == 'BUY']
    sells = [s for s in signals if s['signal'] == 'SELL']
    holds = [s for s in signals if s['signal'] == 'HOLD']
    
    # Current signals summary
    report.append("📊 CURRENT MARKET SIGNALS")
    report.append("-" * 80)
    report.append(f"Strong Buys (just crossed above SMA): {len(strong_buys)}")
    report.append(f"Buys (above SMA):                     {len(buys)}")
    report.append(f"Sells (just crossed below SMA):       {len(sells)}")
    report.append(f"Holds (below SMA):                    {len(holds)}")
    report.append(f"Total Analyzed:                       {len(signals)}")
    report.append("")
    
    # Backtest summary
    valid_backtests = [b for b in backtest_results if b is not None]
    if valid_backtests:
        total_trades = sum(b['total_trades'] for b in valid_backtests)
        avg_win_rate = sum(b['win_rate'] for b in valid_backtests) / len(valid_backtests)
        profitable_stocks = len([b for b in valid_backtests if b['total_profit'] > 0])
        
        report.append("📈 BACKTEST SUMMARY")
        report.append("-" * 80)
        report.append(f"Stocks with Signals: {len(valid_backtests)}")
        report.append(f"Total Trades: {total_trades}")
        report.append(f"Average Win Rate: {avg_win_rate:.1f}%")
        report.append(f"Profitable Stocks: {profitable_stocks}/{len(valid_backtests)}")
        report.append("")
    
    # Strong Buy signals
    if strong_buys:
        report.append("")
        report.append("🔥 STRONG BUY SIGNALS (Just Crossed Above SMA)")
        report.append("=" * 80)
        for s in sorted(strong_buys, key=lambda x: x['distance_pct'], reverse=True):
            report.append(f"\n{s['ticker']}")
            report.append(f"  Price: ${s['price']:.2f} | SMA: ${s['sma']:.2f} | Distance: {s['distance_pct']:+.2f}%")
            
            # Add backtest info if available
            backtest = next((b for b in backtest_results if b and b['ticker'] == s['ticker']), None)
            if backtest:
                report.append(f"  Backtest: {backtest['total_trades']} trades | "
                            f"Win Rate: {backtest['win_rate']:.1f}% | "
                            f"Avg P/L: {backtest['avg_profit_pct']:+.2f}%")
    
    # Buy signals
    if buys:
        report.append("")
        report.append("🟢 BUY SIGNALS (Above SMA)")
        report.append("=" * 80)
        for s in sorted(buys, key=lambda x: x['distance_pct'], reverse=True)[:10]:  # Top 10
            report.append(f"\n{s['ticker']}")
            report.append(f"  Price: ${s['price']:.2f} | SMA: ${s['sma']:.2f} | Distance: {s['distance_pct']:+.2f}%")
            
            backtest = next((b for b in backtest_results if b and b['ticker'] == s['ticker']), None)
            if backtest:
                report.append(f"  Backtest: {backtest['total_trades']} trades | "
                            f"Win Rate: {backtest['win_rate']:.1f}% | "
                            f"Avg P/L: {backtest['avg_profit_pct']:+.2f}%")
        
        if len(buys) > 10:
            report.append(f"\n  ... and {len(buys) - 10} more BUY signals")
    
    # Detailed backtest results
    if valid_backtests:
        report.append("")
        report.append("")
        report.append("=" * 80)
        report.append("DETAILED BACKTEST RESULTS")
        report.append("=" * 80)
        
        # Sort by profitability
        sorted_backtests = sorted(valid_backtests, key=lambda x: x['total_profit'], reverse=True)
        
        for bt in sorted_backtests[:15]:  # Top 15 most profitable
            report.append(f"\n{bt['ticker']}")
            report.append("-" * 80)
            report.append(f"Total Trades: {bt['total_trades']}")
            report.append(f"Wins: {bt['winning_trades']} | Losses: {bt['losing_trades']} | Win Rate: {bt['win_rate']:.1f}%")
            report.append(f"Avg Profit/Loss: {bt['avg_profit_pct']:+.2f}%")
            report.append(f"Avg Winner: {bt['avg_winner_pct']:+.2f}% | Avg Loser: {bt['avg_loser_pct']:+.2f}%")
            report.append(f"Total Profit: ${bt['total_profit']:+.2f}")
            
            # Show individual trades
            report.append(f"\nTrades:")
            for i, trade in enumerate(bt['trades'][:5], 1):  # Show first 5 trades
                duration_hours = trade['duration'].total_seconds() / 3600
                report.append(f"  {i}. Entry: {trade['entry_date'].strftime('%m/%d %H:%M')} @ ${trade['entry_price']:.2f}")
                report.append(f"     Exit:  {trade['exit_date'].strftime('%m/%d %H:%M')} @ ${trade['exit_price']:.2f}")
                report.append(f"     P/L: ${trade['profit_loss']:+.2f} ({trade['profit_loss_pct']:+.2f}%) | Duration: {duration_hours:.1f}h")
            
            if len(bt['trades']) > 5:
                report.append(f"  ... and {len(bt['trades']) - 5} more trades")
    
    report.append("")
    report.append("=" * 80)
    report.append("STRATEGY EXPLANATION")
    report.append("-" * 80)
    report.append(f"Entry Signal: Price crosses above {SMA_PERIOD}-period SMA")
    report.append(f"Exit Signal: Price crosses below {SMA_PERIOD}-period SMA")
    report.append("Data: 15-minute intervals including extended hours (pre-market & after-hours)")
    report.append("")
    report.append("STRONG BUY: Stock just crossed above SMA (fresh signal)")
    report.append("BUY: Stock is above SMA (in uptrend)")
    report.append("SELL: Stock just crossed below SMA (exit signal)")
    report.append("HOLD: Stock is below SMA (in downtrend)")
    report.append("=" * 80)
    
    return "\n".join(report)


def save_report(report_text):
    """
    Save report to a text file in trade_reports directory.
    """
    # Create directory if it doesn't exist
    if not os.path.exists('trade_reports'):
        os.makedirs('trade_reports')
    
    # Generate filename with timestamp
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
    3. Generate and save report
    """
    print("\n" + "=" * 80)
    print("STOCK SCREENER WITH BACKTESTING")
    print("=" * 80)
    print(f"Strategy: {SMA_PERIOD}-period SMA Crossover")
    print(f"Interval: {INTERVAL}")
    print(f"Backtest: {BACKTEST_DAYS} days (extended hours included)")
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
                status += f" | Backtest: {backtest['total_trades']} trades, {backtest['win_rate']:.0f}% WR"
            print(status)
        else:
            print("⚠ Insufficient data")
        
        time.sleep(0.25)  # Be respectful to API
    
    print(f"\n✅ Analysis complete! {len(signals)} stocks analyzed.\n")
    
    # Generate report
    report_text = generate_report(signals, backtest_results)
    print(report_text)
    
    # Save report
    filename = save_report(report_text)
    print(f"\n💾 Report saved to: {filename}")
    print("\n" + "=" * 80)
    print("✅ Program complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
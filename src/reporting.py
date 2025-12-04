"""
Report generation and output formatting
Handles both text reports and JSON dashboard data
"""

import os
import json
from datetime import datetime
from .config import REPORTS_DIR, DASHBOARD_DIR, SMA_PERIOD, INTERVAL, LOOKBACK_PERIOD
from .config import PORTFOLIO_SIZE, MAX_POSITION_PCT, RISK_PER_TRADE_PCT
from .config import STOP_LOSS_PCT, USE_STOP_LOSS


def generate_report(signals, backtest_results, portfolio_summary):
    """
    Generate human-readable text report with all analysis results.
    
    Args:
        signals (list): List of current trading signals
        backtest_results (list): List of backtest results for all stocks
        portfolio_summary (dict): Portfolio-wide performance metrics
        
    Returns:
        str: Formatted text report
    """
    report = []
    report.append("=" * 80)
    report.append("SHPE CAPITAL - TEAM CASHFLOW")
    report.append("Stock Screening & Backtesting Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")
    
    # Strategy Configuration
    report.append("STRATEGY CONFIGURATION")
    report.append("-" * 80)
    report.append(f"Indicator: {SMA_PERIOD}-period Simple Moving Average")
    report.append(f"Interval: {INTERVAL} (Daily candles)")
    report.append(f"Lookback Period: {LOOKBACK_PERIOD}")
    report.append(f"Portfolio Size: ${PORTFOLIO_SIZE:,}")
    report.append(f"Max Position Size: {MAX_POSITION_PCT * 100}% (${PORTFOLIO_SIZE * MAX_POSITION_PCT:,.0f} per stock)")
    report.append(f"Risk Per Trade: {RISK_PER_TRADE_PCT * 100}% (${PORTFOLIO_SIZE * RISK_PER_TRADE_PCT:,.0f})")
    report.append(f"Stop-Loss: {'ENABLED' if USE_STOP_LOSS else 'DISABLED'} ({STOP_LOSS_PCT * 100}% threshold)")
    report.append("")
    
    # Portfolio Summary
    summary = portfolio_summary
    report.append("PORTFOLIO SUMMARY")
    report.append("=" * 80)
    report.append(f"Stocks Analyzed: {summary['total_stocks_analyzed']}")
    report.append(f"Profitable Stocks: {summary['profitable_stocks']} ({summary['profitable_stocks']/summary['total_stocks_analyzed']*100:.1f}%)")
    report.append(f"Unprofitable Stocks: {summary['unprofitable_stocks']}")
    report.append("")
    report.append(f"Total Trades Simulated: {summary['total_trades']:,}")
    report.append(f"Winning Trades: {summary['winning_trades']:,} ({summary['overall_win_rate']:.1f}%)")
    report.append(f"Losing Trades: {summary['losing_trades']:,}")
    report.append("")
    report.append(f"Gross Profit: ${summary['gross_profit']:,.2f}")
    report.append(f"Gross Loss: ${summary['gross_loss']:,.2f}")
    report.append(f"Net Profit: ${summary['net_profit']:,.2f}")
    report.append(f"Profit Factor: {summary['profit_factor']:.2f}x")
    report.append(f"Avg Profit % Per Stock: {summary['avg_profit_pct_per_stock']:.2f}%")
    report.append("")
    report.append(f"Best Performer: {summary['best_performer']['ticker']} (+${summary['best_performer']['profit']:,.2f}, {summary['best_performer']['win_rate']:.1f}% win rate)")
    report.append(f"Worst Performer: {summary['worst_performer']['ticker']} (${summary['worst_performer']['profit']:,.2f}, {summary['worst_performer']['win_rate']:.1f}% win rate)")
    report.append("")
    report.append(f"Stop-Loss Exits: {summary['stop_loss_exits']:,} ({summary['stop_loss_exits']/summary['total_trades']*100:.1f}%)")
    report.append(f"Signal Exits: {summary['signal_exits']:,} ({summary['signal_exits']/summary['total_trades']*100:.1f}%)")
    report.append(f"Worst Single Trade: {summary['worst_trade_pct']:.2f}%")
    report.append("")
    
    # Current Trading Signals
    report.append("=" * 80)
    report.append("CURRENT TRADING SIGNALS")
    report.append("=" * 80)
    
    # Separate by signal type
    strong_buy = [s for s in signals if s and s['signal'] == 'STRONG BUY']
    buy = [s for s in signals if s and s['signal'] == 'BUY']
    sell = [s for s in signals if s and s['signal'] == 'SELL']
    hold = [s for s in signals if s and s['signal'] == 'HOLD']
    
    report.append(f"\n🟢 STRONG BUY Signals: {len(strong_buy)}")
    report.append("-" * 80)
    for sig in strong_buy[:10]:  # Top 10
        report.append(f"{sig['ticker']:6s} | Price: ${sig['price']:8.2f} | SMA: ${sig['sma']:8.2f} | Distance: {sig['distance_pct']:6.2f}%")
        if sig['position']:
            pos = sig['position']
            report.append(f"        → BUY {pos['shares']} shares = ${pos['dollars']:,.2f} | Stop-Loss: ${pos['stop_loss_price']:.2f}")
    
    report.append(f"\n🟢 BUY Signals: {len(buy)}")
    report.append("-" * 80)
    for sig in buy[:10]:
        report.append(f"{sig['ticker']:6s} | Price: ${sig['price']:8.2f} | SMA: ${sig['sma']:8.2f} | Distance: {sig['distance_pct']:6.2f}%")
        if sig['position']:
            pos = sig['position']
            report.append(f"        → BUY {pos['shares']} shares = ${pos['dollars']:,.2f} | Stop-Loss: ${pos['stop_loss_price']:.2f}")
    
    report.append(f"\n🔴 SELL Signals: {len(sell)}")
    report.append("-" * 80)
    for sig in sell[:10]:
        report.append(f"{sig['ticker']:6s} | Price: ${sig['price']:8.2f} | SMA: ${sig['sma']:8.2f} | Distance: {sig['distance_pct']:6.2f}%")
    
    # Top Backtest Performers
    report.append("")
    report.append("=" * 80)
    report.append("TOP 15 BACKTEST PERFORMERS")
    report.append("=" * 80)
    report.append(f"{'Ticker':<8} {'Profit':<12} {'Trades':<8} {'Win%':<8} {'Avg%':<10} {'PF':<6}")
    report.append("-" * 80)
    
    sorted_results = sorted([r for r in backtest_results if r], key=lambda x: x['total_profit'], reverse=True)
    for result in sorted_results[:15]:
        pf = abs(result['gross_profit'] / result['gross_loss']) if result['gross_loss'] != 0 else float('inf')
        pf_str = f"{pf:.2f}x" if pf != float('inf') else "∞"
        report.append(f"{result['ticker']:<8} ${result['total_profit']:<11.2f} {result['total_trades']:<8} "
                     f"{result['win_rate']:<7.1f}% {result['avg_profit_pct']:<9.2f}% {pf_str:<6}")
    
    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


def save_report(report_text):
    """
    Save text report to file with timestamp.
    
    Args:
        report_text (str): The generated report text
        
    Returns:
        str: Path to saved file
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"screening_report_{timestamp}.txt"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\n📄 Report saved: {filepath}")
    return filepath


def generate_dashboard_json(signals, backtest_results, portfolio_summary):
    """
    Generate JSON data structure for web dashboard.
    
    Args:
        signals (list): Current trading signals
        backtest_results (list): Backtest results for all stocks
        portfolio_summary (dict): Portfolio performance metrics
        
    Returns:
        dict: JSON-serializable data structure
    """
    return {
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
        'signals': [s for s in signals if s is not None],
        'backtests': [b for b in backtest_results if b is not None]
    }


def save_dashboard_json(dashboard_data):
    """
    Save dashboard JSON to timestamped file and latest.json.
    
    Args:
        dashboard_data (dict): Dashboard data structure
        
    Returns:
        tuple: (timestamped_path, latest_path)
    """
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    
    # Save timestamped version
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    timestamped_file = f"dashboard_{timestamp}.json"
    timestamped_path = os.path.join(DASHBOARD_DIR, timestamped_file)
    
    with open(timestamped_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2)
    
    # Save as latest.json for dashboard
    latest_path = os.path.join(DASHBOARD_DIR, 'latest.json')
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print(f"📊 Dashboard JSON saved: {timestamped_path}")
    print(f"📊 Latest JSON updated: {latest_path}")
    
    return timestamped_path, latest_path

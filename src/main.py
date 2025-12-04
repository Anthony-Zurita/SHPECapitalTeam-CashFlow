"""
Main execution script for SHPE Capital Trading Algorithm
Orchestrates the entire analysis pipeline
"""

import sys

# Fix encoding issues on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        pass

from .data_loader import load_tickers
from .portfolio import analyze_stock, calculate_portfolio_summary
from .reporting import generate_report, save_report
from .reporting import generate_dashboard_json, save_dashboard_json


def main():
    """
    Main execution function that runs the complete analysis pipeline:
    1. Load ticker symbols
    2. Analyze each stock (signals + backtest)
    3. Calculate portfolio summary
    4. Generate reports (text + JSON)
    """
    print("=" * 80)
    print("🚀 SHPE CAPITAL - TEAM CASHFLOW")
    print("Stock Screening & Backtesting Algorithm")
    print("=" * 80)
    print("")
    
    # Load tickers
    tickers = load_tickers()
    if not tickers:
        print("❌ No tickers loaded. Exiting.")
        return
    
    print(f"\n📈 Starting analysis of {len(tickers)} stocks...")
    print("⏳ This may take a few minutes...\n")
    
    # Analyze all stocks
    signals = []
    backtest_results = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}")
        
        signal, backtest = analyze_stock(ticker)
        signals.append(signal)
        backtest_results.append(backtest)
    
    print("\n✅ Analysis complete!")
    
    # Calculate portfolio summary
    print("\n📊 Calculating portfolio summary...")
    portfolio_summary = calculate_portfolio_summary(backtest_results)
    
    # Generate text report
    print("\n📄 Generating reports...")
    report_text = generate_report(signals, backtest_results, portfolio_summary)
    print(report_text)
    save_report(report_text)
    
    # Generate dashboard JSON
    dashboard_data = generate_dashboard_json(signals, backtest_results, portfolio_summary)
    save_dashboard_json(dashboard_data)
    
    # Print summary
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Net Profit: ${portfolio_summary['net_profit']:,.2f}")
    print(f"Profit Factor: {portfolio_summary['profit_factor']:.2f}x")
    print(f"Win Rate: {portfolio_summary['overall_win_rate']:.1f}%")
    print(f"Total Trades: {portfolio_summary['total_trades']:,}")
    print("=" * 80)


if __name__ == "__main__":
    main()

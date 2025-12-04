SHPECapital - Team CashFlow Swing Trading Algorithm

SHPECapital Swing Trading Algorithm
A stock screening and backtesting tool built for educational purposes as part of the SHPECapital algorithmic trading program.
Algorithmic Trading Concepts Used
Market Data Feed
We use Yahoo Finance (via the yfinance Python library) to stream historical OHLCV data — Open, High, Low, Close, and Volume for each time period. This gives us the raw price information our algorithm needs to make decisions.
Trading Platform
Our Python script acts as a simulated trading platform. It processes market data, applies our strategy rules, and generates buy/sell signals. In a live environment, this would connect to a broker to execute real trades.
Connectivity
For swing trading (holding 2-10 days), millisecond latency isn't critical. We use Yahoo Finance's free API which has slight delays — acceptable since we're not doing high-frequency trading.
Backtesting
Before trusting any strategy with real money, we test it on 60 days of historical data. This shows how the strategy would have performed, helping us identify weaknesses before going live.
Risk Management
We implement safeguards to prevent catastrophic losses: stop-loss rules exit positions if they drop too far, and position sizing limits how much capital goes into any single trade.

Strategy Overview
Indicator Used

50-period Simple Moving Average (SMA) on 15-minute candles

Entry Rules (BUY)

Price crosses above the 50-period SMA
This signals potential upward momentum

Exit Rules (SELL)

Price crosses below the 50-period SMA
This signals the uptrend may be ending

Hold Conditions

If already in a position and price remains above SMA: hold
If not in a position and price is below SMA: wait (no entry)

Risk Rules

Stop-Loss: Exit if position loses more than 5% from entry price
Position Size: Maximum 10% of portfolio in any single stock
Daily Loss Limit: Stop trading if daily losses exceed 2% of portfolio


How to Run
Requirements
pip install yfinance pandas
Setup

Create a file called qqq_holdings.txt with stock tickers (one per line)
Run the screener:

bashpython merp.py
Output

Current BUY/SELL/HOLD signals for each stock
Backtest results showing historical performance
Reports saved to trade_reports/ folder


File Structure
├── merp.py              # Main algorithm and backtesting engine
├── qqq_holdings.txt     # Stock tickers to analyze
├── requirements.txt     # Python dependencies
├── trade_reports/       # Generated screening reports
└── README.md            # This file

Performance Metrics
Our backtest calculates:

Win Rate: Percentage of profitable trades
Average Profit/Loss: Mean return per trade
Total Trades: Number of entry/exit cycles
Average Winner vs Loser: Comparing good trades to bad ones


Team
SHPECapital Algorithmic Trading Team

Disclaimer
This is an educational project. Nothing here constitutes financial advice. Always do your own research before trading.

## Strategy Overview

**Indicators Used:**
- 20-period Simple Moving Average (SMA)

**Time Windows:**
- Daily (1d) intervals
- 5-year lookback for backtesting

**BUY Rules:**
- Price crosses above 20-day SMA
- Maximum 10% portfolio allocation per position
- Risk 2% per trade

**SELL Rules:**
- Price crosses below 20-day SMA, OR
- Stop-loss triggered (5% below entry price)

**HOLD Conditions:**
- Price above SMA but no fresh crossover
- Position already active

**Risk Management:**
- 5% stop-loss on all positions
- Maximum 10% portfolio per stock
- 2% risk per trade for position sizing

## Risk Management

**Stop-Loss (5%):**
- Prevents single trade from destroying portfolio
- Caps maximum loss per position
- Protects against trend reversals
- Reduces overfitting to historical winners

**Position Sizing:**
- Max 10% per stock prevents concentration risk
- 2% risk per trade ensures portfolio survives losing streaks
- Diversification across 10+ positions reduces single-stock risk

**Why This Matters:**
- Without stop-loss, worst trade was -15% in testing
- With stop-loss, worst trade is capped at -5%
- Prevents overfitting by not requiring perfect entry timing

Environment Set Up

Download Git

Install Here: https://git-scm.com/downloads

Download Python

Install Here: https://www.python.org/downloads/

Clone Repo

Cloning a Repo Instructions: https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository

Create a Virtual Environment (use trading_env for VM name as it is being ignored by .gitignore):

Run Command: python -m venv trading_env

Run Command: trading_env\Scripts\activate

these two commands create your virtual environment and activate it too

Install Requirements.txt

Run command: pip install -r requirements.txt

Run main.py by clicking in the top right-hand corner the run button

# SHPECapital - Team CashFlow Swing Trading Algorithm

A stock screening and backtesting tool that analyzes 100+ stocks from the QQQ ETF (Nasdaq 100) using a Simple Moving Average crossover strategy.

---

## Algorithmic Trading Concepts Used

### Market Data Feed
We use **Yahoo Finance** (via the `yfinance` Python library) as our market data feed, which provides historical OHLCV data (Open, High, Low, Close, Volume) for each trading day. For swing trading, we pulled **5 years of daily price data** (2020-2025) to ensure our backtests capture multiple market cycles including bull markets (2020-2021), corrections (2022), and recovery periods (2023-2024). Yahoo Finance is free and doesn't require authentication, making it ideal for our project. The 15-minute data delay is acceptable since we're analyzing daily candles for swing trades, not executing high-frequency strategies.

### Trading Platform
Our Python backtesting engine simulates a trading platform by processing historical data day-by-day and executing trades based on our SMA crossover rules. The engine tracks cash balances, open positions, entry prices, and calculates profit/loss for each completed trade. In a production environment, this logic would connect to a broker API (like Alpaca or Interactive Brokers) to execute real trades with real capital, but for the purpose of this project we simulate everything in Python to understand the mechanics without risking any real money.

### Connectivity & Latency
For swing trading strategies that hold positions for 2-10 days, millisecond-level latency is not critical. We use Yahoo Finance's free API which has slight delays in data delivery, but this doesn't impact our strategy since we make decisions based on daily closing prices. Unlike high-frequency trading where microseconds matter, swing trading gives us the luxury of using free, delayed data sources without sacrificing performance.

### Why Backtesting Matters
Backtesting is essential because it lets us test our strategy against **5 years of real market data** (7,272 simulated trades) before risking actual money. Our backtest revealed a critical insight: without a stop-loss, our worst single trade would have lost -15%, but with a 5% stop-loss implemented, losses are capped and the strategy becomes consistently profitable with a 1.15x profit factor across 100 stocks.

### Risk Controls Implementation
We implement multiple safeguards to prevent catastrophic losses and protect capital. **Stop-loss rules** (5% threshold) automatically exit positions that move against us, preventing any single trade from destroying the portfolio. **Position sizing limits** (max 10% per stock) ensure diversification across multiple positions, so no single stock failure can wipe out the account. **Risk-per-trade calculations** (2% portfolio risk) determine exact share quantities to buy, ensuring that even if the stop-loss triggers, we only lose 2% of total capital. These controls were discussed in Week 2 as essential components of professional algorithmic trading systems.

---

## Strategy Overview

### Indicator Used
- **20-period Simple Moving Average (SMA)** calculated on daily closing prices
- The SMA is a trend-following indicator that smooths out price noise by averaging the last 20 days of closing prices

### Time Windows
- **Daily (1d) candles**: Each data point represents one full trading day
- **5-year lookback period**: Historical data from 2020-2025 for comprehensive backtesting
- **20-day calculation window**: SMA uses the most recent 20 trading days

### Entry Rules (BUY)
- **Price crosses above 20-day SMA**: When yesterday's close was below the SMA and today's close is above, generate BUY signal
- This crossover signals potential trend reversal from downtrend to uptrend
- **Maximum 10% portfolio allocation per position**: No single stock can exceed 10% of total capital ($10,000 portfolio = max $1,000 per stock)
- **Risk 2% per trade**: Position size calculated so that if stop-loss triggers, maximum loss is 2% of portfolio ($200 on a $10,000 account)

### Exit Rules (SELL)
- **Price crosses below 20-day SMA**: When yesterday's close was above the SMA and today's close is below, generate SELL signal (trend reversal)
- **OR Stop-loss triggered**: Exit immediately if price drops 5% below entry price (risk management override)
- Stop-loss exits take priority over SMA signals to protect capital

### HOLD Conditions
- **Already in position + price above SMA**: Continue holding the position, no action taken
- **Not in position + price below SMA**: Wait for entry signal, stay in cash

### Risk Management Rules
- **5% stop-loss on all positions**: Automatically exit if trade drops 5% from entry price
- **Maximum 10% portfolio per stock**: Enforces diversification across 10+ positions minimum
- **2% risk per trade**: Position sizing ensures consistent risk across all trades regardless of stock price

---

## Risk Management: Why These Rules Matter

### Stop-Loss Protection (5%)
**What it does:**
- Caps maximum loss per trade at exactly -5.00% (verified in backtest results)
- Exits position automatically when price drops 5% below entry, regardless of SMA signal

**Why it matters:**
- **Prevents catastrophic losses**: Without stop-loss, our backtest showed worst single trade at -15.3%
- **With stop-loss enabled**: Worst trade is capped at -5.00% (1,120 stop-loss exits across 7,272 trades)
- **Protects profits**: If a winning trade reverses, stop-loss can be moved to breakeven or profit levels
- **Reduces emotional trading**: Pre-defined exit removes decision-making stress during drawdowns

### Position Sizing (10% max, 2% risk)
**What it does:**
- Limits any single stock to 10% of total portfolio value
- Calculates exact share quantity so stop-loss trigger = 2% portfolio loss

**Why it matters:**
- **Prevents concentration risk**: If one stock crashes, you lose max 10% of capital (one position), not 50% (if you were all-in)
- **Survives losing streaks**: With 2% risk per trade, you can survive 20+ consecutive losses before significant portfolio damage
- **Enables diversification**: $10,000 portfolio allows 10-20 simultaneous positions across tech sector
- **Professional risk management**: Mirrors institutional trading desks that never risk >2% per trade

### Backtesting Proof
Our 5-year backtest across 100 QQQ stocks demonstrates the effectiveness of these controls:

**Without stop-loss (hypothetical worst case):**
- Losing trades could run to -15% or worse
- Profit factor would be <1.0 (unprofitable)
- Single bad trade could wipe out weeks of gains

**With stop-loss enabled (actual results):**
- ✅ Worst single trade: -5.00% (exactly at stop-loss)
- ✅ Profit factor: 1.15x (profitable)
- ✅ Net profit: +$4,178.90 across all 100 stocks
- ✅ 60 profitable stocks vs. 40 unprofitable (60% success rate at portfolio level)

### Prevents Overfitting
These risk controls also reduce overfitting to historical data:
- Stop-loss doesn't rely on perfect SMA timing (which may not repeat in future)
- Fixed 5% threshold works across all stocks regardless of volatility patterns
- Position sizing adapts to stock price (expensive vs cheap stocks treated equally)
- Forces strategy to work with realistic risk constraints, not just theoretical perfect entries

---

## Performance Metrics

Our backtest engine calculates comprehensive performance statistics:

### Trade-Level Metrics
- **Win Rate**: Percentage of profitable trades (26.2% across all stocks)
- **Average Profit/Loss per Trade**: Mean return across all entries and exits
- **Average Winner vs Average Loser**: Comparison of winning trades vs losing trades (trend-following strategies have low win rates but large winners)
- **Gross Profit**: Sum of all winning trades in dollars
- **Gross Loss**: Sum of all losing trades in dollars
- **Profit Factor**: Gross profit ÷ Gross loss (>1.0 = profitable strategy)

### Portfolio-Level Metrics
- **Total Trades**: Number of complete entry/exit cycles across all 100 stocks (7,272 trades)
- **Net Profit/Loss**: Final dollar profit after all trades (currently +$4,178.90)
- **Profitable vs Unprofitable Stocks**: How many stocks made money vs lost money (60/40 split)
- **Best/Worst Performers**: Top and bottom stocks by total profit

### Risk Metrics
- **Stop-Loss Exit Rate**: Percentage of trades exited by stop-loss vs SMA signal (1,120 stop-loss exits / 7,272 total)
- **Maximum Loss Per Trade**: Worst single trade percentage (capped at -5.00% due to stop-loss)
- **Position Sizing Analysis**: Dollar allocation per trade based on 2% risk rule

---

## How to Run

### 1. Environment Setup

**Install Git:**
- Download from: https://git-scm.com/downloads

**Install Python 3.8+:**
- Download from: https://www.python.org/downloads/

**Clone the repository:**
```bash
git clone [your-repo-url]
cd shpecapital-trading
```

**Create virtual environment:**
```bash
# Create environment (using trading_env name to match .gitignore)
python -m venv trading_env

# Activate environment
trading_env\Scripts\activate          # Windows
source trading_env/bin/activate       # Mac/Linux
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

This installs:
- `yfinance` - Yahoo Finance data API
- `pandas` - Data manipulation and analysis
- `flask` - Web server for dashboard
- `flask-cors` - CORS handling for dashboard API

---

### 2. Run the Stock Screener

```bash
python merp.py
```

**What this does:**
1. Loads 100+ ticker symbols from `qqq_holdings.txt` (QQQ ETF constituents)
2. Downloads 5 years of daily OHLCV data from Yahoo Finance for each stock
3. Calculates 20-day Simple Moving Average for each stock
4. Generates current trading signals for today (STRONG BUY, BUY, SELL, HOLD)
5. Runs complete 5-year backtest simulating all trades with stop-loss
6. Calculates portfolio-level performance metrics

**Output files generated:**
- `screening_report_[timestamp].txt` - Human-readable text report with all signals and backtest results
- `dashboard_[timestamp].json` - Structured data file for dashboard visualization

**Expected runtime:** 2-5 minutes depending on internet speed (downloading 100 stocks × 5 years of data)

---

### 3. View Interactive Dashboard

```bash
python server.py
```

Then open your web browser to: **http://localhost:8000**

**Dashboard features:**
- 📊 **Portfolio Summary**: Total profit/loss, profit factor, win rate, number of trades
- 🎯 **Current Signals**: Today's STRONG BUY, BUY, SELL, and HOLD recommendations with position sizing
- 📈 **Top Performers**: Best and worst stocks by backtest performance
- 🔍 **Individual Stock Analysis**: Detailed trade-by-trade breakdown for each ticker
- ⚙️ **Configuration Display**: Shows exact parameters used (SMA period, stop-loss %, lookback period)

The dashboard reads from `dashboard_[timestamp].json` and presents all data in an easy-to-navigate web interface with filtering and sorting capabilities.

---

## File Structure

```
shpecapital-trading/
├── merp.py                          # Main algorithm and backtesting engine (893 lines)
├── server.py                        # Flask web server for dashboard (simple HTTP server)
├── dashboard.html                   # Interactive results dashboard (HTML/CSS/JavaScript)
├── qqq_holdings.txt                 # Stock tickers to analyze (QQQ ETF constituents, 100+ symbols)
├── requirements.txt                 # Python dependencies (yfinance, pandas, flask, flask-cors)
├── screening_report_[timestamp].txt # Generated text report with signals and backtest results
├── dashboard_[timestamp].json       # Generated JSON data for dashboard visualization
├── README.md                        # This documentation file
├── SHPE_final_rubric.pdf           # Project grading rubric
└── Week_2_SHPE_Capital.pdf         # Educational materials on algorithmic trading concepts
```

**Note:** Files with `[timestamp]` are auto-generated each time you run `merp.py`. The format is `YYYYMMDD_HHMM` (e.g., `20251203_1810` = December 3, 2025 at 6:10 PM).

---

## Code Architecture

### Main Components (`merp.py`)

**Configuration Section (Lines 76-93):**
- Defines all strategy parameters (SMA period, stop-loss %, portfolio size)
- Easy to modify for testing different configurations

**Data Loading (Lines 95-160):**
- `load_tickers()` - Reads stock symbols from text file
- `fetch_stock_data()` - Downloads historical data from Yahoo Finance

**Indicator Calculation (Lines 162-180):**
- `calculate_sma()` - Computes 20-day simple moving average

**Signal Generation (Lines 182-247):**
- `generate_current_signal()` - Analyzes latest data to produce STRONG BUY/BUY/SELL/HOLD
- `calculate_position_size()` - Determines exact share quantity based on 2% risk rule

**Backtesting Engine (Lines 249-421):**
- `backtest_strategy()` - Walks through historical data simulating trades
- Tracks open positions, entry/exit prices, profit/loss
- Implements stop-loss logic and SMA crossover detection
- Calculates win rate, average profit, gross profit/loss

**Portfolio Analysis (Lines 423-525):**
- `analyze_stock()` - Combines signal generation + backtesting for one stock
- `calculate_portfolio_summary()` - Aggregates results across all 100 stocks

**Reporting (Lines 527-893):**
- `generate_report()` - Creates human-readable text report
- `save_json_for_dashboard()` - Exports structured data for web dashboard
- `main()` - Orchestrates entire pipeline

---

## Understanding the Strategy

### Why 20-Day SMA?
The 20-day Simple Moving Average represents approximately one month of trading activity (20 business days ≈ 4 weeks). This timeframe is optimal for swing trading because:
- Short enough to respond to trend changes within days/weeks
- Long enough to filter out daily noise and false signals
- Aligns with our 2-10 day holding period target

### Why This Strategy Works (Sort Of)
**Current Performance:** 1.15x profit factor, +$4,178.90 net profit across 100 stocks

**Strengths:**
- Captures major trends when stocks transition from downtrend to uptrend
- Stop-loss protection prevents catastrophic losses
- Diversification across 100 stocks reduces single-stock risk
- Simple, objective rules remove emotional decision-making

**Weaknesses:**
- 26.2% win rate means 73.8% of trades lose money (trend-following trade-off)
- Choppy, sideways markets generate frequent false signals and stop-loss triggers
- Lagging indicator: SMA crossovers happen after trend already started (late entries)
- No volume confirmation or momentum filters to validate signals

### What We Learned
This project taught us fundamental algorithmic trading concepts:
1. **Backtesting is mandatory** - Never trade a strategy without historical testing
2. **Risk management > Strategy selection** - Stop-loss turns unprofitable strategy into profitable one
3. **Low win rates are OK** - Trend-following strategies naturally have low win rates but large winners compensate
4. **Diversification matters** - 60% of stocks were profitable individually, but portfolio overall is profitable due to diversification
5. **Simple != Bad** - A single-indicator strategy with proper risk controls outperforms complex strategies without risk controls

---

## Team

**SHPECapital - Team CashFlow**  

**Contributors:**
- Anthony Zurita
- Marcos Viloria
- Juan Cavallin
- Kyle
- Max Arthay

---

## Disclaimer

⚠️ **IMPORTANT: This is an educational project only.**

**Current backtest results (+$4,178.90 profit) are simulated.** Real trading involves slippage, commissions, market impact, and execution delays not modeled in this backtest.

---

## License

Educational use only. See disclaimer above.

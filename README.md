# algo-backtester

Event-driven backtesting engine for technical trading strategies, with a Django web interface.
Fetches historical OHLCV data, runs a strategy over it bar by bar, and reports performance after
realistic trading costs.

The engine is built around one idea: **a backtest that ignores costs is not a backtest.** Commission
and slippage are applied on every fill, and P&L is measured against the actual cash paid to enter a
position, not the quoted price.

## What it does

```
symbol + date range ──▶ fetch OHLCV ──▶ strategy generates signals ──▶ simulate fills
                                                                          │
                                        equity curve + trade log ◀────────┘
```

- **8 predefined strategies**: MA crossover, RSI, MACD, Bollinger Bands, Stochastic, ADX, Ichimoku,
  mean reversion
- **9 indicators implemented from scratch** (`backtester/indicators.py`): SMA, EMA, RSI, MACD,
  Bollinger Bands, Stochastic, ATR, ADX with Wilder's smoothing, Ichimoku Cloud
- **Cost-aware simulation**: configurable commission rate (default 0.1%), slippage (default 0.01%),
  position sizing (default 95% of available cash), and a starting capital
- **Metrics reported**: total return, Sharpe ratio, maximum drawdown, win rate, total trades,
  winning trades, plus a full per-trade log with entry price, exit price, size, commission and P&L
- **Data fetching** with retry and exponential backoff, column validation, and a minimum-history
  check before a run is allowed to start

## Stack

Python, Django, pandas, NumPy, matplotlib, yfinance. Frontend is server-rendered templates with
vanilla JS and CSS.

## Running it

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open `http://127.0.0.1:8000/`. Pick a symbol, date range and strategy, and the results view
returns the metrics, the equity curve and the trade log.

Headless use:

```python
from backtester.backtest_engine import BacktestEngine
from strategies.predefined_strategies import RSIStrategy

engine = BacktestEngine(RSIStrategy(), initial_capital=10000, commission_rate=0.001)
results = engine.run("AAPL", "2023-01-01", "2024-01-01")
print(results["total_return"], results["sharpe_ratio"], results["max_drawdown"])
```

`fetch_live_data.py` pulls recent intraday bars from Yahoo Finance for quick checks.

## Correctness work

`FIXES_SUMMARY.md` records defects found in the engine and how they were fixed. Two mattered:

- **P&L was inflated.** Entry cost was computed as `price * position`, excluding the commission paid
  to open. Every trade therefore looked more profitable than it was. Fixed to measure P&L against the
  actual total cost paid, commission included.
- **ADX was wrong.** The original implementation used neither Wilder's smoothing nor proper
  directional movement logic, so any ADX-gated strategy was trading on a meaningless number.

Both were caught by checking the arithmetic against hand-computed trades rather than by the results
looking wrong — a backtest that overstates returns rarely looks broken.

## Limitations

- Long-only. No shorting, no leverage, no margin.
- One position at a time, one symbol per run. No portfolio-level backtests.
- Fills assume the signal bar's price plus slippage; no order book, no partial fills, no gap handling.
- Sharpe is computed on the equity curve without a risk-free rate adjustment.

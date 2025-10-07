import yfinance as yf
import pandas as pd
from backtester.backtest_engine import BacktestEngine
from strategies.predefined_strategies import RSIStrategy

# Download historical data for AAPL
df = yf.download("AAPL", period="1mo", interval="1d")

# Fix multi-level columns if any
df.columns = ['_'.join(map(str, col)).strip() if isinstance(col, tuple) else col for col in df.columns]
print("Fixed DataFrame Columns:", df.columns)

# Rename columns to single level
df = df.rename(columns=lambda x: x.split("_")[0])
print("Renamed DataFrame Columns:", df.columns)

# Instantiate strategy (no data needed in constructor now)
strategy = RSIStrategy(period=14, overbought=70, oversold=30)

# Instantiate backtest engine with strategy
backtest = BacktestEngine(strategy)

# Define start and end dates for backtest
start_date = df.index.min().strftime('%Y-%m-%d')
end_date = df.index.max().strftime('%Y-%m-%d')

# Run backtest
results = backtest.run("AAPL", start_date, end_date)

# Print results summary
print("Backtest Results:")
print(f"Total Return: {results['total_return']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
print(f"Total Trades: {results['total_trades']}")
print(f"Winning Trades: {results['winning_trades']}")

import yfinance as yf
import pandas as pd

def fetch_live_data(ticker="AAPL", period="7d", interval="1h"):
    """Fetch live stock data from Yahoo Finance."""
    data = yf.download(ticker, period=period, interval=interval)
    data = data[['Close']]  # Keep only 'Close' prices
    data.reset_index(inplace=True)  # Reset index for compatibility
    return data

if __name__ == "__main__":
    stock_data = fetch_live_data()
    print(stock_data.tail())  # Print last few rows

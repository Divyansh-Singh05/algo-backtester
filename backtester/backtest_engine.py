import pandas as pd
import importlib
import os
from datetime import datetime
import numpy as np
import yfinance as yf
import time
import logging

class BacktestEngine:
    def __init__(self, strategy, initial_capital=10000, commission_rate=0.001, slippage=0.0001, position_size=0.95):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate  # 0.1% commission per trade
        self.slippage = slippage  # 0.01% slippage per trade
        self.position_size = position_size  # Use 95% of available capital by default

    def fetch_data(self, symbol, start_date, end_date, max_retries=5, backoff_factor=1):
        """Fetch historical data with proper error handling and validation"""
        if not symbol or not start_date or not end_date:
            raise ValueError("Symbol, start_date, and end_date must be provided")
            
        ticker = yf.Ticker(symbol)
        attempt = 0
        
        while attempt < max_retries:
            try:
                df = ticker.history(start=start_date, end=end_date)
                
                if df.empty:
                    logging.warning(f"No data returned for {symbol} on attempt {attempt + 1}")
                    attempt += 1
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** (attempt - 1))
                        time.sleep(wait_time)
                    continue
                    
                # Validate required columns
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    raise ValueError(f"Missing required columns: {missing_columns}")
                    
                # Check for sufficient data points
                if len(df) < 2:
                    raise ValueError(f"Insufficient data points: {len(df)}")
                    
                return df
                
            except Exception as e:
                attempt += 1
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** (attempt - 1))
                    logging.warning(f"Attempt {attempt} failed for {symbol} with error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to fetch data for {symbol} after {max_retries} attempts: {e}")
                    
        raise ValueError(f"Failed to fetch data for {symbol} after {max_retries} attempts")
        
    def run(self, symbol, start_date, end_date):
        """Run backtest for the given strategy"""
        # Validate inputs
        if not symbol or not start_date or not end_date:
            raise ValueError("Symbol, start_date, and end_date are required")
            
        # Fetch historical data
        data = self.fetch_data(symbol, start_date, end_date)
        if data.empty:
            raise ValueError(f"No data found for symbol {symbol}")
            
        # Generate trading signals
        data = self.strategy.generate_signals(data)
        
        # Validate that signals were generated
        if 'Signal' not in data.columns:
            raise ValueError("Strategy did not generate 'Signal' column")
        
        # Initialize portfolio metrics with proper dtypes
        data['Position'] = 0
        data['Position'] = data['Position'].astype(int)
        data['Cash'] = float(self.initial_capital)
        data['Holdings'] = 0.0
        data['Total'] = float(self.initial_capital)
        position = 0
        cash = self.initial_capital
        
        # Simulate trading
        trades = []
        completed_trades = []  # Track completed trade pairs
        last_buy_price = None
        last_buy_size = None
        last_entry_cost = None  # Track actual entry cost including commission
        
        # Simulate trading
        for index, row in data.iterrows():
            # Skip rows with NaN signals
            if pd.isna(row['Signal']):
                continue
                
            # Handle buy signal
            if row['Signal'] == 1 and position == 0:
                # Calculate position size using available cash
                available_cash = cash * self.position_size
                execution_price = row['Close'] * (1 + self.slippage)  # Account for slippage
                max_shares = available_cash / execution_price
                position = int(max_shares)  # Round down to nearest whole share
                
                if position > 0:
                    # Calculate actual cost including commission
                    cost = position * execution_price
                    commission = cost * self.commission_rate
                    total_cost = cost + commission
                    
                    if total_cost <= cash:  # Verify we have enough cash
                        cash -= total_cost
                        last_buy_price = execution_price
                        last_buy_size = position
                        last_entry_cost = total_cost  # Store actual total cost paid
                        
                        trades.append({
                            'date': index.strftime('%Y-%m-%d'),
                            'type': 'BUY',
                            'price': execution_price,
                            'size': position,
                            'commission': commission,
                            'total_cost': total_cost,
                            'pnl': None
                        })
            
            # Handle sell signal
            elif row['Signal'] == -1 and position > 0:
                execution_price = row['Close'] * (1 - self.slippage)  # Account for slippage
                gross_value = position * execution_price
                commission = gross_value * self.commission_rate
                net_value = gross_value - commission
                
                # Calculate P&L using actual entry cost (including entry commission)
                pnl = net_value - last_entry_cost
                pnl_pct = (pnl / last_entry_cost) * 100  # Percentage return
                
                trades.append({
                    'date': index.strftime('%Y-%m-%d'),
                    'type': 'SELL',
                    'price': execution_price,
                    'size': position,
                    'commission': commission,
                    'total_value': net_value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
                
                # Record completed trade
                if last_buy_price is not None and last_entry_cost is not None:
                    completed_trades.append({
                        'entry_price': last_buy_price,
                        'exit_price': execution_price,
                        'size': last_buy_size,
                        'entry_cost': last_entry_cost,
                        'exit_value': net_value,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
                cash += net_value
                position = 0
                last_buy_price = None
                last_buy_size = None
                last_entry_cost = None
            
            # Update portfolio values using execution prices for consistency
            current_price = row['Close']
            if position > 0:
                # For holdings valuation, use current market price
                holdings_value = position * current_price
            else:
                holdings_value = 0
                
            data.at[index, 'Position'] = int(position)
            data.at[index, 'Cash'] = float(cash)
            data.at[index, 'Holdings'] = float(holdings_value)
            data.at[index, 'Total'] = float(cash + holdings_value)
        
        # Calculate performance metrics
        initial_value = self.initial_capital
        final_value = data['Total'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value
        
        # Calculate win rate based on completed trades
        winning_trades = sum(1 for trade in completed_trades if trade['pnl'] > 0)
        total_trades = len(completed_trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Format equity curve data
        equity_curve = [
            {'date': date.strftime('%Y-%m-%d'), 'value': value} 
            for date, value in zip(data.index, data['Total'])
        ]
        
        # Prepare results
        results = {
            'trades': trades,
            'equity_curve': equity_curve,
            'total_return': float(total_return),
            'win_rate': float(win_rate),
            'max_drawdown': self._calculate_max_drawdown(data['Total']),
            'sharpe_ratio': self._calculate_sharpe_ratio(data['Total']),
            'total_trades': total_trades,
            'winning_trades': winning_trades
        }
        
        return results
    
    def _calculate_max_drawdown(self, equity_curve):
        """Calculate maximum drawdown as a percentage
        
        Maximum drawdown is the largest peak-to-trough decline in the portfolio value,
        expressed as a percentage of the peak value.
        """
        # Calculate running maximum (peak)
        running_max = equity_curve.expanding(min_periods=1).max()
        
        # Calculate drawdown in percentage terms
        drawdown = ((equity_curve - running_max) / running_max)
        
        # Get the maximum drawdown
        max_drawdown = drawdown.min()
        
        return float(max_drawdown)
    
    def _calculate_sharpe_ratio(self, equity_curve, risk_free_rate=0.01):
        """Calculate Sharpe ratio using correct formula
        
        Sharpe Ratio = (Mean Excess Return) / (Standard Deviation of Excess Returns)
        """
        returns = equity_curve.pct_change().dropna()
        if len(returns) <= 1:
            return 0.0
            
        # Calculate daily risk-free rate
        daily_rf_rate = risk_free_rate / 252
        excess_returns = returns - daily_rf_rate
        
        # Calculate Sharpe ratio with correct standard deviation
        if excess_returns.std() == 0:
            return 0.0
            
        sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
        return float(sharpe_ratio)
    
    def run_backtest(self, strategy_name, parameters, start_date, end_date, symbol='AAPL'):
        """
        Run a backtest with the specified strategy and parameters
        """
        # Load data
        data = self._load_data(start_date, end_date, symbol)
        
        # Import and instantiate the strategy
        strategy_module = importlib.import_module(f"strategies.{strategy_name}")
        
        # Get the strategy class based on the file name
        if strategy_name == 'rsi_strategy':
            strategy_class = getattr(strategy_module, 'RSIStrategy')
        elif strategy_name == 'customStrategy':
            strategy_class = getattr(strategy_module, 'CustomStrategy')
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
        strategy = strategy_class(data, **parameters)
        
        # Run the backtest
        self.data = data
        self.strategy = strategy
        final_value, trade_log = self.run()
        
        # Calculate metrics
        total_return = (final_value - self.initial_capital) / self.initial_capital
        sharpe_ratio = self._calculate_sharpe_ratio()
        max_drawdown = self._calculate_max_drawdown()
        win_rate = self._calculate_win_rate(trade_log)
        
        # Format results
        results = {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'equity_curve': self._generate_equity_curve(),
            'trades': self._format_trades(trade_log)
        }
        
        return results
    
    def _load_data(self, start_date, end_date, symbol='AAPL'):
        """
        Load data for the specified stock and date range using yfinance
        """
        try:
            # Download data from Yahoo Finance
            stock = yf.Ticker(symbol)
            data = stock.history(start=start_date, end=end_date)
            
            # Ensure the data has the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                raise ValueError(f"Missing required columns in data. Required: {required_columns}")
            
            # If data is empty, fall back to random data
            if len(data) == 0:
                logging.warning(f"No data available for {symbol}, using random data instead")
                return self._generate_random_data(start_date, end_date)
                
            return data
            
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {str(e)}")
            logging.info("Falling back to random data")
            return self._generate_random_data(start_date, end_date)
    
    def _generate_random_data(self, start_date, end_date):
        """
        Generate random price data for testing
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        date_range = pd.date_range(start=start, end=end, freq='D')
        
        # Create random price data
        np.random.seed(42)  # For reproducibility
        prices = np.random.normal(100, 10, len(date_range))
        prices = np.cumsum(np.random.normal(0, 1, len(date_range))) + 100
        
        data = pd.DataFrame({
            'Open': prices,
            'High': prices * (1 + np.random.uniform(0, 0.02, len(date_range))),
            'Low': prices * (1 - np.random.uniform(0, 0.02, len(date_range))),
            'Close': prices * (1 + np.random.normal(0, 0.01, len(date_range))),
            'Volume': np.random.randint(1000, 10000, len(date_range))
        }, index=date_range)
        
        return data
    
    def _calculate_win_rate(self, trade_log):
        """
        Calculate the win rate
        """
        if not trade_log:
            return 0.0
        
        winning_trades = sum(1 for trade in trade_log if trade['type'] == 'SELL' and trade['pnl'] > 0)
        total_trades = sum(1 for trade in trade_log if trade['type'] == 'SELL')
        
        return winning_trades / total_trades if total_trades > 0 else 0.0
    
    def _generate_equity_curve(self):
        """
        Generate the equity curve
        """
        equity_curve = []
        current_value = self.initial_capital
        
        for date, row in self.data.iterrows():
            # Simple equity curve calculation
            if len(equity_curve) > 0:
                prev_close = self.data['Close'].shift(1).loc[date]
                current_close = row['Close']
                change = (current_close - prev_close) / prev_close
                current_value *= (1 + change)
            
            equity_curve.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': current_value
            })
        
        return equity_curve
    
    def _format_trades(self, trade_log):
        """
        Format the trade log for the API response
        """
        formatted_trades = []
        
        for trade in trade_log:
            # If date is already a datetime object, use it directly
            if isinstance(trade['date'], (pd.Timestamp, datetime)):
                date_str = trade['date'].strftime('%Y-%m-%d')
            else:
                # If it's an index, get the date from the DataFrame's index
                date_str = self.data.index[trade['date']].strftime('%Y-%m-%d')
                
            formatted_trades.append({
                'date': date_str,
                'type': trade['type'],
                'price': trade['price'],
                'size': trade['size'],
                'commission': trade['commission'],
                'total_value': trade['total_value'],
                'pnl': trade['pnl'],
                'pnl_pct': trade['pnl_pct']
            })
        
        return formatted_trades

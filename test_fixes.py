#!/usr/bin/env python3
"""
Test script to verify backtesting fixes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtester.backtest_engine import BacktestEngine
from strategies.predefined_strategies import MACrossoverStrategy, RSIStrategy, MACDStrategy
from backtester.indicators import calculate_rsi, calculate_sma, calculate_adx

def test_indicators():
    """Test indicator calculations"""
    print("Testing indicators...")
    
    # Generate sample data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.normal(0, 1, len(dates)))
    
    data = pd.DataFrame({
        'Open': prices,
        'High': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
        'Low': prices * (1 - np.random.uniform(0, 0.02, len(dates))),
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Test RSI
    try:
        rsi = calculate_rsi(data, 14)
        assert not rsi.isna().all(), "RSI should not be all NaN"
        assert rsi.max() <= 100 and rsi.min() >= 0, "RSI should be between 0-100"
        print("✓ RSI calculation working")
    except Exception as e:
        print(f"✗ RSI test failed: {e}")
    
    # Test SMA
    try:
        sma = calculate_sma(data, 20)
        assert not sma.isna().all(), "SMA should not be all NaN"
        print("✓ SMA calculation working")
    except Exception as e:
        print(f"✗ SMA test failed: {e}")
    
    # Test ADX
    try:
        adx_data = calculate_adx(data, 14)
        assert 'ADX' in adx_data.columns, "ADX should have ADX column"
        assert '+DI' in adx_data.columns, "ADX should have +DI column" 
        assert '-DI' in adx_data.columns, "ADX should have -DI column"
        print("✓ ADX calculation working")
    except Exception as e:
        print(f"✗ ADX test failed: {e}")

def test_strategies():
    """Test strategy signal generation"""
    print("\nTesting strategies...")
    
    # Generate sample data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.normal(0, 1, len(dates)))
    
    data = pd.DataFrame({
        'Open': prices,
        'High': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
        'Low': prices * (1 - np.random.uniform(0, 0.02, len(dates))),
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Test MA Crossover Strategy
    try:
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
        result = strategy.generate_signals(data.copy())
        assert 'Signal' in result.columns, "Strategy should generate Signal column"
        signal_counts = result['Signal'].value_counts()
        print(f"✓ MA Crossover: {signal_counts.to_dict()}")
    except Exception as e:
        print(f"✗ MA Crossover test failed: {e}")
    
    # Test RSI Strategy  
    try:
        strategy = RSIStrategy(period=14, overbought=70, oversold=30)
        result = strategy.generate_signals(data.copy())
        assert 'Signal' in result.columns, "Strategy should generate Signal column"
        signal_counts = result['Signal'].value_counts()
        print(f"✓ RSI Strategy: {signal_counts.to_dict()}")
    except Exception as e:
        print(f"✗ RSI Strategy test failed: {e}")
    
    # Test MACD Strategy
    try:
        strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        result = strategy.generate_signals(data.copy())
        assert 'Signal' in result.columns, "Strategy should generate Signal column"
        signal_counts = result['Signal'].value_counts()
        print(f"✓ MACD Strategy: {signal_counts.to_dict()}")
    except Exception as e:
        print(f"✗ MACD Strategy test failed: {e}")

def test_backtest_engine():
    """Test backtesting engine"""
    print("\nTesting backtest engine...")
    
    try:
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
        engine = BacktestEngine(strategy, initial_capital=10000)
        
        # Test with a simple symbol and date range
        start_date = '2023-01-01'
        end_date = '2023-12-31'
        
        # This will use random data if live data fails
        results = engine.run('AAPL', start_date, end_date)
        
        # Check results structure
        required_keys = ['trades', 'equity_curve', 'total_return', 'win_rate', 
                        'max_drawdown', 'sharpe_ratio', 'total_trades', 'winning_trades']
        
        for key in required_keys:
            assert key in results, f"Results should contain '{key}'"
        
        print(f"✓ Backtest completed successfully")
        print(f"  - Total Return: {results['total_return']:.2%}")
        print(f"  - Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"  - Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"  - Win Rate: {results['win_rate']:.2%}")
        print(f"  - Total Trades: {results['total_trades']}")
        
    except Exception as e:
        print(f"✗ Backtest engine test failed: {e}")
        import traceback
        traceback.print_exc()

def test_input_validation():
    """Test input validation"""
    print("\nTesting input validation...")
    
    # Test invalid strategy parameters
    try:
        MACrossoverStrategy(fast_period=-1, slow_period=30)
        print("✗ Should have failed for negative period")
    except ValueError:
        print("✓ MA Crossover correctly validates negative periods")
    
    try:
        MACrossoverStrategy(fast_period=30, slow_period=10)
        print("✗ Should have failed for fast >= slow")
    except ValueError:
        print("✓ MA Crossover correctly validates fast >= slow period")
    
    try:
        RSIStrategy(period=14, overbought=30, oversold=70)
        print("✗ Should have failed for overbought < oversold")
    except ValueError:
        print("✓ RSI Strategy correctly validates overbought < oversold")

if __name__ == "__main__":
    print("Running backtesting fixes verification...")
    print("=" * 50)
    
    test_indicators()
    test_strategies() 
    test_backtest_engine()
    test_input_validation()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
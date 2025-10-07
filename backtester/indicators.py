import pandas as pd
import numpy as np

def calculate_sma(data, period):
    """Calculate Simple Moving Average with validation"""
    if period <= 0:
        raise ValueError("Period must be positive")
    if len(data) < period:
        return pd.Series([np.nan] * len(data), index=data.index)
    return data['Close'].rolling(window=period).mean()

def calculate_ema(data, period):
    """Calculate Exponential Moving Average with validation"""
    if period <= 0:
        raise ValueError("Period must be positive")
    if len(data) < 2:
        return pd.Series([np.nan] * len(data), index=data.index)
    return data['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    """Calculate RSI with proper boundary handling and validation"""
    if period <= 0:
        raise ValueError("Period must be positive")
    if len(data) < period + 1:
        return pd.Series([np.nan] * len(data), index=data.index)
        
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Handle division by zero
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    
    # Fill NaN values with neutral RSI (50)
    rsi = rsi.fillna(50)
    
    return rsi

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    fast_ema = calculate_ema(data, fast_period)
    slow_ema = calculate_ema(data, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return pd.DataFrame({
        'MACD': macd_line,
        'Signal': signal_line,
        'Histogram': macd_histogram
    })

def calculate_bollinger_bands(data, period=20, std_dev=2):
    sma = calculate_sma(data, period)
    std = data['Close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return pd.DataFrame({
        'Middle': sma,
        'Upper': upper_band,
        'Lower': lower_band
    })

def calculate_stochastic(data, k_period=14, d_period=3):
    low_min = data['Low'].rolling(window=k_period).min()
    high_max = data['High'].rolling(window=k_period).max()
    k_line = 100 * (data['Close'] - low_min) / (high_max - low_min)
    d_line = k_line.rolling(window=d_period).mean()
    return pd.DataFrame({
        'K': k_line,
        'D': d_line
    })

def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = abs(data['High'] - data['Close'].shift())
    low_close = abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()

def calculate_adx(data, period=14):
    """Calculate ADX (Average Directional Index) using proper Wilder's smoothing
    
    ADX measures trend strength, not direction.
    +DI and -DI measure directional movement.
    """
    if len(data) < period + 1:
        # Return empty DataFrame with proper structure if insufficient data
        return pd.DataFrame({
            'ADX': pd.Series([np.nan] * len(data), index=data.index),
            '+DI': pd.Series([np.nan] * len(data), index=data.index),
            '-DI': pd.Series([np.nan] * len(data), index=data.index)
        })
    
    # Calculate True Range components
    high_low = data['High'] - data['Low']
    high_close_prev = abs(data['High'] - data['Close'].shift(1))
    low_close_prev = abs(data['Low'] - data['Close'].shift(1))
    
    # True Range is the maximum of the three
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    
    # Calculate Directional Movement
    high_diff = data['High'].diff()
    low_diff = data['Low'].diff()
    
    plus_dm = pd.Series(np.where(
        (high_diff > low_diff) & (high_diff > 0), high_diff, 0
    ), index=data.index)
    
    minus_dm = pd.Series(np.where(
        (low_diff > high_diff) & (low_diff > 0), low_diff, 0
    ), index=data.index)
    
    # Apply Wilder's smoothing (exponential moving average with alpha = 1/period)
    def wilders_smoothing(series, period):
        alpha = 1.0 / period
        return series.ewm(alpha=alpha, adjust=False).mean()
    
    # Smooth TR, +DM, and -DM using Wilder's method
    atr = wilders_smoothing(tr, period)
    plus_dm_smooth = wilders_smoothing(plus_dm, period)
    minus_dm_smooth = wilders_smoothing(minus_dm, period)
    
    # Calculate Directional Indicators
    plus_di = 100 * (plus_dm_smooth / atr)
    minus_di = 100 * (minus_dm_smooth / atr)
    
    # Calculate DX (Directional Index)
    di_sum = plus_di + minus_di
    di_diff = abs(plus_di - minus_di)
    
    # Avoid division by zero
    dx = pd.Series(np.where(
        di_sum != 0, 100 * (di_diff / di_sum), 0
    ), index=data.index)
    
    # Calculate ADX using Wilder's smoothing of DX
    adx = wilders_smoothing(dx, period)
    
    return pd.DataFrame({
        'ADX': adx,
        '+DI': plus_di,
        '-DI': minus_di
    })

def calculate_ichimoku(data, conversion_period=9, base_period=26, span_period=52):
    high_values = data['High']
    low_values = data['Low']
    
    conversion_line = (high_values.rolling(window=conversion_period).max() + 
                      low_values.rolling(window=conversion_period).min()) / 2
    
    base_line = (high_values.rolling(window=base_period).max() + 
                 low_values.rolling(window=base_period).min()) / 2
    
    leading_span_a = ((conversion_line + base_line) / 2).shift(base_period)
    
    leading_span_b = ((high_values.rolling(window=span_period).max() + 
                      low_values.rolling(window=span_period).min()) / 2).shift(base_period)
    
    lagging_span = data['Close'].shift(-base_period)
    
    return pd.DataFrame({
        'Conversion': conversion_line,
        'Base': base_line,
        'SpanA': leading_span_a,
        'SpanB': leading_span_b,
        'Lagging': lagging_span
    }) 
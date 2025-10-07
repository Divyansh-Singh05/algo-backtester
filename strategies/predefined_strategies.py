from backtester.indicators import *

class MACrossoverStrategy:
    def __init__(self, fast_period=10, slow_period=30):
        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("Periods must be positive integers")
        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period")
            
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    def generate_signals(self, data):
        if len(data) < max(self.fast_period, self.slow_period):
            # Not enough data for indicators
            data['Signal'] = 0
            return data
            
        data['FastMA'] = calculate_sma(data, self.fast_period)
        data['SlowMA'] = calculate_sma(data, self.slow_period)
        
        # Detect crossovers: buy when fast MA crosses above slow MA
        data['Signal'] = 0
        
        # Calculate previous values for crossover detection
        fast_prev = data['FastMA'].shift(1)
        slow_prev = data['SlowMA'].shift(1)
        
        # Buy signal: Fast MA crosses above Slow MA
        bullish_cross = (
            (data['FastMA'] > data['SlowMA']) & 
            (fast_prev <= slow_prev)
        )
        
        # Sell signal: Fast MA crosses below Slow MA  
        bearish_cross = (
            (data['FastMA'] < data['SlowMA']) & 
            (fast_prev >= slow_prev)
        )
        
        data.loc[bullish_cross, 'Signal'] = 1
        data.loc[bearish_cross, 'Signal'] = -1
        
        return data

class RSIStrategy:
    def __init__(self, period=14, overbought=70, oversold=30):
        if period <= 0:
            raise ValueError("Period must be positive")
        if not (0 < oversold < overbought < 100):
            raise ValueError("Must have 0 < oversold < overbought < 100")
            
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self, data):
        if len(data) < self.period + 1:
            data['Signal'] = 0
            return data
            
        data['RSI'] = calculate_rsi(data, self.period)
        
        # Initialize signals
        data['Signal'] = 0
        
        # Generate signals with proper condition checks
        oversold_condition = (data['RSI'] < self.oversold) & (~pd.isna(data['RSI']))
        overbought_condition = (data['RSI'] > self.overbought) & (~pd.isna(data['RSI']))
        
        data.loc[oversold_condition, 'Signal'] = 1   # Buy signal
        data.loc[overbought_condition, 'Signal'] = -1  # Sell signal
        
        return data

class MACDStrategy:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
            raise ValueError("All periods must be positive integers")
        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period")
            
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
    def generate_signals(self, data):
        min_required = max(self.slow_period, self.signal_period) + 10  # Buffer for EMA
        if len(data) < min_required:
            data['Signal'] = 0
            return data
            
        macd_data = calculate_macd(data, self.fast_period, self.slow_period, self.signal_period)
        data['MACD'] = macd_data['MACD']
        data['Signal_Line'] = macd_data['Signal']
        
        # Detect MACD crossovers
        data['Signal'] = 0
        
        # Get previous values for crossover detection
        macd_prev = data['MACD'].shift(1)
        signal_prev = data['Signal_Line'].shift(1)
        
        # Buy signal: MACD crosses above Signal line
        bullish_cross = (
            (data['MACD'] > data['Signal_Line']) & 
            (macd_prev <= signal_prev)
        )
        
        # Sell signal: MACD crosses below Signal line
        bearish_cross = (
            (data['MACD'] < data['Signal_Line']) & 
            (macd_prev >= signal_prev)
        )
        
        data.loc[bullish_cross, 'Signal'] = 1
        data.loc[bearish_cross, 'Signal'] = -1
        
        return data

class BollingerBandsStrategy:
    def __init__(self, period=20, std_dev=2):
        self.period = period
        self.std_dev = std_dev
        
    def generate_signals(self, data):
        bb = calculate_bollinger_bands(data, self.period, self.std_dev)
        data['BB_Middle'] = bb['Middle']
        data['BB_Upper'] = bb['Upper']
        data['BB_Lower'] = bb['Lower']
        
        # Buy when price crosses below lower band, sell when crosses above upper band
        data['Signal'] = 0
        data.loc[data['Close'] < data['BB_Lower'], 'Signal'] = 1
        data.loc[data['Close'] > data['BB_Upper'], 'Signal'] = -1
        
        return data

class StochasticStrategy:
    def __init__(self, k_period=14, d_period=3, overbought=80, oversold=20):
        self.k_period = k_period
        self.d_period = d_period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self, data):
        stoch = calculate_stochastic(data, self.k_period, self.d_period)
        data['K'] = stoch['K']
        data['D'] = stoch['D']
        
        # Buy when both K and D are below oversold and K crosses above D
        # Sell when both K and D are above overbought and K crosses below D
        data['Signal'] = 0
        data.loc[(data['K'] < self.oversold) & (data['D'] < self.oversold) & 
                (data['K'] > data['D']), 'Signal'] = 1
        data.loc[(data['K'] > self.overbought) & (data['D'] > self.overbought) & 
                (data['K'] < data['D']), 'Signal'] = -1
        
        return data

class ADXStrategy:
    def __init__(self, period=14, adx_threshold=25):
        self.period = period
        self.adx_threshold = adx_threshold
        
    def generate_signals(self, data):
        adx_data = calculate_adx(data, self.period)
        data['ADX'] = adx_data['ADX']
        data['+DI'] = adx_data['+DI']
        data['-DI'] = adx_data['-DI']
        
        # Buy when ADX > threshold and +DI crosses above -DI
        # Sell when ADX > threshold and +DI crosses below -DI
        data['Signal'] = 0
        data.loc[(data['ADX'] > self.adx_threshold) & 
                (data['+DI'] > data['-DI']), 'Signal'] = 1
        data.loc[(data['ADX'] > self.adx_threshold) & 
                (data['+DI'] < data['-DI']), 'Signal'] = -1
        
        return data

class IchimokuStrategy:
    def __init__(self, conversion_period=9, base_period=26, span_period=52):
        self.conversion_period = conversion_period
        self.base_period = base_period
        self.span_period = span_period
        
    def generate_signals(self, data):
        ichimoku = calculate_ichimoku(data, self.conversion_period, 
                                    self.base_period, self.span_period)
        
        data['Conversion'] = ichimoku['Conversion']
        data['Base'] = ichimoku['Base']
        data['SpanA'] = ichimoku['SpanA']
        data['SpanB'] = ichimoku['SpanB']
        
        # Buy when Conversion Line crosses above Base Line and price is above Span A
        # Sell when Conversion Line crosses below Base Line and price is below Span A
        data['Signal'] = 0
        data.loc[(data['Conversion'] > data['Base']) & 
                (data['Close'] > data['SpanA']), 'Signal'] = 1
        data.loc[(data['Conversion'] < data['Base']) & 
                (data['Close'] < data['SpanA']), 'Signal'] = -1
        
        return data

class MeanReversionStrategy:
    def __init__(self, period=20, std_dev=2):
        self.period = period
        self.std_dev = std_dev
        
    def generate_signals(self, data):
        data['SMA'] = calculate_sma(data, self.period)
        data['STD'] = data['Close'].rolling(window=self.period).std()
        data['Upper'] = data['SMA'] + (data['STD'] * self.std_dev)
        data['Lower'] = data['SMA'] - (data['STD'] * self.std_dev)
        
        # Buy when price is below lower band, sell when above upper band
        data['Signal'] = 0
        data.loc[data['Close'] < data['Lower'], 'Signal'] = 1
        data.loc[data['Close'] > data['Upper'], 'Signal'] = -1
        
        return data 
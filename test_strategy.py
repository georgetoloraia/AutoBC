import pandas as pd
import numpy as np
from trading.strategy import simplified_evaluate_trading_signals

# Mock settings
TIMEFRAMES = ['3m', '5m', '15m', '30m']
INDICATOR_WEIGHTS = {
    'close < lower_band': 0.2,
    'rsi < 30': 0.2,
    'macd > macd_signal': 0.2,
    'adx > 30 and plus_DI > minus_DI': 0.2,  # Renamed DI columns
    'close > vwap': 0.1,
    'mfi < 20': 0.1,
}
TIMEFRAME_WEIGHTS = {'3m': 0.5, '5m': 0.6, '15m': 0.7, '30m': 0.9}
BUY_CONFIDENCE_THRESHOLD = 0.5
SELL_CONFIDENCE_THRESHOLD = 0.5

# Mock OHLCV Data
def generate_mock_data(rows=100):
    """Generate mock OHLCV data with indicators."""
    timestamps = pd.date_range("2025-01-01", periods=rows, freq="min")
    data = {
        'timestamp': timestamps,
        'open': np.random.uniform(100, 200, rows),
        'high': np.random.uniform(200, 250, rows),
        'low': np.random.uniform(80, 100, rows),
        'close': np.random.uniform(100, 200, rows),
        'volume': np.random.uniform(1000, 5000, rows),
        'lower_band': np.random.uniform(90, 100, rows),
        'upper_band': np.random.uniform(200, 210, rows),
        'rsi': np.random.uniform(20, 70, rows),
        'macd': np.random.uniform(-5, 5, rows),
        'macd_signal': np.random.uniform(-5, 5, rows),
        'adx': np.random.uniform(20, 40, rows),
        'plus_DI': np.random.uniform(10, 20, rows),  # Renamed DI columns
        'minus_DI': np.random.uniform(10, 20, rows),  # Renamed DI columns
        'vwap': np.random.uniform(100, 150, rows),
        'mfi': np.random.uniform(10, 80, rows),
    }
    return pd.DataFrame(data).set_index('timestamp')

# Generate mock data for all timeframes
mock_data = {tf: generate_mock_data() for tf in TIMEFRAMES}

# Test strategy.py
if __name__ == "__main__":
    signal = simplified_evaluate_trading_signals(mock_data)
    print(f"Final Signal: {signal}")

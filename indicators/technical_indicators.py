import talib
import pandas as pd

def calculate_indicators(df):
    # Trend Indicators
    df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)

    # Momentum Indicators
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    df['mfi'] = talib.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=14)

    # Volatility Indicators
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)

    # Volume Indicators
    df['obv'] = talib.OBV(df['close'], df['volume'])
    df['ad_line'] = talib.AD(df['high'], df['low'], df['close'], df['volume'])

    # Price Transform Functions
    df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
    df['typprice'] = talib.TYPPRICE(df['high'], df['low'], df['close'])

    #-
    df['+DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
    df['-DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)

    return df

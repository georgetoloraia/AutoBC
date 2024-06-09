import talib

def calculate_indicators(df):
    # df['ema'] = talib.EMA(df['close'], timeperiod=14)
    # df['wma'] = talib.WMA(df['close'], timeperiod=14)
    # df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
    # df['trix'] = talib.TRIX(df['close'], timeperiod=15)
    df['rsi'] = talib.RSI(df['close'], timeperiod=1)
    # df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    # df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    # df['slowk'], df['slowd'] = talib.STOCH(df['high'], df['low'], df['close'], fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    # df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=14)
    # df['obv'] = talib.OBV(df['close'], df['volume'])
    # df['%K'], df['%D'] = talib.STOCH(df['high'], df['low'], df['close'])
    # df['adx'] = talib.ADX(df['high'], df['low'], df['close'])
    # df['+DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'])
    # df['-DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'])
    # df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

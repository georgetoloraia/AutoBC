import talib

def calculate_indicators(df):

    df = df.copy()
    
    df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
    df['adx'] = talib.ADX(df['high'], df['low'], df['close'])
    df['+DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'])
    df['-DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'])
    df['rsi'] = talib.RSI(df['close'])
    df['mfi'] = talib.MFI(df['high'], df['low'], df['close'], df['volume'])
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'])
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'])
    df['obv'] = talib.OBV(df['close'], df['volume'])
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    df['typical_price'] = talib.TYPPRICE(df['high'], df['low'], df['close'])

     # Add shifted conditions at the dataframe level
    df['atr_shift'] = df['atr'].shift(1)
    df['obv_shift'] = df['obv'].shift(1)

    # Add 200-period moving average
    df['ma_200'] = df['close'].rolling(window=200).mean()

    return df

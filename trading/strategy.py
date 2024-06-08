import logging
from indicators.technical_indicators import calculate_indicators

logger = logging.getLogger(__name__)

def simplified_evaluate_trading_signals(data):
    signals = {}
    for timeframe, df in data.items():
        if df.empty:
            logger.info(f"DataFrame is empty for {timeframe} timeframe.")
            continue

        latest = df.iloc[-1]
        df = calculate_indicators(df)

        # Simplified Buy conditions
        buy_conditions = [
            latest['close'] > latest['ema'],  # Price above EMA
            latest['trix'] > 0,  # TRIX positive
            latest['rsi'] < 40,  # RSI below 40 (less strict oversold condition)
            latest['macd'] > latest['macd_signal']  # MACD above signal line
        ]

        # Simplified Sell conditions
        sell_conditions = [
            latest['close'] < latest['ema'],  # Price below EMA
            latest['trix'] < 0,  # TRIX negative
            latest['rsi'] > 60,  # RSI above 60 (less strict overbought condition)
            latest['macd'] < latest['macd_signal']  # MACD below signal line
        ]

        if all(buy_conditions):
            logger.info(f"Simplified Buy signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'buy'
        elif all(sell_conditions):
            logger.info(f"Simplified Sell signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'sell'
    return signals

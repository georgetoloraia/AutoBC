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

        # Buy conditions
        buy_conditions = [
            # latest['close'] < latest['lower_band'],  # Price below lower Bollinger Band
            # latest['%K'] < 25 and latest['%K'] > latest['%D'],  # Stochastic %K < 20 and %K > %D
            # latest['+DI'] > latest['-DI'] and latest['adx'] > 20,  # ADX conditions
            # latest['close'] > latest['vwap'],  # Price above VWAP
            latest['rsi'] < 35,  # RSI below 30
            latest['macd'] > latest['macd_signal'],  # MACD bullish crossover
            # latest['obv'] > df['obv'].iloc[-2]  # Increasing OBV
        ]

        # Sell conditions
        sell_conditions = [
            # latest['close'] > latest['upper_band'],  # Price above upper Bollinger Band
            # latest['%K'] > 80 and latest['%K'] < latest['%D'],  # Stochastic %K > 80 and %K < %D
            # latest['-DI'] > latest['+DI'] and latest['adx'] > 20,  # ADX conditions
            # latest['close'] < latest['vwap'],  # Price below VWAP
            latest['rsi'] > 70,  # RSI above 70
            latest['macd'] < latest['macd_signal'],  # MACD bearish crossover
            # latest['obv'] < df['obv'].iloc[-2]  # Decreasing OBV
        ]

        if all(buy_conditions):
            logger.info(f"Simplified Buy signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'buy'
        elif all(sell_conditions):
            logger.info(f"Simplified Sell signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'sell'
    return signals

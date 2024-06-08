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
            latest['close'] < latest['lower_band'],  # Price below lower Bollinger Band
            latest['%K'] < 20 and latest['%K'] > latest['%D'],  # Stochastic %K < 20 and %K > %D
            latest['+DI'] > latest['-DI'] and latest['adx'] > 20,  # ADX conditions
            latest['close'] > latest['vwap']  # Price above VWAP
        ]

        # Sell conditions
        sell_conditions = [
            latest['close'] > latest['upper_band'],  # Price above upper Bollinger Band
            latest['%K'] > 80 and latest['%K'] < latest['%D'],  # Stochastic %K > 80 and %K < %D
            latest['-DI'] > latest['+DI'] and latest['adx'] > 20,  # ADX conditions
            latest['close'] < latest['vwap']  # Price below VWAP
        ]

        if all(buy_conditions):
            logger.info(f"Simplified Buy signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'buy'
        elif all(sell_conditions):
            logger.info(f"Simplified Sell signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'sell'
    return signals

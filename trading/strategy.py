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
            latest['rsi'] < 30,  # RSI below 35
            latest['macd'] > latest['macd_signal'],  # MACD bullish crossover
            latest['adx'] > 25 and latest['+DI'] > latest['-DI'],  # ADX indicating strong trend
            latest['close'] > latest['vwap'],  # Price above VWAP
            latest['mfi'] < 20  # Money Flow Index indicating oversold
        ]

        # Sell conditions
        sell_conditions = [
            latest['close'] > latest['upper_band'],  # Price above upper Bollinger Band
            latest['rsi'] > 70,  # RSI above 70
            latest['macd'] < latest['macd_signal'],  # MACD bearish crossover
            latest['adx'] > 25 and latest['-DI'] > latest['+DI'],  # ADX indicating strong trend
            latest['close'] < latest['vwap'],  # Price below VWAP
            latest['mfi'] > 80  # Money Flow Index indicating overbought
        ]

        # Calculate confidence scores
        buy_confidence = sum([1 if cond else 0 for cond in buy_conditions]) / len(buy_conditions)
        sell_confidence = sum([1 if cond else 0 for cond in sell_conditions]) / len(sell_conditions)

        logger.info(f"Buy confidence for {timeframe} timeframe: {buy_confidence}")
        logger.info(f"Sell confidence for {timeframe} timeframe: {sell_confidence}")

        if buy_confidence > 0.55:
            logger.info(f"Simplified Buy signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'buy'
        elif sell_confidence > 0.75:
            logger.info(f"Simplified Sell signal conditions met in {timeframe} timeframe.")
            signals[timeframe] = 'sell'
        # else:
        #     signals[timeframe] = 'hold'

    return signals
